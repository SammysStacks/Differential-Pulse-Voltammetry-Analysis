
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
from natsort import natsorted

# Baseline Subtraction
from BaselineRemoval import BaselineRemoval




# ---------------------------------------------------------------------------#
# --------------------- Specify/Find File Names -----------------------------#

def txt2csv(txtFile, csvFile):
    # Check to see if csv conversion alreayd happened
    if not os.path.isfile(csvFile):
        # # IF it does ask the user if they want to overwrite it
        # overwrite = input("File already exists. Type 'y' to overwrite (else anything):   ")
        # if overwrite.lower() != 'y':
        #     sys.exit("Code Was Stopped Because Original File Was Going to Be Overwritten")
        with open(txtFile, "r") as in_text:
            in_reader = csv.reader(in_text, delimiter = ',')
            with open(csvFile, 'w', newline='') as out_csv:
                out_writer = csv.writer(out_csv)
                for row in in_reader:
                    out_writer.writerow(row)
    else:
        print("You already renamed the '.txt' to 'csv'")

# If Using All the CSV Files in the Folder
if use_All_CSV_Files:
    dpvFiles = []
    for file in os.listdir(data_Directory):
        if file.endswith(".txt") and thatDoesntContain not in file and thatContains in file and file not in dpvFiles:
            base = os.path.splitext(file)[0]
            csvFile = data_Directory + base + ".csv"
            txt2csv(data_Directory + file, csvFile)
            dpvFiles.append(base + ".csv")
        elif file.endswith(".csv") and thatDoesntContain not in file and thatContains in file and file not in dpvFiles:
            dpvFiles.append(file)
    if len(dpvFiles) == 0:
        print("No CSV Files Found in the Data Folder:", data_Directory)
        sys.exit()
    
    # Specify Which Files to Ignore
    ignoreFiles = []

# Else Specify Which Files You Want to use
else:
    dpvFiles = [
         'New PB Heat 100C (1).csv',
         ]
    
    # Check to see if the Inputed CSV Files Exist
    for CV_CSV_Data in dpvFiles:    
        if not os.path.isfile(data_Directory + CV_CSV_Data):
            print("The File ", data_Directory + CV_CSV_Data," Mentioned Does NOT Exist")
            sys.exit()
        
    # Not Ignoring Any Files
    ignoreFiles = []

# Sort Files
natsorted(dpvFiles)
# Create Output Folder if the One Given Does Not Exist
outputData = data_Directory +  "Peak_Current_Plots/"
os.makedirs(outputData, exist_ok = True)

# ---------------------- User Does NOT Have to Edit -------------------------#
# ---------------------------------------------------------------------------#
# ---------------------------------------------------------------------------#
# ----------------------------- Functions -----------------------------------#




    

def getBase(potential, currentReal, Iterations, order):
    current = currentReal.copy()
    for _ in range(Iterations):
        fitI = np.polyfit(potential, current, order)
        baseline = np.polyval(fitI, potential)
        for i in range(len(current)):
            if current[i] > baseline[i]:
                current[i] = baseline[i]
    return baseline


        

# ---------------------------------------------------------------------------#
# -------------------- Extract and Plot the Ip Data -------------------------#

