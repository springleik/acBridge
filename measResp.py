#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Analyzes a response wave
file on local mass storage. Assumes the response wave file has
been created by another program with a matching stimulus file.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys, cmath
print ('Usage: python3 measResp.py fileNameNoExtension')

# initialize setup
def initializeDetails (aMeas):
    aMeas.setdefault ('sampleRate', 44100)      # samples per second
    aMeas.setdefault ('cellSamples', 5402)      # samples per cell
    aMeas.setdefault ('countWaves', 49)         # cycles per four cells
    aMeas.setdefault ('imbalanceIn', 0.99712)   # output channel balance L/R
    aMeas.setdefault ('startDelay', 4410)       # samples before first burst

theTree = {}
initializeDetails (theTree)

# check for command line arg
fName = 'acBridge'
if 1 < len(sys.argv): fName = sys.argv[1]

# load setup file
try:
    with open (fName + '.json', 'r') as setupFile:
        theTree = json.load (setupFile)
        print ("Loading setup file '{}.json'".format (fName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.json'".format (fName))
    print (e)

'''
Bursts are approximately 1/2 second in length, doubled up
so the stimulus file contains about one second of left channel
excitation, one second of silence, and one second of right
channel excitation. The total measurement length will be about
three seconds, slightly more than 1/2 megabyte on disk.
'''

# read response file
print ("Reading wave file '{}.wav'".format (fName))
waveFile = wave.open(fName + '.wav', 'rb')
print ('Wave file parameters:')
theParams = waveFile.getparams ()
print (json.dumps (theParams._asdict (), indent = 2))
actualFrames = getattr (theParams, 'nframes')

# add up burst lengths in units of frames
expectFrames = 0
for theMeas in theTree:
    initializeDetails (theMeas)
    expectFrames += (theMeas ['cellSamples'] * 3 * 8) + theMeas ['startDelay']
print ('Expected {} frames, found {}'.format (expectFrames, actualFrames))
if actualFrames < expectFrames:
    print ('Done, not enough frames in response file!')
    quit ()

print (theTree)

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

    # compute a reference vector
    refVec = [math.sin ((n + 0.5) * incr) for n in range (burstSamp)]

    # analyze first response burst
    datum += delay + burstSamp
    waveFile.setpos (datum - cellSamp)
    sinBytes = waveFile.readframes (burstSamp)
    sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
    imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
    imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

    waveFile.setpos (datum)
    cosBytes = waveFile.readframes (burstSamp)
    cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
    realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
    realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

    # normalize
    imagPartL *= -2 / burstSamp / imbal
    realPartL *=  2 / burstSamp / imbal
    firstL = complex (realPartL, imagPartL)

    imagPartR *= -2 / burstSamp
    realPartR *=  2 / burstSamp
    firstR = complex (realPartR, imagPartR)

    toUpdate = {'firstBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
    theMeas.update (toUpdate)

    # analyze silent gap
    datum += 2 * burstSamp
    waveFile.setpos (datum - cellSamp)
    sinBytes = waveFile.readframes (burstSamp)
    sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
    imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
    imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

    waveFile.setpos (datum)
    cosBytes = waveFile.readframes (burstSamp)
    cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
    realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
    realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

    # normalize
    imagPartL *= -2 / burstSamp / imbal
    realPartL *=  2 / burstSamp / imbal
    silentL = complex (realPartL, imagPartL)

    imagPartR *= -2 / burstSamp
    realPartR *=  2 / burstSamp
    silentR = complex (realPartR, imagPartR)

    toUpdate = {'silentBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
    theMeas.update (toUpdate)

    # analyze second response burst
    datum += 2 * burstSamp
    waveFile.setpos (datum - cellSamp)
    sinBytes = waveFile.readframes (burstSamp)
    sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
    imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
    imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

    waveFile.setpos (datum)
    cosBytes = waveFile.readframes (burstSamp)
    cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
    realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
    realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

    # normalize
    imagPartL *= -2 / burstSamp / imbal
    realPartL *=  2 / burstSamp / imbal
    secondL = complex (realPartL, imagPartL)

    imagPartR *= -2 / burstSamp
    realPartR *=  2 / burstSamp
    secondR = complex (realPartR, imagPartR)

    toUpdate = {'secondBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
    theMeas.update (toUpdate)

    # do some calculations
    print ('firstL/firstR: {}, secondL/secondR: {}'.format (firstL/firstR, secondL/secondR))
    print ('secondL/firstL: {}, secondR/firstR: {}'.format (secondL/firstL, secondR/firstR))

    # point to next burst
    datum += burstSamp
    
# create setup file, overwrite previous
print ("Writing setup file '{}.json'".format (fName))
with open(fName + '.json', 'w') as jFile:
        json.dump(theTree, jFile, indent = 2)
        jFile.write('\n')
