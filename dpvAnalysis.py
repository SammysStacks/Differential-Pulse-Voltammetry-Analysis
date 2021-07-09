
"""
Need to Install on the Anaconda Prompt:
    $ conda install openpyxl
    $ conda install seaborn
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
# Modules for Peak Analysis
from scipy.signal import argrelextrema
# Baseline Subtraction
from BaselineRemoval import BaselineRemoval
# Modules to Plot
import matplotlib.pyplot as plt

# Import Python Helper Files
sys.path.append('./Helper Files/')  # Folder with All the Helper Files
import excelProcessing
import dataPlotting
#import polynomialBaselineFit


if __name__ == "__main__":
    # ---------------------------------------------------------------------- #
    #    User Parameters to Edit (More Complex Edits are Inside the Files)   #
    # ---------------------------------------------------------------------- #

    # Specify Where the Files are Located
    dataDirectory = "./Input Data/Concentration Analysis/"   # The Path to the CHI Data; Must End With '/'
    outputDirectory = "./Output Data/Concentration Analysis/"   # The Path to Output Folder (For Plots); Must End With '/'
    
    # Specify Which Files to Read In
    useAllFiles = True # Read in All TXT/CSV/EXCEL Files in the dataDirectory
    if useAllFiles:
        # Specify Which Files You Want to Read
        fileDoesntContain = "Round 11"
        fileContains = "Round 1"
    else:
        # Else, Specify the File Names
        dpvFiles = ['New PB Heat 100C (1).csv']
        
    # Specify How You Want to Analyze the DPV Curve (First Variable Listed as True Will be Executed)
    useCHIPeaks = False            # Use CHI's Predicted Peak Values (The Information Must be in the TXT/CSV/Excel)
    useBaselineSubtraction = True # Perform Iterative Polynomial Fit to Find the Baseline and peak Current
    useLinearFit = True            # Fit a Linear Baseline under the Peak to Find the Peak Current
    
    # Parameters Specific for Each DPV Analysis Algorythm
    if useBaselineSubtraction:
        order = 1  # Order of the Polynomial Fit in Baseline Subtraction (Extremely Important to Modify)
    
    # Specify Figure Asthetics
    numSubPlotsX = 2  # The Number of Plots to Display in Each Row
    figWidth = 25     # The Figure Width
    figHeight = 13    # The Figure Height
    # Specify Current Units
    scaleCurrent = 10**6        # Scale the Current (Y-Axis)
    yLabel = "Current (uAmps)"  # Y-Axis (The Current) Units
    
    # Cut Off Data From the DPV Graph
    minPotentialCut = -0.1   # The Minimum Potential to Display (If Potential is Greater Than or Equal, Keep the Data)
    maxPotentialCut = 0.5    # The Maximum Potential to Display (If Potential is Less Than or Equal, Keep the Data)
    
    plotBaselineSteps = False # Display the Baseline as Well as the Final Current After Baseline Subtraction

    # ---------------------------------------------------------------------- #
    # ------------------------- Preparation Steps -------------------------- #
    
    # Get File Information
    extractData = excelProcessing.processFiles()
    if useAllFiles:
        dpvFiles = extractData.getFiles(dataDirectory, fileDoesntContain, fileContains)
    # Sort Files
    dpvFiles = natsorted(dpvFiles)
    # Create Output Folder if the One Given Does Not Exist
    os.makedirs(outputDirectory, exist_ok = True)

    # Create One Plot with All the DPV Curves
    plot = dataPlotting.plots(yLabel, outputDirectory)
    fig, ax = plt.subplots(math.ceil(len(dpvFiles)/numSubPlotsX), numSubPlotsX, sharey=False, sharex = True, figsize=(figWidth,figHeight))
    fig.tight_layout(pad=3.0)
    data = {}  # Store Results ina Dictionary for Later Analaysis
    
    # ---------------------------------------------------------------------- #
    # ----------------------------- DPV Program ---------------------------- #
    
    # For Each Data File, Extract the Important Data and Plot
    for fileNum, currentFile in enumerate(sorted(dpvFiles)):
        
        # Extract the Data/File Information from the File (Potential, Current)
        dataFile = dataDirectory + currentFile
        fileName = os.path.splitext(currentFile)[0]
        potential, current, peakPotentialList, peakCurrentList = extractData.getData(dataFile, outputDirectory, testSheetNum = 0, excelDelimiter = ",")
        # Scale and Cull the Data
        current = current*scaleCurrent
        current = current[np.logical_and(minPotentialCut <= potential, potential <= maxPotentialCut)]
        potential = potential[np.logical_and(minPotentialCut <= potential, potential <= maxPotentialCut)]
        # Plot the Initial Data
        fig1 = plt.figure(2+fileNum) # Leaving 2 Figures Free for Other plots
        plt.plot(potential, current, label="True Data: " + fileName, color='C0')
        
        # Determine Whether the Data is Oxidative or Reductive
        numNeg = sum(1 for currentVal in current if currentVal < 0)
        reductiveScan = numNeg > len(current)/2
        
        # If We use the CHI Peaks, Skip Peak Detection
        if useCHIPeaks:
            # Set Axes Limits
            axisLimits = [min(current) - min(current)/10, max(current) + max(current)/10]
        # Perform Iterative Baseline Subtraction
        elif useBaselineSubtraction:
            # Get Baseline Depending on Ox/Red Curve
            if reductiveScan:
                baseObj = BaselineRemoval(-current)
                baseline = current + baseObj.ModPoly(order)
            else:
                baseObj = BaselineRemoval(current)
                baseline = current - baseObj.ModPoly(order)
            # Find Current After Baseline Subtraction
            baselineCurrent = current - baseline
        # Find Linear Baseline   
        elif useLinearFit:
            a = 1
        else:
            print("Please Specify a DPV Peak Detection Mechanism")
        
        if not useCHIPeaks:

            # Plot Subtracted baseline
            plt.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            plt.plot(potential, baseline, label="Baseline Current", color='C1')  
            
            # Find Where Data Begins to Deviate from the Edges
            minimums = argrelextrema(baselineCurrent, np.less)[0]
            maximums = argrelextrema(baselineCurrent, np.greater)[0]
            stopInitial = min(minimums[0], maximums[0]) + 10
            stopFinal = max(minimums[-1], maximums[0]) - 10
            
            # Get the Peak Current (Max Differenc between the Data and the Baseline)
            if stopInitial <= stopFinal:
                if reductiveScan:
                    IpIndex = np.argmin(baselineCurrent[stopInitial:stopFinal+1])
                else:
                    IpIndex = np.argmax(baselineCurrent[stopInitial:stopFinal+1])
                Ip = baselineCurrent[stopInitial+IpIndex]
                Vp = potential[stopInitial+IpIndex]
            else:
                Ip = 0; IpIndex = 0
                Vp = 0
        
            # Plot the Peak Current (Verticle Line) for Visualization
            axisLimits = [min(*baselineCurrent,*current,*baseline), max(*baselineCurrent,*current,*baseline)]
            axisLimits[0] -= (axisLimits[1] - axisLimits[0])/10
            axisLimits[1] += (axisLimits[1] - axisLimits[0])/10
            plt.axvline(x=Vp, ymin=plot.normalize(baseline[stopInitial+IpIndex], axisLimits[0], axisLimits[1]), ymax=plot.normalize(float(Ip + baseline[stopInitial+IpIndex]), axisLimits[0], axisLimits[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
    
        # Save Figure
        plot.saveplot(fig1, axisLimits, fileName)
        
        # Keep Running Subplots Order
        if numSubPlotsX == 1 and len(dpvFiles) == 1:
            currentAxes = ax
        elif numSubPlotsX == 1:
            currentAxes = ax[fileNum]
        elif numSubPlotsX == len(dpvFiles):
            currentAxes = ax[fileNum]
        elif numSubPlotsX > 1:
            currentAxes = ax[fileNum//numSubPlotsX][fileNum%numSubPlotsX]
        else:
            print("numSubPlotsX CANNOT be < 1. Currently it is: ", numSubPlotsX)
            exit
        
        # Plot Data in Subplots
        if useCHIPeaks and Ip != None and Vp != None:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            currentAxes.axvline(x=Vp, ymin=plot.normalize(max(current) - Ip, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=plot.normalize(max(current), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
            currentAxes.legend(loc='upper left')  
        elif not plotBaselineSteps:
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C1')
            currentAxes.axvline(x=Vp, ymin=plot.normalize(0, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=plot.normalize(float(Ip), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
            currentAxes.axhline(y = 0, color='r', linestyle='--')
            currentAxes.legend(loc='upper left')  
        else:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            currentAxes.plot(potential, baseline, label="Baseline Current", color='C1')  
            currentAxes.axvline(x=Vp, ymin=plot.normalize(baseline[stopInitial+IpIndex], currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=plot.normalize(float(Ip+baseline[stopInitial+IpIndex]), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
            currentAxes.legend(loc='best')  
    
        currentAxes.set_xlabel("Potential (V)")
        currentAxes.set_ylabel(yLabel)
        currentAxes.set_title(fileName)
        
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
    fig = plt.figure(0)
    #fig.tight_layout(pad=3) #tight margins
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






#sys.exit()

fig = plt.figure(1)
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


fig = plt.figure(2)
#fig.tight_layout(pad=3) #tight margins
fig.set_figwidth(7.5)
fig.set_figheight(5)
legendList = []
#ax = fig.add_axes([0.1, 0.1, 0.7, 0.9])
for i,filename in enumerate(sorted(data.keys())):
    # Extract Data from Name
    stringDigits = re.findall(r'\d+', filename) 
    digitsInName = list(map(int, stringDigits))
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
        exit
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






"""
Deleted Code:
    
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
    """
    