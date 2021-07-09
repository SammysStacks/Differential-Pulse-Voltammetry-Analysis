
"""
Need to Install on the Anaconda Prompt:
    $ conda install openpyxl
    $ conda install seaborn
    $ conda install scipy
    $ pip install natsort
    $ pip install BaselineRemoval
"""
import csv
import os
import sys
import openpyxl as xl
import matplotlib.pyplot as plt
import numpy as np
import re
import math
from scipy.signal import argrelextrema
# Modules for Low Pass Filter
from scipy.signal import butter, lfilter
from scipy.signal import freqs



class bestLinearFit:
    
    def butter_lowpass(self, cutOff, fs, order=5):
        nyq = 0.5 * fs
        normalCutoff = cutOff / nyq
        b, a = butter(order, normalCutoff, btype='low', analog = True)
        return b, a

    def butter_lowpass_filter(self, data, cutOff, fs, order=4):
        b, a = self.butter_lowpass(cutOff, fs, order=order)
        y = lfilter(b, a, data)
        return y
    
    def findLinearBaseline(self, current, potential):
        
        # Low Pass Filter
        current = self.butter_lowpass_filter(current,)

        # Fit Lines to Ends of Graph
        m0, b0 = np.polyfit(potential[0:edgeCollectionLeft], current[0:edgeCollectionLeft], 1)
        mf, bf = np.polyfit(potential[-edgeCollectionRight:-1], current[-edgeCollectionRight:-1], 1)
        potentialNumpy = np.array(potential)
        y0 = m0*potentialNumpy+b0
        yf = mf*potentialNumpy+bf
        
        # Find Where Data Begins to Deviate from the Lines
        stopInitial = np.argwhere(abs(((y0-current)/current)) < errorVal)[-1][0]
        stopFinal = np.argwhere(abs(((yf-current)/current)) < errorVal)[0][0]
        
        # Get the Points inside the Peak
        potentialEnds = potential[0:stopInitial] + potential[stopFinal:-1]
        currentEnds = current[0:stopInitial] + current[stopFinal:-1]
        
        # Fit the Peak with a Cubic Spline
        cs = CubicSpline(potentialEnds, currentEnds)
        xs = np.arange(potential[0], potential[-1], (potential[-1]-potential[0])/len(potential))
        
        # Get the Peak Current (Max Differenc between the Data and the Spline/Background)
        peakCurrents = current[stopInitial:stopFinal+1] - cs(potential[stopInitial:stopFinal+1])
        IpIndex = np.argmax(peakCurrents)
        Ip = peakCurrents[IpIndex]
        Vp = potential[IpIndex+stopInitial]
        
        # Plot Fit
        plt.plot(potential, cs(xs), label="Spline Interpolation")
        axisLimits = [min(current) - min(current)/10, max(current) + max(current)/10]