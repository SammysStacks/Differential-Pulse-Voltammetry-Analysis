
"""

"""

# -------------------------------------------------------------------------- #
# ------------------------- Imported Modules --------------------------------#

import numpy as np
# Modules to Plot
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------- #
# ------------------------- Plotting Functions ------------------------------#

class plots:
    
    def __init__(self, yLabel, outputDirectory, useCHIPeaks, plotBaselineSteps, numSubPlotsX, numFiles):
        self.yLabel = yLabel
        self.outputDirectory = outputDirectory
        self.useCHIPeaks = useCHIPeaks
        self.plotBaselineSteps = plotBaselineSteps
        self.numSubPlotsX = numSubPlotsX
        self.numFiles = numFiles
    
    def saveplot(self, figure, axisLimits, base):
        # Plot and Save
        plt.title(base + " DPV Graph")
        plt.xlabel("Potential (V)")
        plt.ylabel(self.yLabel)
        plt.ylim(axisLimits)
        lgd = plt.legend(bbox_to_anchor=(1.04,1), borderaxespad=0)
        figure.savefig(self.outputDirectory + base + ".png", dpi=300, bbox_extra_artists=(lgd,), bbox_inches='tight')
    
    
    def saveSubplot(self, fig):
        # Plot and Save
        plt.title("Subplots of all DPV")
        #fig.legend(bbox_to_anchor=(.5, 1))
        #plt.subplots_adjust(hspace=0.5, wspace=0.5)
        fig.savefig(self.outputDirectory + "subplots.png", dpi=300)
    
    def normalize(self, point, low, high):
        return (point-low)/(high-low)
    
    def plotResults(self, potential, current, baseline, baselineCurrent, peakCurrents, peakPotentials, fileName):
        # Plot the Initial Data
        fig1 = plt.figure()
        plt.plot(potential, current, label="True Data: " + fileName, color='C0')
        
        if self.useCHIPeaks:
            # Set Axes Limits
            axisLimits = [min(current) - min(current)/10, max(current) + max(current)/10]
        else:
            # Plot Subtracted baseline
            plt.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            plt.plot(potential, baseline, label="Baseline Current", color='C1')  
            
            # Get the Axis Limit on the Figure
            axisLimits = [min(*baselineCurrent,*current,*baseline), max(*baselineCurrent,*current,*baseline)]
            axisLimits[0] -= (axisLimits[1] - axisLimits[0])/10
            axisLimits[1] += (axisLimits[1] - axisLimits[0])/10
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]
                plt.axvline(x=Vp, ymin=self.normalize(np.argmax(baseline), axisLimits[0], axisLimits[1]), ymax=self.normalize(float(Ip + np.argmax(baseline)), axisLimits[0], axisLimits[1]), linewidth=2, color='tab:red', label="Peak Current " + str(peakNum) + ": " + "%.4g"%Ip)
    
        # Save Figure
        self.saveplot(fig1, axisLimits, fileName)
    
    def plotFullResults(self, potential, current, baseline, baselineCurrent, peakInd, peakCurrents, peakPotentials, ax, fileNum, fileName):
        # Keep Running Subplots Order
        if self.numSubPlotsX == 1 or self.numFiles == 1:
            currentAxes = ax
        elif self.numSubPlotsX == 1:
            currentAxes = ax[fileNum]
        elif self.numSubPlotsX == self.numFiles:
            currentAxes = ax[fileNum]
        elif self.numSubPlotsX > 1:
            currentAxes = ax[fileNum//self.numSubPlotsX][fileNum%self.numSubPlotsX]
        else:
            print("numSubPlotsX CANNOT be < 1. Currently it is: ", self.numSubPlotsX)
            exit
        
        # Plot Data in Subplots
        if self.useCHIPeaks and len(peakCurrents) != 0 and len(peakPotentials) != 0:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]    
                currentAxes.axvline(x=Vp, ymin=self.normalize(max(current) - Ip, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=self.normalize(max(current), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='tab:red', label="Peak Current " + str(peakNum) + ": " + "%.4g"%Ip)
            # Set Legend Location
            currentAxes.legend(loc='upper left')  
        elif not self.plotBaselineSteps:
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='k', linewidth=2)
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]                
                currentAxes.axvline(x=Vp, ymin=self.normalize(0, currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=self.normalize(float(Ip), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='tab:red', label="Peak Current " + str(peakNum) + ": " + "%.4g"%Ip)
            currentAxes.axhline(y = 0, color='tab:red', linestyle='--')
            # Set Legend Location
            currentAxes.legend(loc='upper left')  
        else:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            currentAxes.plot(potential, baseline, label="Baseline Current", color='C1')  
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]   
            currentAxes.axvline(x=Vp, ymin=self.normalize(baseline[peakInd], currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), ymax=self.normalize(float(Ip+baseline[peakInd]), currentAxes.get_ylim()[0], currentAxes.get_ylim()[1]), linewidth=2, color='tab:red', label="Peak Current " + str(peakNum) + ": " + "%.4g"%Ip)
            # Set Legend Location
            currentAxes.legend(loc='best')  
    
        currentAxes.set_xlabel("Potential (V)")
        currentAxes.set_ylabel(self.yLabel)
        currentAxes.set_title(fileName)
        
        