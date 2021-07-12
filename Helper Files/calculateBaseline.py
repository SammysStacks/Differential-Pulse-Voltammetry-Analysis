
"""
Need to Install in the Python Enviroment Beforehand:
    $ pip install BaselineRemoval
"""

# Import Basic Modules
import numpy as np
# Import Modules for Baseline Subtraction
from BaselineRemoval import BaselineRemoval
# Import Modules for Low Pass Filter
from scipy.signal import butter, lfilter 
# Import Modules to Find Peak
from scipy.interpolate import UnivariateSpline
import scipy.signal
# Modules to Plot
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------#
# --------------------- Specify/Find File Names -----------------------------#

class polynomialBaselineFit:
    
    def baselineSubtractionAPI(self, current, polynomialOrder, reductiveScan):
        # Get Baseline Depending on Ox/Red Curve
        if reductiveScan:
            baseObj = BaselineRemoval(-current)
            baseline = current + baseObj.ModPoly(polynomialOrder)
        else:
            baseObj = BaselineRemoval(current)
            baseline = current - baseObj.ModPoly(polynomialOrder)
        # Return Baseline
        return baseline
    
    def baselineSubtraction(self, potential, current, polynomialOrder, Iterations, reductiveScan):
        if reductiveScan:
            baseline = - self.getBaseline(potential, -current, Iterations, polynomialOrder)
        else:
            baseline = self.getBaseline(potential, current, Iterations, polynomialOrder)
        # Return Baseline
        return baseline
    
    def getBaseline(self, x, y, Iterations, order):
        yHold = y.copy()
        for _ in range(Iterations):
            fitI = np.polyfit(x, yHold, order)
            baseline = np.polyval(fitI, x)
            for i in range(len(y)):
                if yHold[i] > baseline[i]:
                    yHold[i] = baseline[i]
        return baseline
        

