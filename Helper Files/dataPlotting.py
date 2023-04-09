
# -------------------------------------------------------------------------- #
# ------------------------- Imported Modules --------------------------------#

# General modules
import os
import numpy as np
# Modules to plot
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------- #
# ------------------------- Plotting Functions ------------------------------#

class plots:
    
    def __init__(self, yLabel, outputDirectory, useCHIPeaks, plotBaselineSteps, numSubPlotsX, numFiles):
        # Create Output Folder if the One Given Does Not Exist
        outputDirectory = outputDirectory + "DPV Analysis/"
        os.makedirs(outputDirectory, exist_ok = True)
        
        # Save instance variables.
        self.plotBaselineSteps = plotBaselineSteps
        self.outputDirectory = outputDirectory
        self.numSubPlotsX = numSubPlotsX
        self.useCHIPeaks = useCHIPeaks
        self.numFiles = numFiles
        self.finalYLim = [None, None]
        self.yLabel = yLabel
    
    def clearFigure(self, fig):
        # Clear plots
        fig.clear()
        plt.cla(); plt.clf()
        plt.close(fig); plt.close('all')
        
    def getAxisLimits(self, dataOnPlots = [], yLim = [None, None]):
        # For each plot on the graph
        for data in dataOnPlots:
            # If data is already on the plot, get the old bounds of the data.
            if yLim[0] != None:
                oldDataRange = (yLim[1] - yLim[0])/1.2
                oldDataMax = yLim[1] - oldDataRange*0.1
                oldDataMin = yLim[0] + oldDataRange*0.1
            else:
                oldDataMax = -np.inf
                oldDataMin = np.inf
            
            # Get the plotting bounds, considering all the data.
            newDataMax = max(*data, oldDataMax)
            newDataMin = min(*data, oldDataMin)
            newDataRange = newDataMax - newDataMin
            # Calculate the y-limits for the data
            yLim[0] = newDataMin - newDataRange*0.1
            yLim[1] = newDataMax + newDataRange*0.1

        return yLim

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
        axisLimits = [None, None]
        
        if self.useCHIPeaks:
            plt.plot(potential, current, label="True Data: " + fileName, color='C0')
            # Set Axes Limits
            axisLimits = self.getAxisLimits([current], axisLimits)
        else:
            # Plot Subtracted baseline
            plt.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            if self.plotBaselineSteps:
                plt.plot(potential, current, label="True Data: " + fileName, color='C0')
                plt.plot(potential, baseline, label="Baseline Current", color='C1')  
                # Adjust axes limits
                axisLimits = self.getAxisLimits([current, baseline], axisLimits)
                # Save as different filename
                fileName += " Full Analysis"
            # Adjust axes limits
            axisLimits = self.getAxisLimits([baselineCurrent], axisLimits)
            
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]
                plt.axvline(x=Vp, ymin=self.normalize(0, axisLimits[0], axisLimits[1]), ymax=self.normalize(float(Ip), axisLimits[0], axisLimits[1]), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
    
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
            exit("numSubPlotsX CANNOT be < 1. Currently it is: ", self.numSubPlotsX)
        
        # Plot Data in Subplots
        if self.useCHIPeaks and len(peakCurrents) != 0 and len(peakPotentials) != 0:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]    
                currentAxes.axvline(x=Vp, ymin=max(current) - Ip, ymax=max(current), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            # Set Legend Location
            currentAxes.legend(loc='best')  
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([current], self.finalYLim)
        elif not self.plotBaselineSteps or True:
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='k', linewidth=2)
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]                
                currentAxes.vlines(x=Vp, ymin=0, ymax=float(Ip), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            currentAxes.axhline(y = 0, color='tab:red', linestyle='--')
            # Set Legend Location
            currentAxes.legend(loc='best') 
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([baselineCurrent], self.finalYLim)
        else:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='C2')
            currentAxes.plot(potential, baseline, label="Baseline Current", color='C1')  
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]   
                peakValue = baseline[peakInd][peakNum]
                currentAxes.vlines(x=Vp, ymin=peakValue, ymax=float(Ip+peakValue), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            # Set Legend Location
            currentAxes.legend(loc='best')  
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([current, baseline, baselineCurrent], self.finalYLim)
    
        currentAxes.set_xlabel("Potential (V)")
        currentAxes.set_ylabel(self.yLabel)
        currentAxes.set_title(fileName)
        
        