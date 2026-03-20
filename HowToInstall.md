# How to Install acBridge

The _acBridge_ project consists of several Python scripts, and is installed by cloning a copy of the project.
```
gate@RasPi5:~/GitHub $ git clone https://github.com/springleik/acBridge.git
Cloning into 'acBridge'...
remote: Enumerating objects: 383, done.
remote: Counting objects: 100% (58/58), done.
remote: Compressing objects: 100% (41/41), done.
remote: Total 383 (delta 26), reused 47 (delta 16), pack-reused 325 (from 1)
Receiving objects: 100% (383/383), 646.21 KiB | 3.20 MiB/s, done.
Resolving deltas: 100% (221/221), done.
```
To test the installation, clone a copy of the adjacent _PompTree_ project.
```
gate@RasPi5:~/GitHub $ git clone https://github.com/springleik/PompTree.git
Cloning into 'PompTree'...
remote: Enumerating objects: 134, done.
remote: Counting objects: 100% (134/134), done.
remote: Compressing objects: 100% (90/90), done.
remote: Total 134 (delta 79), reused 82 (delta 41), pack-reused 0 (from 0)
Receiving objects: 100% (134/134), 34.39 KiB | 1.04 MiB/s, done.
Resolving deltas: 100% (79/79), done.
```
Navigate to the _check_ folder, clean any previous results, and run the stimulus generator to create a wave file of tone bursts.
```
gate@RasPi5:~/GitHub $ cd acBridge/check/

gate@RasPi5:~/GitHub/acBridge/check $ ls -la
total 20
drwxrwxr-x 2 gate gate 4096 Mar 20 11:47 .
drwxrwxr-x 9 gate gate 4096 Mar 20 11:47 ..
-rwxrwxr-x 1 gate gate   41 Mar 20 11:47 a.json
-rwxrwxr-x 1 gate gate  455 Mar 20 11:47 bRef.json
-rwxrwxr-x 1 gate gate 1545 Mar 20 11:47 cRef.json

gate@RasPi5:~/GitHub/acBridge/check $ ../measStim.py a b
Loading setup file 'a.json'
Wrote wave file 'a.wav' with 1147632 bytes of data
Writing setup file 'b.json'
```
You don't need to use the sound hardware for test purposes, just copy the stimulus file to the response file.
```
gate@RasPi5:~/GitHub/acBridge/check $ cp a.wav b.wav
```
Now run the response analyzer to see what was in the stimulus file.
```
gate@RasPi5:~/GitHub/acBridge/check $ ../measResp.py b c
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
159.162527 4000000.0115386085 8.019616032637323e-08 0.0 0.0 0.0 0.0
Writing setup file 'c.json'
```
Finally, use the _CompTree_ script to compare the stimulus and analysis output files with checked-in references.
```
gate@RasPi5:~/GitHub/acBridge/check $ ../../PompTree/CompTree.py bRef.json b.json
[]
gate@RasPi5:~/GitHub/acBridge/check $ ../../PompTree/CompTree.py cRef.json c.json 1e-8
[]
```
The empty square brackets "[]" mean that no differences were found between the new output files and the archived reference files. In the second comparison we used the optional third argument to set an error delta, allowing test and reference to differ by up to $1 \times 10^{-8}$. Try removing the third argument to see differences that were hidden by the error delta.
