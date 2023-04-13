
# -------------------------------------------------------------------------- #
# ---------------------------- Imported Modules ---------------------------- #

# General modules
import os
import sys
import scipy

# Import baseline files
sys.path.append(os.path.dirname(__file__) + "/Helper Files/")
import _baselineProtocols

# Import filtering file
import _filteringProtocols as filteringMethods # Import Files with Filtering Methods

# -------------------------------------------------------------------------- #
# ----------------------------- DPV Protocols ------------------------------ #

class dpvProtocols:
    
    def __init__(self):
        # Define filtering class
        self.filteringMethods = filteringMethods.filteringMethods()
    
    def useBaselineSubtraction(self, current, potential, polynomialOrder, reductiveScale):
        # Get Baseline from Iterative Polynomial Subtraction
        polynomialBaselineFit = _baselineProtocols.polynomialBaselineFit()
        baseline = polynomialBaselineFit.baselineSubtractionAPI(current, polynomialOrder, reductiveScale)
        # Find Current After Baseline Subtraction
        baselineCurrent = current - baseline
        
        smoothCurrent = scipy.interpolate.UnivariateSpline(potential, baselineCurrent, s=0.001, k=5)
        smoothCurrentPeaks = scipy.signal.find_peaks(smoothCurrent.derivative(n=1)(potential), prominence=10E-10)
        
        if len(smoothCurrentPeaks[0]) > 0:
            # bestPeak = smoothCurrentPeaks[1]['prominences'].argmax()
            # peakIndices = smoothCurrentPeaks[0][bestPeak]
            peakIndices = smoothCurrentPeaks[0]
        else:
            peakIndices = [];
        
        return baseline, baselineCurrent, peakIndices
            
    def useLinearFit(self, current, potential, reductiveScale):
        # Get Baseline from Iterative Polynomial Subtraction
        linearBaselineFit = _baselineProtocols.bestLinearFit2()
        # Remove the baseline from the data
        baseline = linearBaselineFit.findBaseline(potential, current*reductiveScale)*reductiveScale
        baselineCurrent = current - baseline
        # Find the Peak Current After Baseline Subtraction
        peakIndices = linearBaselineFit.findPeakGeneral(potential, baselineCurrent*reductiveScale)
        
        return baseline, baselineCurrent, peakIndices
        
