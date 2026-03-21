# How to Install acBridge

The _acBridge_ project consists of several Python scripts which can generate a stimulus wave file, analyze a response wave file, and calibrate a digital-to-analog converter (DAC). The following code blocks show everything in the terminal window including the console prompt, commands you type, and console output resulting from your commands. While these were copied from a Linux terminal window, the steps are the same for Windows and MacOS. Start by cloning the _acBridge_ project repository.
```

```
To test the installation, clone a copy of the adjacent _PompTree_ project.
```

```
Navigate to the _check_ folder in the _acBridge_ project, clean any previous results, and run the stimulus generator to create a wave file with a pair of tone bursts. The first burst is in the left channel, the second burst is in the right channel. Frequency for both is 1000 rad/sec, or about 159 Hz.
```

```
For the first check you won't need the sound hardware, just copy the stimulus file to the response file.
```

```
Now run the response analyzer to see what was in the stimulus file.
```

```
Finally, run _CompTree.py_ to compare the stimulus and analysis output files with the checked-in reference files.
```

```
The empty square brackets "[]" in the output mean that no differences were found between the new output files and the archived reference files. In the second comparison we used the optional third argument to set an error delta, allowing test and reference to differ by up to $1 \times 10^{-8}$. Try removing the third argument to see if any differences were hidden by the error delta. To help familiarize yourself with these tools I've prepared measurement description file _a1.json_ which specifies four tone burst pairs at 100, 1000, 10000, and 100000 rad/sec. To continue, generate a new stimulus file with _a1.json_ as input. Output shown below is from a MacOS terminal window
```

```
Again bypassing the hardware, copy the stimulus file to the response file.
```

```
And run the response analyzer to see what was in the stimulus file.
```

```
