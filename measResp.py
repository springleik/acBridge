#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Analyzes a response wave
file on local mass storage. Assumes the response wave file has
been created by another program with a matching stimulus file.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys, cmath

# check for command line args
if len (sys.argv) != 3:
    print ('Useage: python3 {} inFileNameNoExt outFileNameNoExt'.format (sys.argv[0]))
    quit ()
inFileName = sys.argv[1]    # setup for creating stimulus file
outFileName = sys.argv[2]   # setup for analyzing response file

# load setup file
theTree = []
try:
    with open (inFileName + '.json', 'r') as setupFile:
        theTree = json.load (setupFile)
        print ("Loading setup file '{}.json'".format (inFileName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.json'".format (inFileName))
    print (e)
    quit ()

'''
Bursts are approximately 1/2 second in length, doubled up
so the stimulus file contains silence followed by up to one
second of left channel excitation, more silence, then one second
of right channel excitation. The total measurement length will
be about 4 seconds, somewhat less than 3/4 megabyte on disk.
'''

# read response file
print ("Reading wave file '{}.wav'".format (inFileName))
with wave.open(inFileName + '.wav', 'rb') as waveFile:
    print ('Wave file parameters:')
    theParams = waveFile.getparams ()
    print (json.dumps (theParams._asdict (), indent = 2))
    actualFrames = getattr (theParams, 'nframes')

    # add up burst lengths in units of frames
    expectFrames = 0
    for theMeas in theTree:
        expectFrames += 2 * ((theMeas ['cellSamples'] * 8) + theMeas ['startDelay'])
    print ('Expected {} frames, found {}'.format (expectFrames, actualFrames))
    if actualFrames < expectFrames:
        print ('Done, not enough frames in response file!')
        quit ()
    print (theTree)

    # perform dot product over two vectors
    def innerProduct (vec1, vec2) -> float:
        return sum ([x * y for (x,y) in zip (vec1, vec2)])

    # iterate over measurements
    datum = 0
    for theMeas in theTree:
        # gather details for each measurement
        delay = theMeas ['startDelay']
        imbal = theMeas ['imbalanceIn']
        cellSamp = theMeas ['cellSamples']
        countWave = theMeas ['countWaves']
        burstSamp = cellSamp * 4
        incr = 2.0 * math.pi * countWave / 4.0 / cellSamp

        # compute reference vectors for fundamental and second harmonic
        # NOTE harmonic in right channel won't see exponential decay in left channel
        fundCos = [math.cos ((n + 0.5) * incr) for n in range (burstSamp)]
        harmCos = [math.cos (2 * (n + 0.5) * incr) / -2 for n in range (burstSamp)]
        harmSin = [math.sin (2 * (n + 0.5) * incr) / -2 for n in range (burstSamp)]

        # analyze first response burst
        datum += (delay + burstSamp)
        waveFile.setpos (datum - cellSamp)
        sinBytes = waveFile.readframes (burstSamp)
        sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
        imagPartL = innerProduct (fundCos, sinVecL)
        imagPartR = innerProduct (fundCos, sinVecR)

        waveFile.setpos (datum)
        cosBytes = waveFile.readframes (burstSamp)
        cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
        realPartL = innerProduct (fundCos, cosVecL)
        realPartR = innerProduct (fundCos, cosVecR)
        realHarmR = innerProduct (harmCos, cosVecR)
        imagHarmR = innerProduct (harmSin, cosVecR)

        # normalize
        imagPartL *= -2 / burstSamp / imbal
        realPartL *=  2 / burstSamp / imbal
        firstL = complex (realPartL, imagPartL)

        imagPartR *= -2 / burstSamp
        realPartR *=  2 / burstSamp
        firstR = complex (realPartR, imagPartR)

        imagHarmR *= -2 / burstSamp
        realHarmR *=  2 / burstSamp
        firstHarmR = complex (realHarmR, imagHarmR)

        # decorate measurement tree
        toUpdate = {'firstBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
        theMeas.update (toUpdate)

        # analyze second response burst
        datum += (delay + 2 * burstSamp)
        waveFile.setpos (datum - cellSamp)
        sinBytes = waveFile.readframes (burstSamp)
        sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
        imagPartL = innerProduct (fundCos, sinVecL)
        imagPartR = innerProduct (fundCos, sinVecR)

        waveFile.setpos (datum)
        cosBytes = waveFile.readframes (burstSamp)
        cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
        realPartL = innerProduct (fundCos, cosVecL)
        realPartR = innerProduct (fundCos, cosVecR)
        realHarmR = innerProduct (harmCos, cosVecR)
        imagHarmR = innerProduct (harmSin, cosVecR)

        # normalize
        imagPartL *= -2 / burstSamp / imbal
        realPartL *=  2 / burstSamp / imbal
        secondL = complex (realPartL, imagPartL)

        imagPartR *= -2 / burstSamp
        realPartR *=  2 / burstSamp
        secondR = complex (realPartR, imagPartR)

        imagHarmR *= -2 / burstSamp
        realHarmR *=  2 / burstSamp
        secondHarmR = complex (realHarmR, imagHarmR)

        # decorate measurement tree
        toUpdate = {'secondBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
        theMeas.update (toUpdate)

        # do some calculations
        correction = secondHarmR/firstHarmR
        print ('secondHarmR/firstHarmR: {}'.format (correction))
        print ('secondL/firstL: {}, secondR/firstR: {}'.format (secondL/firstL, secondR/firstR))
        print ('corrected secondL/firstL: {},'.format (secondL/firstL/correction))
        print ()

        # move to end of second burst
        datum += burstSamp

# create setup file, overwrite previous
print ("Writing setup file '{}.json'".format (outFileName))
with open(outFileName + '.json', 'w') as jsonFile:
        json.dump(theTree, jsonFile, indent = 2)
        jsonFile.write('\n')
