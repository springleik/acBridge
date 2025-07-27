#!/usr/bin/env python3

'''
Python script to calibrate the output side of a digital
bridge using a gated toneburst technique. Assumes stimulus
and response setup files already exist, modifies the stimulus
setup with a calibration matrix for each measurement.
M. Williamsen, 4 July 2025
'''

import sys, json, numpy
import CompTree as ct

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

# check for command line args
if len (sys.argv) != 3:
    print ('usage: python3 {} stimFileNoExt respFileNoExt'.format (sys.argv[0]))
    quit ()
stimFileName = sys.argv[1]  # stimulus setup file
respFileName = sys.argv[2]  # response setup file

# load setup files
stimTree = []
respTree = []
try:
    with open (stimFileName + '.json', 'r') as setupFile:
        stimTree = json.load (setupFile)
        print ("Loading stimulus setup file '{}.json'".format (stimFileName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load stimulus setup file '{}.json'".format (stimFileName))
    print (e)
    quit ()

try:
    with open (respFileName + '.json', 'r') as setupFile:
        respTree = json.load (setupFile)
        print ("Loading response setup file '{}.json'".format (respFileName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load response setup file '{}.json'".format (respFileName))
    print (e)
    quit ()

# gather a list of frequencies from the stimulus tree
freqList = list (ct.locateKey ('requestFreq', stimTree))
freqList = list (dict.fromkeys (freqList))
calList = []
print ('Frequency list: ', freqList)

# TODO Count and show how many entries are in the input file
# for each frequency and left/right because it will throw
# the correction off if counts don't match.

# iterate over request frequencies
for aFreq in freqList:
    # gather left output measurements from response tree
    fragMent = {'requestFreq': aFreq, 'output': 'left'}
    matchList = []
    ct.locateTree (fragMent, respTree, matchList)
    # iterate over left output measurements
    firstLeft = 0+0j
    secondLeft = 0+0j
    for i in range (len (matchList)):
        firstLeft += complex (*matchList [i]['bursts'][0]['chans'][0]['rect'])
        secondLeft += complex (*matchList [i]['bursts'][1]['chans'][0]['rect'])

    # gather right output measurements from response tree
    fragMent = {'requestFreq': aFreq, 'output': 'right'}
    matchList = []
    ct.locateTree (fragMent, respTree, matchList)
    # iterate over right output measurements
    firstRight = 0+0j
    secondRight = 0+0j
    for i in range (len (matchList)):
        firstRight += complex (*matchList [i]['bursts'][0]['chans'][0]['rect'])
        secondRight += complex (*matchList [i]['bursts'][1]['chans'][0]['rect'])

    # show averages, normalized and inverted, as JSON text
    result = numpy.array ([[firstLeft,secondLeft],[firstRight,secondRight]])
    result /= result [0][0]
    result = numpy.linalg.inv (result)
    newDict = {'requestFreq': aFreq, 'calMatrix': result.tolist ()}
    print (json.dumps (newDict, indent = 2, default = customJson))
