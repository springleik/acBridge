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

# initialize global setup
fName = 'acMeasure'
theTree = {
    'halfPiOffset': 69,     # samples per quarter wavelength
    'sampleRate': 44100,    # samples per second
    'imbalance': 0.99809    # input channel balance L/R
    }

# check for command line arg
if 1 < len(sys.argv): fName = sys.argv[1]

# try to load setup file
try:
    with open (fName + '.json', 'r') as setupFile:
        aTree = json.load (setupFile)
        if aTree: theTree.update (aTree)
        print ("Loading setup file '{}.json'".format (fName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.json'".format (fName))
    print (e)

'''
Given a sample rate and the samples per quarter wavelength,
compute the samples per cycle, frequency, and cycles per burst
adjusted so each burst contains complete cycles.
'''

# fill in the details
offs = theTree ['halfPiOffset']
sampRate = theTree ['sampleRate']
imbal = theTree ['imbalance']
theTree ['samplesPerCycle'] = nSamp = 4 * offs
hertz = sampRate / nSamp
theTree ['frequency'] = round (hertz, 2)
theTree ['cyclesPerBurst'] = nCycle = int (hertz / 2)
incr = 2.0 * math.pi / nSamp
print (json.dumps(theTree, indent = 2))

'''
Bursts are approximately 1/2 second in length, doubled up
so the stimulus file contains about one second of left channel
excitation, one second of silence, and one second of right
channel excitation. The total file length will be about three
seconds, slightly more than 1/2 megabyte on disk.
'''

# read response file
print ("Reading wave file '{}.wav'.".format (fName))
waveFile = wave.open(fName + '.wav', 'rb')
theParams = waveFile.getparams ()
print ('Wave file parameters:')
print (json.dumps (theParams._asdict (), indent = 2))

# compute burst length in frames
burstLength = nSamp * nCycle
expectFrames = burstLength * 2 * 3
actualFrames = getattr (theParams, 'nframes')
print ('Expected {} frames, found {}'.format (expectFrames, actualFrames))
if actualFrames < expectFrames:
    print ('Done, not enough frames in response file!')
    quit ()

# compute reference vector
refVec = [math.cos ((n + 0.5) * incr) for n in range (burstLength)]

# analyze first response burst
waveFile.setpos (burstLength - offs)
sinBytes = waveFile.readframes (burstLength)
sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

waveFile.setpos (burstLength)
cosBytes = waveFile.readframes (burstLength)
cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

# normalize
imagPartL *= -2 / burstLength / imbal
realPartL *=  2 / burstLength / imbal
firstL = complex (realPartL, imagPartL)

imagPartR *= -2 / burstLength
realPartR *=  2 / burstLength
firstR = complex (realPartR, imagPartR)

toUpdate = {'firstBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
theTree.update (toUpdate)

# analyze silent gap
waveFile.setpos (3 * burstLength - offs)
sinBytes = waveFile.readframes (burstLength)
sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

waveFile.setpos (3 * burstLength)
cosBytes = waveFile.readframes (burstLength)
cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

# normalize
imagPartL *= -2 / burstLength / imbal
realPartL *=  2 / burstLength / imbal
silentL = complex (realPartL, imagPartL)

imagPartR *= -2 / burstLength
realPartR *=  2 / burstLength
silentR = complex (realPartR, imagPartR)

toUpdate = {'silentBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
theTree.update (toUpdate)

# analyze second response burst
waveFile.setpos (5 * burstLength - offs)
sinBytes = waveFile.readframes (burstLength)
sinVecL, sinVecR = zip (*[t for t in struct.iter_unpack ('<hh', sinBytes)])
imagPartL = sum ([x * y for (x,y) in zip (refVec, sinVecL)])
imagPartR = sum ([x * y for (x,y) in zip (refVec, sinVecR)])

waveFile.setpos (5 * burstLength)
cosBytes = waveFile.readframes (burstLength)
cosVecL, cosVecR = zip (*[t for t in struct.iter_unpack ('<hh', cosBytes)])
realPartL = sum ([x * y for (x,y) in zip (refVec, cosVecL)])
realPartR = sum ([x * y for (x,y) in zip (refVec, cosVecR)])

# normalize
imagPartL *= -2 / burstLength / imbal
realPartL *=  2 / burstLength / imbal
secondL = complex (realPartL, imagPartL)

imagPartR *= -2 / burstLength
realPartR *=  2 / burstLength
secondR = complex (realPartR, imagPartR)

toUpdate = {'secondBurst': {'left': [realPartL, imagPartL], 'right': [realPartR, imagPartR]}}
theTree.update (toUpdate)

# do some calculations
print ('firstL/firstR: {}, secondL/secondR: {}'.format (firstL/firstR, secondL/secondR))
print ('secondL/firstL: {}, secondR/firstR: {}'.format (secondL/firstL, secondR/firstR))

# create setup file, overwrite previous
print ("Writing setup file '{}.json'".format (fName))
with open(fName + '.json', 'w') as jFile:
        json.dump(theTree, jFile, indent = 2)
        jFile.write('\n')
