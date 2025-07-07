#!/usr/bin/env python3
import numpy, json

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

# read in existing JSON files
# TODO allow user arguments to name files
# TODO names are hard-coded for now
aTree = []
cTree = []
with open ('a.json', 'r') as aFile:
    aTree = json.load(aFile)
with open ('c.json', 'r') as cFile:
    cTree = json.load(cFile)

# look for measured values
reqMeas = None
sumM = []
sumN = 0
for aMeas, cMeas in zip (aTree, cTree):
    # skip over comments and other non-measurements
    if not isinstance (aMeas, dict): continue
    if not isinstance (cMeas, dict): continue
    if "skip" in aMeas: continue
    if "skip" in cMeas: continue

    # look for new frequency in input file
    if "requestFreq" in aMeas:
        if reqMeas:
            # compute the inverse of the average, add to tree
            calOut = numpy.linalg.inv (sumM/sumN)
            reqMeas ['calMatrixOut'] = calOut.tolist ()

        # open new frequency
        reqMeas = aMeas
        sumM = numpy.array ([[0+0j,0+0j],[0+0j,0+0j]])
        sumN = 0

    # look for calibration matrices in output file
    if 'calMatrixMeas' in cMeas:
        # read in the cal output matrix
        calMeas = cMeas ['calMatrixMeas']
        # expand complex values
        calMatrix = numpy.array ([
            [complex (*calMeas[0][0]), complex (*calMeas[0][1])],
            [complex (*calMeas[1][0]), complex (*calMeas[1][1])]
            ])
        sumM += calMatrix
        sumN += 1

# close open average
if reqMeas:
    # compute the inverse of the average, add to tree
    calOut = numpy.linalg.inv (sumM/sumN)
    reqMeas ['calMatrixOut'] = calOut.tolist ()

# save file with both direct and inverse matrices
# print (json.dumps(theTree, indent = 2, default = customJson))
with open ('a.json', 'w') as aFile:
    json.dump (aTree, aFile, indent = 2, default = customJson)

print ('Done!')
