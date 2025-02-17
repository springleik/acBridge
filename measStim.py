#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Creates a stimulus wave
file on local mass storage. Assumes the response wave file
will be created by another program.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys
print ('Useage: python3 measStim.py fileNameNoExtension')

# initialize setup
def initializeDetails (aMeas):
    aMeas.setdefault ('amplL1', 28000)          # max sample value first left
    aMeas.setdefault ('amplR1', 28000)          # max sample value first right
    aMeas.setdefault ('amplL2', 28000)          # max sample value second left
    aMeas.setdefault ('amplR2', 28000)          # max sample value second right
    aMeas.setdefault ('sampleRate', 44100)      # samples per second
    aMeas.setdefault ('imbalanceOut', 0.99712)  # output channel balance L/R
    aMeas.setdefault ('requestFreq', 100.0)     # requested frequency
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
Given a sample rate and requested frequency, compute the number of
samples per cell, cycles in four cells, and actual frequency.
Where a cell is at most 1/8 second, and four cells contain full
waves.
'''

# fill in the details for each measurement
def fillInDetails (aMeas):
    sampRate = aMeas ['sampleRate']
    reqFreq = aMeas ['requestFreq']
    cellQuartWaves = 4 * int ((reqFreq / 2 - 1) / 4) + 1
    quartWaveTime = 1 / reqFreq / 4
    cellTime = cellQuartWaves * quartWaveTime
    cellSamp = int (cellTime * sampRate)
    actFreq = cellQuartWaves / cellSamp / 4 * sampRate
    aMeas ['actualFreq'] = round (actFreq, 2)
    aMeas ['cellSamples'] = cellSamp
    numWaves = round (4 * actFreq * cellSamp / sampRate)
    aMeas ['countWaves'] = numWaves

# initialize and fill in details for all measurements
if isinstance (theTree, dict):
    theTree = [theTree]
for theMeas in theTree:
    initializeDetails (theMeas)
    fillInDetails (theMeas)
print (json.dumps(theTree, indent = 2))

'''
Bursts are approximately 1/2 second in length, doubled up
so the stimulus file contains up to one second of left channel
excitation, one second of silence, and one second of right
channel excitation. The total measurement length will be about 3
seconds, slightly more than 1/2 megabyte on disk.
'''

# create stimulus file, overwrite previous
byteCount = 0
with wave.open(fName + '.wav', 'wb') as waveFile:
    waveFile.setsampwidth (2)   # bytes per channel
    waveFile.setnchannels (2)   # channels per sample
    sampRate = theTree [0]['sampleRate']
    waveFile.setframerate (sampRate)
    # iterate over measurements
    for theMeas in theTree:
        # gather details for each measurement
        delay = theMeas ['startDelay']
        ampL1 = theMeas ['amplL1']
        ampL2 = theMeas ['amplL2']
        ampR1 = theMeas ['amplR1']
        ampR2 = theMeas ['amplR2']
        imbal = theMeas ['imbalanceOut']
        cellSamp = theMeas ['cellSamples']
        countWave = theMeas ['countWaves']
        burstSamp = cellSamp * 4
        incr = 2.0 * math.pi * countWave / 4.0 / cellSamp

        # write silent startup delay
        aCycle = bytearray (struct.pack ('<hh', 0, 0))
        for n in range (delay):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

        # build four cells of stimulus in memory
        theCycle = [math.sin ((n + 0.5) * incr) for n in range (burstSamp)]

        # TODO add harmonic shaping

        # write two bursts (eight cells) to left channel
        aCycle = bytearray ()
        for n in range (burstSamp):
            aSample = struct.pack ('<hh', round (ampL1 * theCycle [n]),
                round (ampR1 * theCycle [n] * imbal))
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

        # write two bursts of silence
        aCycle = bytearray ()
        for n in range (burstSamp):
            aSample = struct.pack ('<hh', 0, 0)
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

        # write two bursts to right channel
        aCycle = bytearray ()
        for n in range (burstSamp):
            aSample = struct.pack ('<hh', round (ampL2 * theCycle [n]),
                round (ampR2 * theCycle [n] * imbal))
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

# report success
print ("Wrote wave file '{}.wav' with {} bytes of data"
    .format (fName, byteCount))

# create setup file, overwrite previous
print ("Writing setup file '{}.json'".format (fName))
with open(fName + '.json', 'w') as jFile:
        json.dump(theTree, jFile, indent = 2)
        jFile.write('\n')
