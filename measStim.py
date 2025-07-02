#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Creates a stimulus wave
file on local mass storage. Assumes the response wave file
will be created by another program.
M. Williamsen, 14 February 2025
'''

import wave, math, struct, json, sys, cmath

# check for command line args
if len (sys.argv) != 3:
    print ('usage: python3 {} inFileNoExt outFileNoExt'.format (sys.argv[0]))
    quit ()
inFileName = sys.argv[1]    # setup for creating stimulus file
outFileName = sys.argv[2]   # setup for analyzing response file

# load setup description file
theTree = {}
try:
    with open (inFileName + '.json', 'r') as setupFile:
        theTree = json.load (setupFile)
        print ("Loading setup file '{}.json'".format (inFileName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.json'".format (inFileName))
    print (e)

# initialize setup, only modify empty fields
sampRate = 44100
def initializeDetails (aMeas) -> dict:
    aMeas.setdefault ('amplitude', 4000000)         # max sample value
    aMeas.setdefault ('ampX', 1.0)                   # max sample value
    aMeas.setdefault ('requestFreq', 159.1549)      # requested frequency
    aMeas.setdefault ('sampleRate', sampRate)       # samples per second
    aMeas.setdefault ('startDelay', 44100)          # silence before each burst
    aMeas.setdefault ('imbalanceOut', [1.0, 0.0])   # output channel balance L/R
    aMeas.setdefault ('imbalanceIn', [1.0, 0.0])    # input channel balance L/R
    return aMeas

'''
Given a sample rate and requested frequency, compute the number of
samples per cell, cycles in four cells, and actual frequency.
Where a cell is at most 1/8 second, and four cells contain full
waves.
'''

# fill in details for each measurement
def fillInDetails (aMeas) -> dict:
    sampRate = aMeas ['sampleRate']
    reqFreq = aMeas ['requestFreq']
    cellQuartWaves = 4 * int ((reqFreq / 2 - 1) / 4) + 1
    quartWaveTime = 1 / reqFreq / 4
    cellTime = cellQuartWaves * quartWaveTime
    cellSamp = int (cellTime * sampRate)
    actFreq = cellQuartWaves / cellSamp / 4 * sampRate
    aMeas ['actualFreq'] = round (actFreq, 6)
    aMeas ['cellSamples'] = cellSamp
    numWaves = round (4 * actFreq * cellSamp / sampRate)
    aMeas ['countWaves'] = numWaves
    return aMeas

# enclose in array if not already
if isinstance (theTree, dict):
    theTree = [theTree]

# initialize and fill in details for all measurements
# carry forward settings found in each measurement
prevTree = initializeDetails ({})
for theMeas in theTree:
    # skip over comments and other non-measurements
    if not isinstance (theMeas, dict): continue
    for key, value in prevTree.items ():
        theMeas.setdefault (key, value)
    fillInDetails (theMeas)
    prevTree = theMeas

# print (json.dumps(theTree, indent = 2))

'''
Bursts are approximately 1/2 second times two, so the stimulus
file contains silence followed by up to one second of left
channel excitation, more silence, then one second of right
channel excitation. The total measurement length will be about
4 seconds, somewhat less than 3/4 megabyte on disk.
'''

# create stimulus file, overwrite existing file if any
byteCount = 0
with wave.open(inFileName + '.wav', 'wb') as waveFile:
    waveFile.setsampwidth (3)   # bytes per channel
    waveFile.setnchannels (2)   # channels per sample
    waveFile.setframerate (sampRate)

    # iterate over measurements
    for theMeas in theTree:
        # skip over comments and other non-measurements
        if not isinstance (theMeas, dict): continue
        # gather details for each measurement
        ampl = theMeas ['amplitude']
        ampX = theMeas ['ampX']
        delay = theMeas ['startDelay']
        imbal = complex (theMeas ['imbalanceOut'][0],
            theMeas ['imbalanceOut'][1])
        cellSamp = theMeas ['cellSamples']
        countWave = theMeas ['countWaves']
        burstSamp = cellSamp * 4
        incr = math.tau * countWave / 4.0 / cellSamp

        # build four cells of stimulus in memory
        fundSin = [cmath.exp (complex (0, (n + 0.5) * incr))
            for n in range (burstSamp)]

        # write silent startup delay, 6 bytes per frame
        aCycle = bytearray (6 * delay)
        waveFile.writeframes (aCycle)
        byteCount += len (aCycle)

        # write four cells twice to both channels
        aCycle = bytearray ()
        for n in range (burstSamp):
            floatL = (ampl * fundSin [n]).imag
            floatR = (0 * ampl * fundSin [n] * imbal).imag
            bytesL = math.floor (floatL).to_bytes (3, byteorder = 'little', signed = True)
            bytesR = math.floor (floatR).to_bytes (3, byteorder = 'little', signed = True)
            aSample = struct.pack ('<BBBBBB', *bytesL, *bytesR)
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

        # write another silent delay
        aCycle = bytearray (6 * delay)
        waveFile.writeframes (aCycle)
        byteCount += len (aCycle)

        # write four cells twice to both channels
        aCycle = bytearray ()
        for n in range (burstSamp):
            floatL = (0 * ampl * fundSin [n] * ampX).imag
            floatR = (ampl * fundSin [n] * imbal).imag
            bytesL = math.floor (floatL).to_bytes (3, byteorder = 'little', signed = True)
            bytesR = math.floor (floatR).to_bytes (3, byteorder = 'little', signed = True)
            aSample = struct.pack ('<BBBBBB', *bytesL, *bytesR)
            aCycle.extend (aSample)
        for n in range (2):
            waveFile.writeframes (aCycle)
            byteCount += len (aCycle)

# report success
print ("Wrote wave file '{}.wav' with {} bytes of data".format (inFileName, byteCount))

# create setup description file with decorated tree
# overwrite existing file if any
print ("Writing setup file '{}.json'".format (outFileName))
with open(outFileName + '.json', 'w') as jsonFile:
        json.dump(theTree, jsonFile, indent = 2)
        jsonFile.write('\n')
