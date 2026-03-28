# How to Obtain the Results of the IEEE Paper

You can use the Python scripts in this repo to obtain the results given in my paper "Digitizing Bridge Measures RC Time Constants" in the IEEE Transactions on Instrumentation and Measurement, vol. 75, pp. 1-8, 2026, doi: [10.1109/TIM.2026.3670597](https://doi.org/10.1109/TIM.2026.3670597).

## Table I

Table I gives the result of obtaining a normalized calibration matrix which accounts for channel imbalance, phase shift, and crosstalk between the two output channels of a stereo digital-to-analog converter (DAC). The JSON text at the end of the console output contains the calibration coefficients in Table I. The Python output has as many as 16 digits, while the coefficients were trimmed to 9 places for publication.
```
MarksiMac:TableI williamm$ python3 ../measCal.py c
Loading stimulus setup file 'c.json'
Loading response setup file 'c.json'
Frequency list:  [159.15494]
689442.9504597873 -3438748.407541822 2.8961486478172183 5.602626267082165
689440.0964874191 -3438703.0535648605 2.7253433676136356 6.227260394429701
689446.9704608072 -3438747.786816199 2.7463025981834965 4.9230145473754305
689456.0719582475 -3438760.331477792 3.119491529580522 6.5006693305985035
689453.9258999722 -3438754.3744191313 2.7461440633718164 6.341303497703125
4.690570587795835 5.210716809393553 695241.6138743705 -3463495.3933703946
4.680168509581562 6.425443155829652 695246.878492828 -3463514.839532161
5.3118875971339925 5.085907807550948 695240.171540798 -3463448.176564105
5.314290578602028 5.143490137490854 695244.0207251265 -3463488.0792900156
5.035411804985136 5.7835538000645865 695248.0771628415 -3463502.9253214723
{
  "requestFreq": 159.15494,
  "calMatrix": [
    [
      [
        0.9999999999999635,
        -3.954293395087328e-12
      ],
      [
        1.4841717799931693e-06,
        -1.1198380603671274e-06
      ]
    ],
    [
      [
        1.2558385018258873e-06,
        -1.6975883831840708e-06
      ],
      [
        0.9928087081139604,
        -0.0002299546742848992
      ]
    ]
  ]
}
```

## Table II

## Table III

## Table IV
