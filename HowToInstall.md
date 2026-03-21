# How to Install acBridge

The _acBridge_ project consists of several Python scripts which can generate a stimulus wave file, analyze a response wave file, and calibrate a digital-to-analog converter (DAC). The following code blocks show everything in the terminal window including the console prompt, commands you type, and console output resulting from your commands. While these were copied from a MacOS terminal window, the steps are the same for Windows and Linux. Start by cloning the _acBridge_ project repository.
```
MarksiMac:GitHub williamm$ git clone https://github.com/springleik/acBridge.git
Cloning into 'acBridge'...
remote: Enumerating objects: 399, done.
remote: Counting objects: 100% (74/74), done.
remote: Compressing objects: 100% (52/52), done.
remote: Total 399 (delta 32), reused 60 (delta 19), pack-reused 325 (from 1)
Receiving objects: 100% (399/399), 649.84 KiB | 5.24 MiB/s, done.
Resolving deltas: 100% (227/227), done.
```
To test the installation, clone a copy of the adjacent _PompTree_ project.
```
MarksiMac:GitHub williamm$ git clone https://github.com/springleik/PompTree.git
Cloning into 'PompTree'...
remote: Enumerating objects: 134, done.
remote: Counting objects: 100% (134/134), done.
remote: Compressing objects: 100% (90/90), done.
remote: Total 134 (delta 79), reused 82 (delta 41), pack-reused 0 (from 0)
Receiving objects: 100% (134/134), 34.39 KiB | 1.56 MiB/s, done.
Resolving deltas: 100% (79/79), done.
```
Navigate to the _check_ folder in the _acBridge_ project, clean any previous results, and run the stimulus generator to create a wave file with a pair of tone bursts. The first burst is in the left channel, the second burst is in the right channel. Frequency for both is 1000 rad/sec, or about 159 Hz.
```
MarksiMac:GitHub williamm$ cd acBridge/check/
```
```
MarksiMac:check williamm$ ls -la
total 48
drwxr-xr-x   8 williamm  staff   272 Mar 21 14:23 .
drwxr-xr-x  19 williamm  staff   646 Mar 21 14:23 ..
-rwxr-xr-x   1 williamm  staff    33 Mar 21 14:23 a.json
-rwxr-xr-x   1 williamm  staff   123 Mar 21 14:23 a1.json
-rw-r--r--   1 williamm  staff   455 Mar 21 14:23 b1Ref.json
-rwxr-xr-x   1 williamm  staff   455 Mar 21 14:23 bRef.json
-rw-r--r--   1 williamm  staff  1545 Mar 21 14:23 c1Ref.json
-rwxr-xr-x   1 williamm  staff  1545 Mar 21 14:23 cRef.json
```
```
MarksiMac:check williamm$ ../measStim.py a b
Loading setup file 'a.json'
Wrote wave file 'a.wav' with 1147632 bytes of data
Writing setup file 'b.json'
```
For the first check you won't need the sound hardware, just copy the stimulus file to the response file.
```
MarksiMac:check williamm$ cp a.wav b.wav
```
Now run the response analyzer to see what was in the stimulus file.
```
MarksiMac:check williamm$ ../measResp.py b c
Loading setup file 'b.json'
Reading wave file 'b.wav'
Wave file parameters:
{
  "nchannels": 2,
  "sampwidth": 3,
  "framerate": 44100,
  "nframes": 191272,
  "comptype": "NONE",
  "compname": "not compressed"
}
Expected 191272 frames, found 191272
159.162527 4000000.0115386085 8.019764318556365e-08 0.0 0.0 0.0 0.0
Writing setup file 'c.json'
```
Finally, run _CompTree.py_ to compare the stimulus and analysis output files with the checked-in reference files.
```
MarksiMac:check williamm$ ../../PompTree/CompTree.py bRef.json b.json
[]
MarksiMac:check williamm$ ../../PompTree/CompTree.py cRef.json c.json 1e-8
[]
```
The empty square brackets "[]" in the output mean that no differences were found between the new output files and the archived reference files. In the second comparison we used the optional third argument to set an error delta, allowing test and reference to differ by up to $1 \times 10^{-8}$. Try removing the third argument to see if any differences were hidden by the error delta. To help familiarize yourself with these tools I've prepared measurement description file _a1.json_ which specifies four tone burst pairs at 100, 1000, 10000, and 100000 rad/sec. To continue, generate a new stimulus file with _a1.json_ as input.
```
MarksiMac:check williamm$ ../measStim.py a1 b1
Loading setup file 'a1.json'
Wrote wave file 'a1.wav' with 4576608 bytes of data
Writing setup file 'b1.json'
```
Again bypassing the hardware, copy the stimulus file to the response file.
```
MarksiMac:check williamm$ cp a1.wav b1.wav
```
And run the response analyzer to see what was in the stimulus file.
```
MarksiMac:check williamm$ ../measResp.py b1 c1
Loading setup file 'b1.json'
Reading wave file 'b1.wav'
Wave file parameters:
{
  "nchannels": 2,
  "sampwidth": 3,
  "framerate": 44100,
  "nframes": 762768,
  "comptype": "NONE",
  "compname": "not compressed"
}
Expected 762768 frames, found 762768
15.916747 4000000.0030160593 4.642234675717688e-09 0.0 0.0 0.0 0.0
159.162527 4000000.0115386085 8.019764318556365e-08 0.0 0.0 0.0 0.0
1591.571252 4000000.0000083633 4.444375808379066e-07 0.0 0.0 0.0 0.0
15916.876157 3999999.995502146 -8.253701325626454e-07 0.0 0.0 0.0 0.0
Writing setup file 'c1.json'
```
