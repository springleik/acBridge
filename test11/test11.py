import numpy, json

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

# read in file a.json
theTree = []
with open ('a.json', 'r') as aFile:
    theTree = json.load(aFile)

# look for calibration output matrix
for theMeas in theTree:
    # skip over comments and other non-measurements
    if not isinstance (theMeas, dict): continue
    if 'calMatrixOut' in theMeas:
        # read in the cal output matrix
        calOut = theMeas ['calMatrixOut']
        # expand complex values
        calMatrix = numpy.array ([
            [complex (*calOut[0][0]), complex (*calOut[0][1])],
            [complex (*calOut[1][0]), complex (*calOut[1][1])]
            ])
        # compute the inverse and add to tree
        calIn = numpy.linalg.inv (calMatrix)
        theMeas ['calMatrixIn'] = calIn.tolist ()

# save file with both direct and inverse matrices
# print (json.dumps(theTree, indent = 2, default = customJson))
with open ('a.json', 'w') as aFile:
    json.dump (theTree, aFile, indent = 2, default = customJson)

print ('Done!')
