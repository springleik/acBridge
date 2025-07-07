#!/usr/bin/env python3
import numpy, json

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

# read in JSON files
aTree = []
cTree = []
with open ('a.json', 'r') as aFile:
    aTree = json.load(aFile)
with open ('c.json', 'r') as cFile:
    cTree = json.load(cFile)

# look for measured values
for aMeas, cMeas in zip (aTree, cTree):
    # skip over comments and other non-measurements
    if not isinstance (aMeas, dict): continue
    if not isinstance (cMeas, dict): continue
    if "skip" in aMeas: continue
    if "skip" in cMeas: continue
    if 'calMatrixMeas' in cMeas:
        # read in the cal output matrix
        calMeas = cMeas ['calMatrixMeas']
        # expand complex values
        calMatrix = numpy.array ([
            [complex (*calMeas[0][0]), complex (*calMeas[0][1])],
            [complex (*calMeas[1][0]), complex (*calMeas[1][1])]
            ])
        # compute the inverse and add to tree
        calOut = numpy.linalg.inv (calMatrix)
        aMeas ['calMatrixOut'] = calOut.tolist ()

# save file with both direct and inverse matrices
# print (json.dumps(theTree, indent = 2, default = customJson))
with open ('a.json', 'w') as aFile:
    json.dump (aTree, aFile, indent = 2, default = customJson)

print ('Done!')
