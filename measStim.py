#!/usr/bin/env python3
'''
Python script to measure the ratio between two impedances
using a gated toneburst technique. Creates a stimulus file
on local mass storage. Assumes the response file will be
created by another program.
M. Williamsen, 1 January 2025
'''

import wave, math, struct, json, sys
print ('Useage: python3 measStim.py fileNameNoExtension')

# initialize global setup
fName = 'acBridge'
theTree = {
    'fileName': fName,      # file name, no extension
    'amplL1': 28000,        # max sample value first left
    'amplR1': 28000,        # max sample value first right
    'amplL2': 28000,        # max sample value second left
    'amplR2': 28000,        # max sample value second right
    'halfPiOffset': 123,    # samples per quarter wavelength
    'sampleRate': 44100,    # samples per second
    'startDelay': 0         # samples before first burst
    }

# check for command line arg
if 1 < len(sys.argv): fName = sys.argv[1]

# try to load setup file
try:
    with open (fName + '.stim', 'r') as setupFile:
        aTree = json.load (setupFile)
        if aTree: theTree.update (aTree)
        print ("Loading setup file '{}.stim'".format (fName))
except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
    print ("Failed to load setup file '{}.stim'".format (fName))
    print (e)

'''
Given a sample rate and the samples per quarter wavelength,
compute the samples per cycle, frequency, and cycles per burst
adjusted so each burst contains complete cycles.
'''

# fill in the details
fName = theTree ['fileName']
amplL1 = theTree ['amplL1']
amplR1 = theTree ['amplR1']
amplL2 = theTree ['amplL2']
amplR2 = theTree ['amplR2']
offs = theTree ['halfPiOffset']
sampRate = theTree ['sampleRate']
theTree ['samplesPerCycle'] = nSamp = 4 * offs
hertz = sampRate / nSamp
theTree ['frequency'] = round (hertz, 2)
theTree ['cyclesPerBurst'] = nCycle = int (hertz / 2)
incr = 2.0 * math.pi / nSamp
delay = theTree ['startDelay']
print (json.dumps(theTree, indent = 2))

'''
Bursts are approximately 1/2 second in length, doubled up
so the stimulus file contains about one second of left channel
excitation, one second of silence, and one second of right
channel excitation. The total file length will be about three
seconds, slightly more than 1/2 megabyte on disk.
'''

# create stimulus file, overwrite previous
print ("Writing wave file '{}.wav' with {} bytes of data"
    .format (fName, 24 * nSamp * nCycle))
with wave.open(fName + '.wav', 'wb') as waveFile:
    waveFile.setsampwidth (2)   # bytes per channel
    waveFile.setnchannels (2)   # channels per sample
    waveFile.setframerate (sampRate)

    # write startup delay
    aCycle = bytearray (struct.pack ('<hh', 0, 0))
    for n in range (delay):
        waveFile.writeframes (aCycle)

    # build a cycle of stimulus in memory
    theCycle = [math.sin ((n + 0.5) * incr) for n in range (nSamp)]

    # write two bursts to left channel
    aCycle = bytearray ()
    for n in range (nSamp):
        aSample = struct.pack ('<hh', round (amplL1 * theCycle [n]), round (amplR1 * theCycle [n]))
        aCycle.extend (aSample)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)

    # write two bursts of silence
    aCycle = bytearray ()
    for n in range (nSamp):
        aSample = struct.pack ('<hh', 0, 0)
        aCycle.extend (aSample)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)

    # write two bursts to right channel
    aCycle = bytearray ()
    for n in range (nSamp):
        aSample = struct.pack ('<hh', round (amplL2 * theCycle [n]), round (amplR2 * theCycle [n]))
        aCycle.extend (aSample)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)
    for n in range (nCycle):
        waveFile.writeframes (aCycle)

# create setup file, overwrite previous
print ("Writing setup file '{}.stim'".format (fName))
with open(fName + '.stim', 'w') as jFile:
        json.dump(theTree, jFile, indent = 2)
        jFile.write('\n')
