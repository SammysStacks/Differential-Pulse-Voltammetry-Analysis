
# -------------------------------------------------------------------------- #
# ---------------------------- Imported Modules ---------------------------- #

# General
import scipy

# Import filtering file
import _baselineProtocols   # Import class with baseline methods.
import _filteringProtocols  # Import class with filtering methods.

# -------------------------------------------------------------------------- #
# ----------------------------- DPV Protocols ------------------------------ #

class dpvProtocols:
    
    def __init__(self):
        # Initialize general data preperation classes.
        self.filteringMethods = _filteringProtocols.filteringMethods()
        
        # Initialize baseline subtraction classes.
        self.linearBaselineFit = _baselineProtocols.bestLinearFit2()
        self.polynomialBaselineFit = _baselineProtocols.polynomialBaselineFit()

    def useBaselineSubtraction(self, current, potential, polynomialOrder, reductiveScale):
        # Get Baseline from Iterative Polynomial Subtraction
        baseline = self.polynomialBaselineFit.baselineSubtractionAPI(current, polynomialOrder, reductiveScale)
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
        # Remove the baseline from the data
        baseline = self.linearBaselineFit.findBaseline(potential, current*reductiveScale)*reductiveScale
        baselineCurrent = current - baseline
        # Find the Peak Current After Baseline Subtraction
        peakIndices = self.linearBaselineFit.findPeakGeneral(potential, baselineCurrent*reductiveScale)
        
        return baseline, baselineCurrent, peakIndices
        
