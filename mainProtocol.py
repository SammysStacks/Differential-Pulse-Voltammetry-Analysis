
"""
Need to Install in the Python Enviroment Beforehand:
    pip install -U scipy numpy pandas natsort
    pip install -U pyexcel openpyxl BaselineRemoval
"""

# -------------------------------------------------------------------------- #
# ---------------------------- Imported Modules ---------------------------- #

# General modules
import re
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
    dataDirectory = os.path.dirname(__file__) + "/Data/Example Data/"   # Specify the data folder with the CHI files. Must end with '/'.
    # Specify conditions for reading in files.
    removeFilesContaining = []    # A list of strings that cannot be in any file analyzed.
    analyzeFilesContaining = []   # A list of strings that must be in any file analyzed.

    # Specify the analysis protocol
    useCHIPeaks = False            # Use CHI calculated peaks. The peak information must be in the file.
    useLinearFit = True            # Fit a linear baseline to the peak and subtract off the baseline.
    useBaselineSubtraction = False # Perform iterative polynomial subtraction to find the baseline of the peak. YOU MUST OPTIMIZE 'polynomialOrder'
    
    # Specify information about the potential/current being read in.
    potentialBounds = [-1, 1]   # The [minimum, maximum] potential to consider in this analysis.
    scaleCurrent = 10**6        # You should scale all current as low values are not recorded well.
    yLabel = "Current (uAmps)"  # The units of the Y-Axis values.

    # ---------------------------------------------------------------------- #
    
    # Assert the proper use of the program.
    assert sum((useCHIPeaks, useLinearFit, useBaselineSubtraction)) == 1, "Only one protocol can be be executed."
        
    # Parameters specific to the analysis protocol.
    if useBaselineSubtraction:
        polynomialOrder = 3     # Order of the polynomial fit in baseline subtraction (Extremely important to modify)

    # Specify the Plotting Extent
    plotBaselineSteps = False   # Display the Baseline as Well as the Final Current After Baseline Subtraction
    numSubPlotsX = 3            # The Number of Plots to Display in Each Row

    # ---------------------------------------------------------------------- #
    # ------------------------- Preparation Steps -------------------------- #
    
    # Get file information
    extractData = excelProcessing.processFiles()
    analysisFiles = extractData.getFiles(dataDirectory, removeFilesContaining, analyzeFilesContaining)

    # Create plot for all the curves.
    numSubPlotsX = min(len(analysisFiles), numSubPlotsX)
    plot = dataPlotting.plots(yLabel, dataDirectory, useCHIPeaks, plotBaselineSteps, numSubPlotsX, len(analysisFiles))
    fig, ax = plt.subplots(math.ceil(len(analysisFiles)/numSubPlotsX), numSubPlotsX, sharey=False, sharex = True, figsize=(25, 13))
    fig.tight_layout(pad = 3.0)
    
    # Compile analysis information
    dpvProtocols = dpvAnalysis.dpvProtocols()

    # ---------------------------------------------------------------------- #
    # ------------------------ Start the Analsysis ------------------------- #
    
    data = {}
    # For each file we are analyzing.
    for fileNum in range(len(analysisFiles)):
        analysisFile = analysisFiles[fileNum]
        fileName = os.path.splitext(os.path.basename(analysisFile))[0]

        # ----------------------- Extract the Data --------------------------#
        # Extract the Data/File Information from the File (Potential, Current)
        potential, current, peakPotentialList, peakCurrentList = extractData.getData(analysisFile, dataDirectory, testSheetNum = 0, excelDelimiter = "\t")
        # Scale and Cull the Data
        current = current*scaleCurrent
        if None not in potentialBounds:
            current = current[np.logical_and(potentialBounds[0] <= potential, potential <= potentialBounds[1])]
            potential = potential[np.logical_and(potentialBounds[0] <= potential, potential <= potentialBounds[1])]
        
        # Determine Whether the Data is Oxidative or Reductive
        numNeg = sum(1 for currentVal in current if currentVal < 0)
        reductiveScan = numNeg > len(current)/2
        
        # ---------------------- Get DPV Baseline ---------------------------#
        # Apply a Low Pass Filter
        current = scipy.signal.savgol_filter(current, 7, 3)
        
        # Perform Iterative Polynomial Subtraction
        if useBaselineSubtraction:
            baseline, baselineCurrent, peakIndices = dpvProtocols.useBaselineSubtraction(current, potential, polynomialOrder, reductiveScan)
        # Find Optimal Linear Baseline Under Peak
        elif useLinearFit:
            baseline, baselineCurrent, peakIndices = dpvProtocols.useLinearFit(current, potential, reductiveScan)
        # At This Point, You BETTER be Getting the Peaks from the CHI File 
        elif not useCHIPeaks:
            sys.exit("Please Specify a DPV Peak Detection Mechanism")
        
        # Find the peak information
        peakCurrents = baselineCurrent[peakIndices]
        peakPotentials = potential[peakIndices]
    
        # ----------------- Save and plot DPV Analysis ----------------------#
        
        # Plot the Current Files Results
        plot.plotResults(potential, current, baseline, baselineCurrent, peakCurrents, peakPotentials, fileName)
        # Plot the Combined Full Results Showing Each Step
        plot.plotFullResults(potential, current, baseline, baselineCurrent, peakIndices, peakCurrents, peakPotentials, ax, fileNum, fileName)

        # Save Data in a Dictionary for Plotting Later
        data[fileName] = {}
        data[fileName]["Ip"] = peakCurrents
        data[fileName]["baselineCurrent"] = baselineCurrent
        data[fileName]["potential"] = potential
    
            
