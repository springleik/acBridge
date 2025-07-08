#!/usr/bin/env python3
'''
Python script to calibrate the input side of a digital
bridge using a gated toneburst technique. Assumes stimulus
and response setup files already exist, modifies the stimulus
setup with a calibration matrix for each measurement.
M. Williamsen, 8 July 2025
'''

import sys, json, numpy

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

# look for measured values
reqMeas = None
sumM = []
sumN = 0

# top level nodes in stimulus and response trees will match
for rMeas, sMeas in zip (respTree, stimTree):
    # skip over comments and other non-measurements
    if not isinstance (rMeas, dict): continue
    if "skip" in rMeas: continue

    # look for new frequency in stimulus file
    if "requestFreq" in sMeas:
        if reqMeas:
            # compute the inverse of the average
            # calIn = numpy.linalg.inv (sumM/sumN)
            # normalize to first coefficient
            # calIn /= calIn [0][0]
            # add to stimulus measurement tree
            calIn = sumM / sumN
            reqMeas ['calMatrixIn'] = calIn.tolist ()

        # open new frequency
        reqMeas = sMeas
        sumM = numpy.array ([[0+0j,0+0j],[0+0j,0+0j]])
        sumN = 0

    # look for calibration matrices in output file
    if 'calMatrixMeas' in rMeas:
        calMeas = rMeas ['calMatrixMeas']
        input = rMeas ['input']
        calMatrix = numpy.array ([[0+0j,0+0j],[0+0j,0+0j]])
        # expand complex values
        if input == 'left':
            calMatrix = numpy.array ([
                [complex (*calMeas[0][0]), complex (1, 0)],
                [complex (*calMeas[1][0]), complex (1, 0)]
                ])
        elif input == 'right':
            calMatrix = numpy.array ([
                [complex (1, 0), complex (*calMeas[0][0])],
                [complex (1, 0), complex (*calMeas[1][0])]
                ])
        sumM += calMatrix
        sumN += 1
    else:
        print ('Calibration matrix missing from response file!')
        quit ()

if reqMeas:
    # compute the inverse of the average
    # calIn = numpy.linalg.inv (sumM/sumN)
    # normalize to first coefficient
    # calIn /= calIn [0][0]
    # add to stimulus measurement tree
    calIn = sumM / sumN
    reqMeas ['calMatrixIn'] = calIn.tolist ()
else:
    print ('Nothing to save, done.')
    quit ()

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

# save file with inverse matrices, overwrites without asking
# print (json.dumps(theTree, indent = 2, default = customJson))
with open (stimFileName + '.json', 'w') as sFile:
    json.dump (stimTree, sFile, indent = 2, default = customJson)

print ('File saved, done.')
