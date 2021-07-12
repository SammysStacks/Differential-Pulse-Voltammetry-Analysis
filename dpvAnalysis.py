
"""
Need to Install in the Python Enviroment Beforehand:
    $ conda install openpyxl
    $ conda install scipy
    $ pip install natsort
    $ pip install pyexcel
    $ pip install BaselineRemoval
"""

# -------------------------------------------------------------------------- #
# ------------------------- Imported Modules ---------------------------------#

# Import Basic Modules
import re
import os
import sys
import math
import numpy as np
# Module to Sort Files in Order
from natsort import natsorted
# Modules to Plot
import matplotlib.pyplot as plt

# Import Python Helper Files
sys.path.append('./Helper Files/')  # Folder with All the Helper Files
import excelProcessing
import dataPlotting
import calculateBaseline

from scipy.interpolate import UnivariateSpline
import scipy.signal

if __name__ == "__main__":
    # ---------------------------------------------------------------------- #
    #    User Parameters to Edit (More Complex Edits are Inside the Files)   #
    # ---------------------------------------------------------------------- #

    # Specify Where the Files are Located
    dataDirectory = "./Input Data/Test 2/"   # The Path to the CHI Data; Must End With '/'
    outputDirectory = "./Output Data/Test 2/"   # The Path to Output Folder (For Plots); Must End With '/'
    
    # Specify Which Files to Read In
    useAllFolderFiles = True # Read in All TXT/CSV/EXCEL Files in the dataDirectory
    if useAllFolderFiles:
        # Specify Which Files You Want to Read
        fileDoesntContain = "Round 11"
        fileContains = ""
    else:
        # Else, Specify the File Names
        dpvFiles = ['New PB Heat 100C (1).csv']
        
    # Specify How You Want to Analyze the DPV Curve (First Variable Listed as True Will be Executed)
    useCHIPeaks = False            # Use CHI's Predicted Peak Values (The Information Must be in the TXT/CSV/Excel)
    useBaselineSubtraction = False # Perform Iterative Polynomial Fit to Find the Baseline and peak Current
    useLinearFit = True            # Fit a Linear Baseline under the Peak to Find the Peak Current
    
    # Parameters Specific for Each DPV Analysis Algorythm
    if useBaselineSubtraction:
        polynomialOrder = 2  # Order of the Polynomial Fit in Baseline Subtraction (Extremely Important to Modify)
    
    # Cut Off Data From the DPV Graph
    minPotentialCut = -0.1   # The Minimum Potential to Display (If Potential is Greater Than or Equal, Keep the Data)
    maxPotentialCut = 0.5    # The Maximum Potential to Display (If Potential is Less Than or Equal, Keep the Data)
    
    # Specify the Plotting Extent
    plotBaselineSteps = False # Display the Baseline as Well as the Final Current After Baseline Subtraction
    # Specify Figure Asthetics
    numSubPlotsX = 2  # The Number of Plots to Display in Each Row
    figWidth = 25     # The Figure Width
    figHeight = 13    # The Figure Height
    # Specify Current Units
    scaleCurrent = 10**6        # Scale the Current (Y-Axis)
    yLabel = "Current (uAmps)"  # Y-Axis (The Current) Units
    
    # ---------------------------------------------------------------------- #
    # ------------------------- Preparation Steps -------------------------- #
    
    # Get File Information
    extractData = excelProcessing.processFiles()
    if useAllFolderFiles:
        dpvFiles = extractData.getFiles(dataDirectory, fileDoesntContain, fileContains)
    # Sort Files
    dpvFiles = natsorted(dpvFiles)
    # Create Output Folder if the One Given Does Not Exist
    os.makedirs(outputDirectory, exist_ok = True)

    # Create One Plot with All the DPV Curves
    plot = dataPlotting.plots(yLabel, outputDirectory, useCHIPeaks, plotBaselineSteps, numSubPlotsX, len(dpvFiles))
    numSubPlotsX = min(len(dpvFiles), numSubPlotsX)
    fig, ax = plt.subplots(math.ceil(len(dpvFiles)/numSubPlotsX), numSubPlotsX, sharey=False, sharex = True, figsize=(figWidth,figHeight))
    fig.tight_layout(pad=3.0)
    data = {}  # Store Results ina Dictionary for Later Analaysis
    
    # ---------------------------------------------------------------------- #
    # ----------------------------- DPV Program ---------------------------- #
    
    # For Each Data File, Extract the Important Data and Plot
    for fileNum, currentFile in enumerate(sorted(dpvFiles)):
        
        # ----------------------- Extract the Data --------------------------#
        # Extract the Data/File Information from the File (Potential, Current)
        dataFile = dataDirectory + currentFile
        fileName = os.path.splitext(currentFile)[0]
        potential, current, peakPotentialList, peakCurrentList = extractData.getData(dataFile, outputDirectory, testSheetNum = 0, excelDelimiter = ",")
        # Scale and Cull the Data
        current = current*scaleCurrent
        current = current[np.logical_and(minPotentialCut <= potential, potential <= maxPotentialCut)]
        potential = potential[np.logical_and(minPotentialCut <= potential, potential <= maxPotentialCut)]
        
        # Determine Whether the Data is Oxidative or Reductive
        numNeg = sum(1 for currentVal in current if currentVal < 0)
        reductiveScan = numNeg > len(current)/2
        
        # ---------------------- Get DPV Baseline ---------------------------#
        # Perform Iterative Polynomial Subtraction
        if useBaselineSubtraction:
            # Get Baseline from Iterative Polynomial Subtraction
            polynomialBaselineFit = calculateBaseline.polynomialBaselineFit()
            baseline = polynomialBaselineFit.baselineSubtractionAPI(current, polynomialOrder, reductiveScan)
            # Find Current After Baseline Subtraction
            baselineCurrent = current - baseline
            
            smoothCurrent = UnivariateSpline(potential, baselineCurrent, s=0.001, k=5)
            smoothCurrentPeaks = scipy.signal.find_peaks(smoothCurrent.derivative(n=1)(potential), prominence=10E-10)
            
            if len(smoothCurrentPeaks[0]) > 0:
                bestPeak = smoothCurrentPeaks[1]['prominences'].argmax()
                peakInd = smoothCurrentPeaks[0][bestPeak]
                
                Ip = baselineCurrent[peakInd]
                Vp = potential[peakInd]
            else:
                Ip = 0; Vp = 0; peakInd = 0;
        # Find Optimal Linear Baseline Under Peak
        elif useLinearFit:
            # Get Baseline from Iterative Polynomial Subtraction
            linearBaselineFit = calculateBaseline.bestLinearFit(potential, current)
            baseline = linearBaselineFit.findLinearBaseline(reductiveScan)
            # Find Current After Baseline Subtraction
            baselineCurrent = current - baseline
            # Find the Peak Current After Baseline Subtraction
            peakInd = abs(baselineCurrent).argmax()
            Ip = baselineCurrent[peakInd]
            Vp = potential[peakInd]
        # At This Point, You BETTER be Getting the Peaks from the CHI File 
        elif not useCHIPeaks:
            print("Please Specify a DPV Peak Detection Mechanism")
            sys.exit()
    
        # ----------------- Save and plot DPV Analysis ----------------------#
        
        # Plot the Current Files Results
        plot.plotResults(potential, current, baseline, baselineCurrent, peakInd, Ip, Vp, fileName)
        # Plot the Combined Full Results Showing Each Step
        plot.plotFullResults(potential, current, baseline, baselineCurrent, peakInd, Ip, Vp, ax, fileNum, fileName)

        # Save Data in a Dictionary for Plotting Later
        data[fileName] = {}
        data[fileName]["Ip"] = Ip
        data[fileName]["baselineCurrent"] = baselineCurrent
        data[fileName]["potential"] = potential
    
            
# ---------------------------------------------------------------------------#
# --------------------- Plot and Save the Data ------------------------------#

plot.saveSubplot(fig)
plt.title(fileName+ " DPV Graph") # Need this Line as we Change the Title When we Save Subplots
plt.show() # Must be the Last Line


# ---------------------------------------------------------------------------#
# -------------- Specific Plotting Method for This Data ---------------------#
# ----------------- USER SPECIFIC (USER SHOULD EDIT) ------------------------#


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
    if ' 0 min' in filename:
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
        plt.plot(Molarity, current, 'o-', label = fileLegend)
        legendList.append(fileLegend)
    
    
# Plot Curves
plt.title("Concentration Dependant DPV Peak Current: Norepinephrine")
plt.xlabel("Concentration (nM)")
plt.ylabel("DPV Peak Current (uAmps)")
lgd = plt.legend(loc=9, bbox_to_anchor=(1.2, 1))
plt.savefig(outputDirectory + "Concentration Dependant DPV Curve Norepinephrine Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
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





