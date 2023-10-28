
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
    
    def findReductiveScale_CV(self, current, potential):
        # Calculate the first derivative
        samplingFreq = abs(len(potential)/(potential[-1] - potential[0]))
        firstDeriv = scipy.signal.savgol_filter(current, self.convert_to_odd(int(samplingFreq*0.1)), 3, deriv = 1)
        
        # See if the first derivative of the initial points are positive or negative.
        initialScanDeriv = firstDeriv[0:int(samplingFreq*0.1)]
        if len(initialScanDeriv)/2 < (initialScanDeriv > 0).sum():
            return -1
        return 1
    
    def convert_to_odd(self, integer):
        # If the integer is even
        if integer % 2 == 0:
            # Add 1 to make it odd
            return integer + 1
        else:
            # If it's already odd, return it as is
            return integer
    
    def findReductiveScale(self, current):
        # Determine Whether the Data is Oxidative or Reductive
        numNeg = sum(1 for currentVal in current if currentVal < 0)
        reductiveScan = numNeg > len(current)/2
        reductiveScale = -(2*reductiveScan - 1)
        
        return reductiveScale
            
    def useBaselineSubtraction(self, current, potential, polynomialOrder):
        # Check if the data is oxidative or reductive.
        reductiveScale = self.findReductiveScale(current)
        
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
            
    def useLinearFit(self, current, potential):
        # Check if the data is oxidative or reductive.
        reductiveScale = self.findReductiveScale(current)
        
        # Remove the baseline from the data
        baseline = self.linearBaselineFit.findBaseline(potential, current*reductiveScale)*reductiveScale
        baselineCurrent = current - baseline
        # Find the Peak Current After Baseline Subtraction
        peakIndices = self.linearBaselineFit.findPeakGeneral(potential, baselineCurrent*reductiveScale)
        
        return baseline, baselineCurrent, peakIndices
        
