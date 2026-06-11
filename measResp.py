#!/usr/bin/env python3

'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Analyzes a response wave
file on local mass storage. Assumes the response wave file has
been created by another program with a matching stimulus file.
M. Williamsen, 4 July 2025
'''

import wave, math, struct, json, sys, cmath, itertools

# check for command line args
if len (sys.argv) < 3:
    print ('usage: python3 {} inFileNameNoExt outFileNameNoExt [mode]'.format (sys.argv[0]))
    quit ()
inFileName = sys.argv[1]    # setup for creating stimulus file
outFileName = sys.argv[2]   # setup for analyzing response file

# optional third argument sets response mode, default is mode 4
mode = 4
if len (sys.argv) > 3:
    mode = int(sys.argv[3])

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
4 seconds, just over a megabyte on disk.
'''

# read response file
print ("Reading wave file '{}.wav'".format (inFileName))
with wave.open(inFileName + '.wav', 'rb') as waveFile:
    print ('Wave file parameters:')
    theParams = waveFile.getparams ()
    print (json.dumps (theParams._asdict (), indent = 2))
    actualFrames = getattr (theParams, 'nframes')
    sampRate = getattr (theParams, 'framerate')

    # add up burst lengths in units of frames
    expectFrames = 0
    for theMeas in theTree:
        # skip over comments, waits, and other non-measurements
        if not isinstance (theMeas, dict): continue
        if "skip" in theMeas: continue
        if "wait" in theMeas:
            expectFrames += 5 * sampRate
            continue
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
        if "skip" in theMeas: continue
        if "wait" in theMeas:
            endDatum += 8 * sampRate
            continue

        # gather details for the measurement
        delay = theMeas ['startDelay']
        cellSamp = theMeas ['cellSamples']
        countWave = theMeas ['countWaves']
        burstSamp = cellSamp * 4
        incr = math.tau * countWave / 4.0 / cellSamp
        burstFrameCount = delay + (2 * burstSamp)
        theMeas.update ({'bursts':[]})
        cursor = theMeas ['bursts']
        output = theMeas ['output']
        freq = theMeas ['actualFreq']
        refVec = [math.cos ((n + 0.5) * incr) for n in range (burstSamp)]
        # print ("freq: {}, len(refVec): {}".format (freq, len(refVec)))

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

        # complex valued measurements
        a = theMeas ['bursts'][0]['chans'][0]['rect']
        b = theMeas ['bursts'][1]['chans'][0]['rect']
        c = theMeas ['bursts'][0]['chans'][1]['rect']
        d = theMeas ['bursts'][1]['chans'][1]['rect']

        # gather direct values for wireless verification
        if 1 == mode:
            print (freq, abs(a), cmath.phase(a),
            abs(b), cmath.phase(b),
            abs(c), cmath.phase(c),
            abs(d), cmath.phase(d),)

        # gather ratios with respect to 'a' for calibration
        elif 2 == mode:
            ratio = 0+0j
            if output == 'left': ratio = b/a
            elif output == 'right': ratio = a/b
            print (freq, ratio.real, ratio.imag)

        # gather absolute values for calibration
        elif 3 == mode:
            e = f = 0+0j
            if output == 'left': e, f = a, b
            elif output == 'right': e, f = b, a
            print (freq, abs(e), cmath.phase(e), abs(f), cmath.phase(f))

        # simple ratio measurement, assumes like impedances
        elif 4 == mode:
            ratio = b / a
            print (freq, a.real, a.imag, b.real, b.imag,
                ratio.real, ratio.imag)

        # gather impedance ratio and time constant for measurement
        # assumes resistor on left output and capacitor on right
        elif 5 == mode:
            ratio = b / a
            omega = complex (0, 2 * math.pi * freq)
            tau = ratio / omega
            print (freq, a.real, a.imag, b.real, b.imag,
                ratio.real, ratio.imag, tau.real, tau.imag)

        # gather complex values for analysis in Excel
        elif 6 == mode:
            print (freq, a.real, b.real, c.real, d.real,
                a.imag, b.imag, c.imag, d.imag)

        # unknown mode encountered
        else:
            print ('Unknown mode encountered: {}.'.format (mode))

# show decorated tree on the console
# print (json.dumps(theTree, indent = 2, default = customJson))

# write decorated tree out to disk, overwrite previous
print ("Writing setup file '{}.json'".format (outFileName))
with open(outFileName + '.json', 'w') as jsonFile:
        json.dump(theTree, jsonFile, indent = 2, default = customJson)
        jsonFile.write('\n')
