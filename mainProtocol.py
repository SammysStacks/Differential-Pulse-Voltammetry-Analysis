
"""
Need to Install in the Python Enviroment Beforehand:
    pip install -U scipy numpy pandas natsort
    pip install -U pyexcel openpyxl BaselineRemoval
"""

# -------------------------------------------------------------------------- #
# ---------------------------- Imported Modules ---------------------------- #

# General modules
import os
import sys
import math
import scipy
import numpy as np
# Plotting modules
import matplotlib.pyplot as plt

# Import data processing files
sys.path.append(os.path.dirname(__file__) + "/Helper Files/")
import excelProcessing
import dataPlotting

# Import analysis files
sys.path.append(os.path.dirname(__file__) + "/Helper Files/Biolectric Protocols/")
import dpvAnalysis

if __name__ == "__main__":
    # ---------------------------------------------------------------------- #
    #    User Parameters to Edit (More Complex Edits are Inside the Files)   #
    # ---------------------------------------------------------------------- #
    
    # Input data information
    dataDirectory = os.path.dirname(__file__) + "/Data/_testMultiChannelSWV/"   # Specify the data folder with the CHI files. Must end with '/'.
    # Specify conditions for reading in files.
    removeFilesContaining = []    # A list of strings that cannot be in any file analyzed.
    analyzeFilesContaining = []   # A list of strings that must be in any file analyzed.

    # Specify the analysis protocol
    useCHIPeaks = False             # DEPRECATED (ASK SAM FOR USE). Use CHI calculated peaks. The peak information must be in the file.
    useLinearFit = True             # Fit a linear baseline to the peak and subtract off the baseline.
    useBaselineSubtraction = False  # Perform iterative polynomial subtraction to find the baseline of the peak. YOU MUST OPTIMIZE 'polynomialOrder'
    
    # Specify information about the potential/current being read in.
    potentialBounds = [None, None]  # The [minimum, maximum] potential to consider in this analysis.
    scaleCurrent = 10**6            # THIS SHOULD SCALE THE CURRENT TO uAMPS! You should scale all current as low values are not recorded well.

    # ---------------------------------------------------------------------- #
    
    # Assert the proper use of the program.
    assert sum((useCHIPeaks, useLinearFit, useBaselineSubtraction)) == 1, "Only one protocol can be be executed."
        
    # Parameters specific to the analysis protocol.
    if useBaselineSubtraction:
        polynomialOrder = 3     # Order of the polynomial fit in baseline subtraction (Extremely important to modify)

    # Specify the Plotting Extent
    numSubPlotsX = 3  # The Number of Plots to Display in Each Row

    # ---------------------------------------------------------------------- #
    # ------------------------- Preparation Steps -------------------------- #
    
    # Get file information
    extractData = excelProcessing.processFiles()
    saveAnalysisResults = excelProcessing.saveExcelData()
    analysisFiles = extractData.getFiles(dataDirectory, removeFilesContaining, analyzeFilesContaining)
    # Compile all the data from the files.
    allPotential, allCurrent, allPeakPotentials, allPeakCurrents, fileNames = extractData.getAllData(analysisFiles, dataDirectory, testSheetNum = 0, excelDelimiter = ",")
    
    # Create plot for all the curves.
    numSubPlotsX = min(len(fileNames), numSubPlotsX)
    plot = dataPlotting.plots(dataDirectory, useCHIPeaks, numSubPlotsX, len(fileNames))
    fig, ax = plt.subplots(math.ceil(len(fileNames)/numSubPlotsX), numSubPlotsX, sharey=False, sharex = True, figsize=(25, 13))
    fig.tight_layout(pad = 3.0)
    
    # Compile analysis information
    dpvProtocols = dpvAnalysis.dpvProtocols()
    
    # ---------------------------------------------------------------------- #
    # ------------------------ Start the Analsysis ------------------------- #
    
    peakInfo = []
    analysisInfo = []
    # For each file we are analyzing.
    for dpvInd in range(len(allPotential)):
        # Extract all the DPV information from the trial.
        peakPotentials, peakCurrents = allPeakPotentials[dpvInd], allPeakCurrents[dpvInd]
        potential, unfilteredCurrent = allPotential[dpvInd], allCurrent[dpvInd]
        fileName = fileNames[dpvInd]      
          
        print(f"\nAnalyzing Data in {fileName}")
        # ----------------------- Data Preprocessing ----------------------- #
        # Scale and Cull the Data
        unfilteredCurrent = unfilteredCurrent*scaleCurrent
        # Only consider data within the provided bounds. If no bounds provided, use all the data.
        unfilteredCurrent = unfilteredCurrent[np.logical_and((potentialBounds[0] or -np.inf) <= potential, potential <= (potentialBounds[1] or np.inf))]
        potential = potential[np.logical_and((potentialBounds[0] or -np.inf) <= potential, potential <= (potentialBounds[1] or np.inf))]
        
        # ------------------------ Get DPV Baseline ------------------------ #
        # Apply a Low Pass Filter
        current = scipy.signal.savgol_filter(unfilteredCurrent, 7, 3)
        
        # Perform Iterative Polynomial Subtraction
        if useBaselineSubtraction:
            baselineCurrent, baselineSubtractedCurrent, peakIndices = dpvProtocols.useBaselineSubtraction(current, potential, polynomialOrder)
        # Find Optimal Linear Baseline Under Peak
        elif useLinearFit:
            baselineCurrent, baselineSubtractedCurrent, peakIndices = dpvProtocols.useLinearFit(current, potential)
        # At This Point, You BETTER be Getting the Peaks from the CHI File 
        elif not useCHIPeaks:
            sys.exit("Please Specify a DPV Peak Detection Mechanism")
        
        # Find the peak information
        if not useCHIPeaks:
            peakCurrents = baselineSubtractedCurrent[peakIndices]
            peakPotentials = potential[peakIndices]
    
        # ----------------- Save and plot DPV Analysis ----------------------#
        
        # Plot the results
        plot.plotResults(potential, current, baselineCurrent, baselineSubtractedCurrent, peakIndices, peakCurrents, peakPotentials, ax, dpvInd, fileName)

        # Store the data in case user wants.
        analysisInfo.append([potential, unfilteredCurrent, current, baselineCurrent, baselineSubtractedCurrent])
        peakInfo.append([peakPotentials, peakCurrents])
        
        # Save the analysis.
        saveExcelPath = dataDirectory + "DPV Analysis/Analysis Files/" + fileName + ".xlsx"
        saveAnalysisResults.saveDataDPV(potential, current, baselineCurrent, baselineSubtractedCurrent, peakCurrents, peakPotentials, saveExcelPath)
            
# ---------------------------------------------------------------------------#
# --------------------- Plot and Save the Data ------------------------------#

# Assert the integrity of data analysis.
assert len(peakInfo) == len(analysisInfo)

# Plot and save all the analysis in one figure.
plt.setp(ax, ylim=plot.finalYLim)
plt.title("All Decompositions") # Need this Line as we Change the Title When we Save Subplots
plot.saveSubplot(fig)
plt.show() # Must be the Last Line

try:
    # Make an ndarray out of the analysis information.
    analysisInfo = np.array(analysisInfo, dtype=object)
    # If they all share a common potential.
    if np.all(np.equal(analysisInfo[:,0], analysisInfo[:, 0][0])):
        # Plot the compiled analysis.
        if len(peakInfo) < 30:
            plot.plotCompiledResults(analysisInfo, peakInfo, fileNames)

        # Save single excel document with all the information.
        saveExcelPath = dataDirectory + "DPV Analysis/Analysis Files/compiledAnalysis.xlsx"
        saveAnalysisResults.saveAllData(analysisInfo, peakInfo, saveExcelPath)
except:
    pass


