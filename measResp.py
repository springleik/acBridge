#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Analyzes a response wave
file on local mass storage. Assumes the response wave file has
been created by another program with a matching stimulus file.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys, cmath, itertools

# check for command line args
if len (sys.argv) != 3:
    print ('usage: python3 {} inFileNameNoExt outFileNameNoExt'.format (sys.argv[0]))
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

# special handling to serialize complex numbers
def customJson (obj):
    if isinstance (obj, complex):
        return [obj.real, obj.imag]
    else:
        return obj

'''
Bursts are approximately 1/2 second times two, so the stimulus
file contains silence followed by up to one second of left
channel excitation, more silence, then one second of right
channel excitation. The total measurement length will be about
4 seconds, somewhat less than 3/4 megabyte on disk.
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
        # skip over comments and other non-measurements
        if not isinstance (theMeas, dict): continue
        expectFrames += 2 * ((theMeas ['cellSamples'] * 8) + theMeas ['startDelay'])
    print ('Expected {} frames, found {}'.format (expectFrames, actualFrames))
    if actualFrames < expectFrames:
        print ('Done, not enough frames in response file!')
        quit ()
    # print (json.dumps(theTree, indent = 2))

    # iterate over measurements
    endDatum = 0
    for i, theMeas in enumerate (theTree):
        # skip over comments and other non-measurements
        if not isinstance (theMeas, dict): continue

        # gather details for the measurement
        delay = theMeas ['startDelay']
        imbal = complex (theMeas['imbalanceIn'][0],
            theMeas['imbalanceIn'][1])
        cellSamp = theMeas ['cellSamples']
        countWave = theMeas ['countWaves']
        burstSamp = cellSamp * 4
        incr = math.tau * countWave / 4.0 / cellSamp
        burstFrameCount = delay + (2 * burstSamp)
        theMeas.update ({'bursts':[]})
        cursor = theMeas ['bursts']
        refVec = [math.cos ((n + 0.5) * incr) for n in range (burstSamp)]

        # iterate over tonebursts
        for j in range(2):
            endDatum += burstFrameCount

            # set file pointer
            waveFile.setpos (endDatum - burstSamp - cellSamp)

            # read the frames in a burst
            burstBytes = waveFile.readframes (burstSamp + cellSamp)

            # unpack frames into channels
            chanL = []
            chanR = []
            theChannels = [chanL, chanR]
            for bytesL, bytesR in itertools.batched (struct.iter_unpack ('<BBB', burstBytes), 2):
                intL = int.from_bytes (bytesL, byteorder = 'little', signed = True)
                intR = int.from_bytes (bytesR, byteorder = 'little', signed = True)
                chanL.append (intL)
                chanR.append (intR)
            cursor.append ({'burst':j, 'chans': []})
            cursor1 = cursor [j]['chans']

            # iterate over input channels
            for k, responseVec in enumerate (theChannels):
                cName = 'left' if not k else 'right'
                cursor1.append ({'chan':cName})

                # measure in-phase and quadrature components with matched filter
                realDotPrdt = math.sumprod (responseVec[:burstSamp], refVec)
                imagDotPrdt = math.sumprod (responseVec[cellSamp:cellSamp+burstSamp], refVec)
                cplx = complex (-realDotPrdt, imagDotPrdt) * 2 / burstSamp

                # decorate the tree with results
                cursor1 [k].update ({'rect': cplx})
                cursor1 [k].update ({'polar': cmath.polar (cplx)})

        # TODO analyze measurement results to obtain RC time constant

        # fundamental
        a = theMeas ['bursts'][0]['chans'][0]['rect']
        b = theMeas ['bursts'][1]['chans'][0]['rect']
        c = theMeas ['bursts'][0]['chans'][1]['rect'] * imbal
        d = theMeas ['bursts'][1]['chans'][1]['rect'] * imbal

        # for basic calibration of inputs and outputs
        # average multiple trials in Excel to get correction factors
        if (False):
            first  = a/c
            second = b/d
            third  = a/d
            print (
                theMeas ['actualFreq'],
                first.real, first.imag,
                second.real, second.imag,
                third.real, third.imag
            )

        # measurement of detector input impedance
        # left-only first burst, right-only second burst
        if (False):
            freq = theMeas ['actualFreq']
            omega = complex (0, 2 * math.pi * freq)
            ratio = d/a
            tau = (ratio - 1)/omega
            print (
                freq, omega,
                ratio.real, ratio.imag,
                tau.real, tau.imag
            )

        # simple impedance ratio measurement with
        # left-only first burst, right-only second burst
        if (True):
            ratio = b/a
            print (
                theMeas ['actualFreq'],
                ratio.real, ratio.imag
            )

        # alternate impedance ratio measurement with
        # left and right positive equal in first burst,
        # left negative and right positive in second burst
        if (False):
            ratio = (a+b)/(a-b)
            print (
                theMeas ['actualFreq'],
                ratio.real, ratio.imag
            )

# show decorated tree on the console
# print (json.dumps(theTree, indent = 2, default = customJson))

# write decorated tree out to disk, overwrite previous
print ("Writing setup file '{}.json'".format (outFileName))
with open(outFileName + '.json', 'w') as jsonFile:
        json.dump(theTree, jsonFile, indent = 2, default = customJson)
        jsonFile.write('\n')