# ---------------------------------------------------------------------------#
# --------------------- Plot and Save the Data ------------------------------#

plt.setp(ax, ylim=plot.finalYLim)
plt.title("All Decompositions") # Need this Line as we Change the Title When we Save Subplots
plot.saveSubplot(fig)
plt.show() # Must be the Last Line

sys.exit()



# ---------------------------------------------------------------------------#
# -------------- Specific Plotting Method for This Data ---------------------#
# ----------------- USER SPECIFIC (USER SHOULD EDIT) ------------------------#


outputDirectory = plot.outputDirectory

if not useCHIPeaks:
    fig = plt.figure()
    fig.set_figwidth(7.5)
    fig.set_figheight(5)
    #ax = fig.add_axes([0.1, 0.1, 0.7, 0.9])
    for i,filename in enumerate(sorted(data.keys())):
        
        # Get Peak Current
        baselineCurrent = data[filename]["baselineCurrent"]
        potential = data[filename]["potential"]
        plt.plot(potential, baselineCurrent, label=filename)    
        
    # Plot Curves
    plt.title("DPV Current After Baseline Subtraction")
    plt.xlabel("Potential (V)")
    plt.ylabel(yLabel)
    lgd = plt.legend(loc=9, bbox_to_anchor=(1.29, 1))
    plt.savefig(outputDirectory + "Time Dependant DPV Curve Norepinephrine Full Curve Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
    plt.show()


fig = plt.figure()
#fig.tight_layout(pad=3) #tight margins
fig.set_figwidth(7.5)
fig.set_figheight(5)
legendList = []; Molarity = []; current = []; time = []
#ax = fig.add_axes([0.1, 0.1, 0.7, 0.9])
for i,filename in enumerate(sorted(data.keys())):
    if ' 5 Min' in filename or "50 nM" in filename:
        continue
    
    # Extract Data from Name
    stringDigits = re.findall('\d*\.?\d+', filename) 
    digitsInName = list(map(float, stringDigits))
    if len(digitsInName) == 2:
        concentration = digitsInName[0]
        timePoint = digitsInName[1]
    elif len(digitsInName) == 3:
        concentration = digitsInName[0]
        timePoint = digitsInName[2]
    elif len(digitsInName) == 1:
        concentration = 0
        timePoint = digitsInName[0]
    else:
        print("Found Too Many Numbers in the FileName")
        sys.exit()
    print(filename, timePoint, concentration)
    
    # Get Peak Current
    Ip = data[filename]["Ip"]
    
    if "0 nM" not in filename:
        Ip = 0
    
    
    if 'f 0 min' in filename:
        time = [timePoint]
        current  = [Ip]
        Molarity = [concentration]
    else:
        time.append(timePoint)
        current.append(Ip)
        Molarity.append(concentration)
        
        # Plot Ip
        fileLegend = filename.split("-")[0]
        plt.plot(Molarity, current, 'o', label = fileLegend)
        legendList.append(fileLegend)

linearFitParams = np.polyfit(Molarity, current, 1)
linearFit = np.polyval(linearFitParams, Molarity)
plt.plot(Molarity, linearFit, 'k--', label="Current[uAmp] = " + str(np.round(linearFitParams[0],5)) + "*conc[nM] + " + str(np.round(linearFitParams[1],5)))
    
# Plot Curves
plt.title("Concentration Dependant DPV Peak Current: Dopamine")
plt.xlabel("Concentration (nM)")
plt.ylabel("DPV Peak Current (uAmps)")
lgd = plt.legend(loc=9, bbox_to_anchor=(1.2, 1))
plt.savefig(outputDirectory + "Concentration Dependant DPV Curve Dopamine no 50nM.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
plt.show()


fig = plt.figure()
#fig.tight_layout(pad=3) #tight margins
fig.set_figwidth(7.5)
fig.set_figheight(5)
legendList = []
#ax = fig.add_axes([0.1, 0.1, 0.7, 0.9])
for i,filename in enumerate(sorted(data.keys())):
    # Extract Data from Name
    stringDigits = re.findall('\d*\.?\d+', filename)
    digitsInName = list(map(float, stringDigits))
    if len(digitsInName) == 2:
        concentration = digitsInName[0]
        timePoint = digitsInName[1]
    elif len(digitsInName) == 3:
        concentration = digitsInName[0]
        timePoint = digitsInName[2]
    elif len(digitsInName) == 1:
        concentration = 0
        timePoint = digitsInName[0]
    else:
        print("Found Too Many Numbers in the FileName")
        sys.exit
    print(filename, timePoint, concentration)
    
    # Get Peak Current
    Ip = data[filename]["Ip"]
    
    
    if ' 0 min' in filename:
        time = [timePoint]
        current  = [Ip]
        Molarity = [concentration]
    else:
        time.append(timePoint)
        current.append(Ip)
        Molarity.append(concentration)
        
        # Plot Ip
        fileLegend = filename.split("-")[0]
        plt.plot(time, current, 'o-', label = fileLegend)
        legendList.append(fileLegend)
    
    
# Plot Curves
plt.title("Time Dependant DPV Peak Current: Norepinephrine")
plt.xlabel("Time (minutes)")
plt.ylabel("DPV Peak Current (uAmps)")
lgd = plt.legend(loc=9, bbox_to_anchor=(1.2, 1))
plt.savefig(outputDirectory + "Time Dependant DPV Curve Norepinephrine Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
plt.show()