# Create One Plot with All the DPV Curves
fig, ax = plt.subplots(math.ceil(len(dpvFiles)/numSubPlotsX), numSubPlotsX, sharey=False, sharex = True, figsize=(figWidth,figHeight))
fig.tight_layout(pad=3.0)
data = {}  # Store Results ina Dictionary for Later Analaysis
# For Each CSV File, Extract the Important Data and Plot
for figNum, CV_CSV_Data in enumerate(sorted(dpvFiles)):
    if CV_CSV_Data in ignoreFiles:
        continue
    
    # ----------------- Convert Data to Excel Format ------------------------#
    
    # Rename the File with an Excel Extension
    base = os.path.splitext(CV_CSV_Data)[0]
    excel_file = data_Directory + base + ".xlsx"
    # If the File is Not Already Converted: Convert
    if not os.path.isfile(excel_file) or True:
        # Make Excel WorkBook
        wb = xl.Workbook()
        ws = wb.active
        # Write to Excel WorkBook
        with open(data_Directory + CV_CSV_Data) as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                ws.append(row)
        # Save as New Excel File
        wb.save(excel_file)
    else:
        print("You already renamed the '.csv' to '.xlsx'")
    
    # Load Data from New Excel File
    WB = xl.load_workbook(excel_file) 
    WB_worksheets = WB.worksheets
    Main = WB_worksheets[0]
        
    # -----------------------------------------------------------------------#
    # ----------------------- Extract Run Info ------------------------------#
    
    # Set Initial Variables from last Run to Zero
    deltaV = None; endVolt = None; initialVolt = None; Vp = None; Ip = None; IpList = []
    # Loop Through the Info Section and Extract the Needxed Run Info from Excel
    for cell in Main['A']:
        # Get Cell Value
        cellVal = cell.value
        if cellVal == None:
            continue
        
        # Find the deltaV for Each Step (Volts)
        if cellVal.startswith("Incr E (V) = "):
            deltaV = float(cellVal.split(" = ")[-1])
        # Find the Final Voltage
        elif cellVal.startswith("Final E (V) = "):
            endVolt = float(cellVal.split(" = ")[-1])
        # Find the Initial Voltage
        elif cellVal.startswith("Init E (V) = "):
            initialVolt = float(cellVal.split(" = ")[-1])
        # If Peak Found by CHI, Get Peak Potential
        elif cellVal.startswith("Ep = "):
            Vp = float(cellVal.split(" = ")[-1][:-1])
        # If Peak Found by CHI, Get Peak Current
        elif cellVal.startswith("ip = "):
            IpCurrent = float(cellVal.split(" = ")[-1][:-1])
            IpList.append(IpCurrent)
            Ip = max(IpList)  # Assuming Strongest Peak is the True Peak
        elif cellVal == "Potential/V":
            startDataRow = cell.row + 2
            break
    # Find the X Axis Width
    xRange = (endVolt - initialVolt)
    # Find Point/Scan
    pointsPerScan = int(xRange/deltaV)
    # -----------------------------------------------------------------------#
    # -------------------- Find Ip Data and Plot ----------------------------#
    
    # Get Potential, Current Data from Excel
    potential = []
    current = []
    baselineCurrent = []; baseline = []
    for cell in Main['A'][startDataRow - 1 + initialCut:]:
        # Break out of Loop if no More Data (edge effect if someone edits excel)
        if cell.value == None:
            break
        # Find the Potential and Current Data points
        row = cell.row - 1
        potential.append(float(cell.value))
        current.append(float(Main['B'][row].value))
    current = np.array(current[:-finalCut])*scaleCurrent
    potential = np.array(potential[:-finalCut])
    
    numNeg = sum(1 for currentVal in current if currentVal < 0)
    backwardScan = numNeg > len(current)/2
        
    # Plot the Initial Data
    fig1 = plt.figure(2+figNum) # Leaving 2 Figures Free for Other plots
    plt.plot(potential, current, label="True Data: " + base, color='C0')
    
    
    
    # If We use the CHI Peaks, Skip Peak Detection
    if useCHIPeaks and Ip != None and Vp != None:
        # Set Axes Limits
        axisLimits = [min(current) - min(current)/10, max(current) + max(current)/10]
        
    # Else, Perform baseline Subtraction to Find the peak
    else:
        # Get Baseline
        if backwardScan:
            if useAPI:
                baseObj = BaselineRemoval(-current)
                baseline = current + baseObj.ModPoly(order)
            else:
                baseline = - getBase(potential, -current, Iterations, order)
        else:
            if useAPI:
                baseObj = BaselineRemoval(current)
                baseline = current - baseObj.ModPoly(order)
            else:
                baseline = getBase(potential, current, Iterations, order)
        baselineCurrent = current - baseline
        
        # Plot Subtracted baseline
        plt.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
        plt.plot(potential, baseline, label="Baseline Current", color='C1')  
        
        # Find Where Data Begins to Deviate from the Edges
        minimums = argrelextrema(baselineCurrent, np.less)[0]
        maximums = argrelextrema(baselineCurrent, np.greater)[0]
        stopInitial = min(minimums[0], maximums[0]) + 25
        stopFinal = max(minimums[-1], maximums[0]) - 25
        
        # Get the Peak Current (Max Differenc between the Data and the Baseline)
        if stopInitial <= stopFinal:
            if backwardScan:
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
        plt.axvline(x=Vp, ymin=normalize(baseline[stopInitial+IpIndex], axisLimits[0], axisLimits[1]), ymax=normalize(float(Ip + baseline[stopInitial+IpIndex]), axisLimits[0], axisLimits[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
    
    # Save Figure
    saveplot(fig1, axisLimits, base, outputData)
    
    # Keep Running Subplots Order
    if numSubPlotsX == 1 and len(dpvFiles) == 1:
        currentAxes = ax
    elif numSubPlotsX == 1:
        currentAxes = ax[figNum]
    elif numSubPlotsX == len(dpvFiles):
        currentAxes = ax[figNum]
    elif numSubPlotsX > 1:
        currentAxes = ax[figNum//numSubPlotsX][figNum%numSubPlotsX]
    else:
        print("numSubPlotsX CANNOT be < 1. Currently it is: ", numSubPlotsX)
        exit
    
    # Plot Data in Subplots
    if useCHIPeaks and Ip != None and Vp != None:
        currentAxes.plot(potential, current, label="True Data: " + base, color='C0')
        currentAxes.axvline(x=Vp, ymin=normalize(max(current) - Ip, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=normalize(max(current), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
        currentAxes.legend(loc='upper left')  
    elif displayOnlyBaselineSubtraction:
        currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C1')
        currentAxes.axvline(x=Vp, ymin=normalize(0, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=normalize(float(Ip), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
        currentAxes.axhline(y = 0, color='r', linestyle='--')
        currentAxes.legend(loc='upper left')  
    else:
        currentAxes.plot(potential, current, label="True Data: " + base, color='C0')
        currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
        currentAxes.plot(potential, baseline, label="Baseline Current", color='C1')  
        currentAxes.axvline(x=Vp, ymin=normalize(baseline[stopInitial+IpIndex], currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=normalize(float(Ip+baseline[stopInitial+IpIndex]), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='r', label="Peak Current: " + "%.4g"%Ip)
        currentAxes.legend(loc='best')  

    currentAxes.set_xlabel("Potential (V)")
    currentAxes.set_ylabel(yLabel)
    currentAxes.set_title(base)
    
    # Save Data in a Dictionary for Plotting Later
    data[base] = {}
    data[base]["Ip"] = Ip
    data[base]["baselineCurrent"] = baselineCurrent
    data[base]["potential"] = potential
    
            
# ---------------------------------------------------------------------------#
# --------------------- Plot and Save the Data ------------------------------#

saveSubplot(fig)
plt.title(base + " DPV Graph") # Need this Line as we Change the Title When we Save Subplots
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
    plt.savefig(outputData + "Time Dependant DPV Curve Norepinephrine Full Curve Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
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
plt.savefig(outputData + "Concentration Dependant DPV Curve Norepinephrine Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
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
plt.savefig(outputData + "Time Dependant DPV Curve Norepinephrine Smooth.png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
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
    