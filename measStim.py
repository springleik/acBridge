#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Creates a stimulus wave
file on local mass storage. Assumes the response wave file
will be created by another program.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys

# check for command line args
if len (sys.argv) != 3:
    print ('Useage: python3 measStim.py inFileNameNoExt outFileNameNoExt')
    quit ()
inFileName = sys.argv[1]    # setup for creating stimulus file
outFileName = sys.argv[2]   # setup for analyzing response file

# load setup file
theTree = [{}]
try:
    with open (inFileName + '.json', 'r') as setupFile:
        theTree = json.load (setupFile)
        print ("Loading setup file '{}.json'".format (inFileName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.json'".format (inFileName))
    print (e)

# initialize setup
def initializeDetails (aMeas):
    aMeas.setdefault ('amplL1', 20000)          # max sample value first left
    aMeas.setdefault ('amplR1', 20000)          # max sample value first right
    aMeas.setdefault ('amplL2', 20000)          # max sample value second left
    aMeas.setdefault ('amplR2', 20000)          # max sample value second right
    aMeas.setdefault ('requestFreq', 100.0)     # requested frequency
    aMeas.setdefault ('sampleRate', 44100)      # samples per second
    aMeas.setdefault ('startDelay', 44100)      # silence before each burst
    aMeas.setdefault ('imbalanceOut', 1.0)      # output channel balance L/R

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
so the stimulus file contains silence followed by up to one
second of left channel excitation, more silence, then one second
of right channel excitation. The total measurement length will
be about 4 seconds, somewhat less than 3/4 megabyte on disk.
'''

# create stimulus file, overwrite existing file if any
byteCount = 0
with wave.open(inFileName + '.wav', 'wb') as waveFile:
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

        # build four cells of stimulus in memory
        theCycle = [math.sin ((n + 0.5) * incr) for n in range (burstSamp)]

        # optionally add in harmonic shaping
        # theCycle [:] = [(theCycle [n] - math.sin (2 * (n + 0.5) * incr) / 2) for n in range (burstSamp)]

        # write silent startup delay, 4 bytes per frame
        aCycle = bytearray (4 * delay)
        waveFile.writeframes (aCycle)
        byteCount += len (aCycle)

        # write two bursts (eight cells) to left channel
        aCycle = bytearray ()
        for n in range (burstSamp):
            aSample = struct.pack ('<hh', round (ampL1 * theCycle [n]),
                round (ampR1 * theCycle [n] * imbal))
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

        # write another silent delay
        aCycle = bytearray (4 * delay)
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
print ("Wrote wave file '{}.wav' with {} bytes of data".format (inFileName, byteCount))

# create setup file with decorated tree, overwrite existing file if any
print ("Writing setup file '{}.json'".format (outFileName))
with open(outFileName + '.json', 'w') as jsonFile:
        json.dump(theTree, jsonFile, indent = 2)
        jsonFile.write('\n')