class bestLinearFit:
    
    def __init__(self, potential, current):
        self.potential = potential
        self.current = current
        self.linearFit = []
        self.baseline = None
    
    def butter_lowpass(self, cutOff, fs, order=5):
        nyq = 0.5 * fs
        normalCutoff = cutOff / nyq
        b, a = butter(order, normalCutoff, btype='low', analog = True)
        return b, a

    def butter_lowpass_filter(self, data, cutOff, fs, order=4):
        b, a = self.butter_lowpass(cutOff, fs, order=order)
        y = lfilter(b, a, data)
        return y
    
    def findPeak(self, smoothCurrent, reductiveScale = 1, ignoredBoundaryPoints = 10):
        smoothCurrentPeaks = scipy.signal.find_peaks(reductiveScale*smoothCurrent.derivative(n=1)(self.potential), prominence=10E-4, width=4)
        allPeakInds = smoothCurrentPeaks[0]
        allProminences = smoothCurrentPeaks[1]['prominences']
        # Remove Peaks Nearby Boundaries
        allProminences = allProminences[np.logical_and(allPeakInds < len(self.potential) - ignoredBoundaryPoints, allPeakInds >= ignoredBoundaryPoints)]
        allPeakInds = allPeakInds[np.logical_and(allPeakInds < len(self.potential) - ignoredBoundaryPoints, allPeakInds >= ignoredBoundaryPoints)]
        
        if len(allPeakInds) > 0:
            bestPeak = allProminences.argmax()
            peakInd = allPeakInds[bestPeak]
        else:
            peakInd = None
        
        return peakInd
    
    def findInflection(self, smoothCurrent, peakInd):
        smoothCurrentPeaks = scipy.signal.find_peaks(smoothCurrent.derivative(n=2)(self.potential), prominence=10E-10)
        allPeakInds = smoothCurrentPeaks[0]
        # Remove Peaks Nearby Boundaries
        ignoredBoundaryPoints = 10
        allPeakInds = allPeakInds[np.logical_and(allPeakInds < len(self.potential) - ignoredBoundaryPoints, allPeakInds >= ignoredBoundaryPoints)]

        leftPoints = allPeakInds[allPeakInds < peakInd]
        if len(leftPoints) > 0 and len(leftPoints) < len(allPeakInds):
            leftInd = np.where(allPeakInds == leftPoints[-1])[0][0]
            leftCutInd = allPeakInds[leftInd]
            rightCutInd = allPeakInds[leftInd + 1]
        else:
            leftCutInd = None; rightCutInd = None
        
        return leftCutInd, rightCutInd
    
    def createTangentLine(self, peakInd, smoothCurrent, reductiveScale = 1, nearbyBuffer = 10, saveGoodInd = 4):
        # Divide the Current into Two Groups: Left and Right
        leftCurrent = self.current[0:peakInd]
        rightCurrent = self.current[peakInd+1:len(self.current)]
        # Store Possibly Good Tangent Indexes
        goodTangentInd = {}
        for goodInd in range(1+saveGoodInd):
            goodTangentInd[goodInd] = []
        
        for rightInd, rightPoint in enumerate(rightCurrent):
            rightInd = rightInd + peakInd + 1
            for leftInd, leftPoint in enumerate(leftCurrent):
                # Fit Lines to Ends of Graph
                m0, b0 = np.polyfit(self.potential[[leftInd, rightInd]], self.current[[leftInd, rightInd]], 1)
                linearFit = m0*self.potential + b0
                
                # Find the Number of Points Above/Below the Tangent Line for Red/Ox
                regionalLimits = np.s_[max(0,leftInd-nearbyBuffer):max(len(self.current),rightPoint+nearbyBuffer)]
                numWrongSideOfTangent = sum(reductiveScale*(linearFit[regionalLimits] - smoothCurrent(self.potential)[regionalLimits]) > 0)
                # If a Tangent Line is Drawn Correctly, Return the Tangent Points' Indexes
                if numWrongSideOfTangent <= saveGoodInd:
                    goodTangentInd[numWrongSideOfTangent].append((leftInd, rightInd))
        
        # If Nothing Found, Try and Return a Semi-Optimal Tangent Position
        for goodInd in sorted(goodTangentInd.keys()):
            if len(goodTangentInd[goodInd]) != 0:
                return min(goodTangentInd[goodInd], key=lambda tangentPair: tangentPair[1]-tangentPair[0])
        return None, None
        
    
    def findLinearBaseline(self, reductiveScan):
        # Smooth Current to Remove Extremely Small Peaks
        smoothCurrent = UnivariateSpline(self.potential, self.current, s=10E-6, k=5)
        # Find the Peak
        reductiveScale = -(2*reductiveScan - 1)
        peakInd = self.findPeak(smoothCurrent, reductiveScale)
        
        # If a Peak Was Found, Find Baseline
        if peakInd != None:
            # Find the Peak Bounds
            leftCutInd, rightCutInd = self.createTangentLine(peakInd, smoothCurrent, reductiveScale)
            print(leftCutInd, rightCutInd, peakInd)
            # If No Bounds Found Than it Was a Single Point Deviation
            if None in [leftCutInd, rightCutInd]:
                return self.current
            
            # Fit Lines to Ends of Graph
            m0, b0 = np.polyfit(self.potential[[leftCutInd, rightCutInd]], self.current[[leftCutInd, rightCutInd]], 1)
            self.linearFit = m0*self.potential + b0
            
            # Piece Together the Current's Baseline
            self.baseline = np.concatenate((self.current[0:leftCutInd+1], self.linearFit[leftCutInd+1: rightCutInd], self.current[rightCutInd:len(self.current)]))
            return self.baseline
        # Else, the Baseline is the Potential (No Peak)
        else:
            return self.current
    
    def plotLinearFit(self, leftCutInd, rightCutInd, peakInd):
        plt.figure()
        plt.plot(self.potential, self.current);
        plt.plot(self.potential[[leftCutInd, rightCutInd, peakInd]],  self.current[[leftCutInd, rightCutInd, peakInd]], 'o');
        plt.plot(self.potential, self.linearFit, linewidth=0.3)
        plt.show()
        
        plt.figure()
        plt.plot(self.potential, self.current, label = "True Data")
        plt.plot(self.potential, self.baseline, label="Baseline Current")
        plt.show()
        


