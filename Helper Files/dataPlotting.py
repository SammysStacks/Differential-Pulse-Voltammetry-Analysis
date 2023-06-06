
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
    
    def __init__(self, outputDirectory, useCHIPeaks, numSubPlotsX, numFiles):
        # Create Output Folder if the One Given Does Not Exist
        outputDirectory = outputDirectory + "DPV Analysis/"
        os.makedirs(outputDirectory, exist_ok = True)
        
        # Save instance variables.
        self.outputDirectory = outputDirectory
        self.numSubPlotsX = numSubPlotsX
        self.useCHIPeaks = useCHIPeaks
        self.numFiles = numFiles
        self.finalYLim = [None, None]
        self.yLabel = "Current (uAmps)"
        self.xLabel = "Potential (V)"
    
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
    
    def setAxisInfo(self, ax, title, xLabel, yLabel, yLim):
        ax.set_xlabel(xLabel)
        ax.set_ylabel(yLabel)
        ax.set_title(title)
        ax.set_ylim(yLim)

    def saveplot(self, figure, superTitle, ax, legendAxes, legendLabels):
        # Plot and Save
        plotTitle = plt.suptitle(superTitle)
        legend = ax.legend(legendAxes, legendLabels, loc='upper left', bbox_to_anchor=(1.02, 1.02))
        figure.savefig(self.outputDirectory + superTitle + ".png", dpi=300, bbox_extra_artists=(legend, plotTitle), bbox_inches='tight')
        
    def saveSubplot(self, fig):
        # Plot and Save
        plt.title("Subplots of all DPV")
        #fig.legend(bbox_to_anchor=(.5, 1))
        #plt.subplots_adjust(hspace=0.5, wspace=0.5)
        fig.savefig(self.outputDirectory + "subplots.png", dpi=300)
    
    def addPeaksToPlot(self, ax, peakPotentials, peakCurrents, peakOffsets, legendAxes = [], legendLabels = []):
        # For each peak found.
        for peakNum in range(len(peakCurrents)):
            # Get the peak location.
            Ip = peakCurrents[peakNum]
            Vp = peakPotentials[peakNum]
            # Check the peak offset.
            peakOffset = peakOffsets
            if isinstance(peakOffsets, (list, np.ndarray)):
                peakOffset = peakOffsets[peakNum]   
            # Add the peak currents (verticle line) to the plots.
            legendLabels.append("Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            legendAxes.append(ax.vlines(x=Vp, ymin=peakOffset, ymax=peakOffset + float(Ip), linewidth=2, color='tab:red', label = "Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps"))
        
        return legendAxes, legendLabels
        
    def plotResults(self, potential, current, baselineCurrent, baselineSubtractedCurrent, peakIndices, peakCurrents, peakPotentials, axFull, fileNum, fileName):
        legendAxes = []; legendLabels = []

        # if using CHI peaks
        if self.useCHIPeaks:
            # Create a new figure to plot the dats
            fig = plt.figure(); ax = plt.gca()
            axisLimits = [None, None]

            # Plot the recorded data.
            legendLabels.append("Recorded Current")
            legendAxes.extend(ax.plot(potential, current, color='C0'))
            # Add the peaks to the plot.
            legendAxes, legendLabels = self.addPeaksToPlot(ax, peakPotentials, peakCurrents, peakOffsets = current[peakIndices] - peakCurrents, legendAxes = legendAxes, legendLabels = legendLabels)
            # Compile axis information.
            axisLimits = self.getAxisLimits([current], axisLimits) # Adjust axes limits.
            self.setAxisInfo(ax, title = "Baseline Analysis", xLabel = self.xLabel, yLabel = self.yLabel, yLim = axisLimits)
            
            # Save Figure
            self.saveplot(fig, fileName + " CHI Analysis", ax, legendAxes, legendLabels)
        else:
            # Create a new figure to plot the data
            fig, axes = plt.subplots(1, 2, sharey=False, sharex = True, figsize=(13, 5))
            axisLimits = [[None, None], [None, None]]
            
            # Plot only the subtracted baseline.
            legendAxes.extend(axes[0].plot(potential, baselineSubtractedCurrent, color='C2'))
            self.addPeaksToPlot(axes[0], peakPotentials, peakCurrents, peakOffsets = 0)
            # Adjust axes limits.
            axisLimits[0] = self.getAxisLimits([baselineSubtractedCurrent], axisLimits[0])
            # Compile axis information.
            self.setAxisInfo(axes[0], title = "Baseline Subtracted Current", xLabel = self.xLabel, yLabel = self.yLabel, yLim = axisLimits[0])
            
            # Plot all the data.
            legendAxes.extend(axes[1].plot(potential, current, color='C0'))
            legendAxes.extend(axes[1].plot(potential, baselineCurrent, color='C1'))
            # Specify the data labels.
            legendLabels = ["Baseline Subtracted Current", "Recorded Current", "Baseline Current"]
            # Add the peaks to the plot.
            legendAxes, legendLabels = self.addPeaksToPlot(axes[1], peakPotentials, peakCurrents, peakOffsets = baselineCurrent[peakIndices], legendAxes = legendAxes, legendLabels = legendLabels)
            # Compile axis information.
            axisLimits[1] = self.getAxisLimits([current, baselineCurrent], axisLimits[1]) # Adjust axes limits.
            self.setAxisInfo(axes[1], title = "Baseline Analysis", xLabel = self.xLabel, yLabel = self.yLabel, yLim = axisLimits[1])

            # Save Figure
            self.saveplot(fig, fileName + " DPV Analysis", axes[1], legendAxes, legendLabels)
                
        # Add these plots to the full plot curve.
        self.plotFullResults(potential, current, baselineCurrent, baselineSubtractedCurrent, peakIndices, peakCurrents, peakPotentials, axFull, fileNum, fileName)
    
    def plotFullResults(self, potential, current, baselineCurrent, baselineSubtractedCurrent, peakIndices, peakCurrents, peakPotentials, ax, fileNum, fileName):
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
            # Add the data to the plot.
            currentAxes.plot(potential, current, label="Recorded Current", color='C0')
            self.addPeaksToPlot(currentAxes, peakPotentials, peakCurrents, peakOffsets = max(current))
            # Set Legend Location
            currentAxes.legend(loc='best')  
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([current], self.finalYLim)
        elif True:
            # Add the data to the plot.
            currentAxes.plot(potential, baselineSubtractedCurrent, label="Baseline Subtracted Current", color='k', linewidth=2)
            self.addPeaksToPlot(currentAxes, peakPotentials, peakCurrents, peakOffsets = 0)
            currentAxes.axhline(y = 0, color='tab:red', linestyle='--')
            # Set Legend Location
            currentAxes.legend(loc='best') 
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([baselineSubtractedCurrent], self.finalYLim)
        else:
            # Add the data to the plot.
            currentAxes.plot(potential, current, label="Recorded Data: " + fileName, color='C0')
            currentAxes.plot(potential, baselineSubtractedCurrent, label="Baseline Subtracted Current", color='C2')
            currentAxes.plot(potential, baselineCurrent, label="Baseline Current", color='C1')  
            self.addPeaksToPlot(currentAxes, peakPotentials, peakCurrents, peakOffsets = baselineCurrent[peakIndices])
            # Set Legend Location
            currentAxes.legend(loc='best')  
            # Adjust axes limits
            self.finalYLim = self.getAxisLimits([current, baselineCurrent, baselineSubtractedCurrent], self.finalYLim)
    
        currentAxes.set_xlabel(self.xLabel)
        currentAxes.set_ylabel(self.yLabel)
        currentAxes.set_title(fileName)
        
    def plotCompiledResults(self, analysisInfo, peakInfo, fileNames):
        # Extract the data.
        allPeakPotentials, allPeakCurrents = np.array(peakInfo, dtype=object).T
        allPotentials, allUnfilteredCurrents, allCurrents, allBaselineCurrents, allBaselineSubtractedCurrents = np.asarray(analysisInfo).transpose((1,0,2))
        
        # Compilee the information.
        potential = allPotentials[0]
        compiledSignals = np.array([allUnfilteredCurrents, allCurrents, allBaselineCurrents, allBaselineSubtractedCurrents])
        plotTitles = ["Recorded Current", "Filtered Current", "Baseline Current", "Final Current"]
        
        for plotInd in range(len(compiledSignals)):
            signalData = compiledSignals[plotInd]
            
            # Create a new figure to plot the dats
            fig = plt.figure(); ax = plt.gca()
            legendAxes = []; legendLabels = []
            axisLimits = [None, None]
            
            # For each dataset/file.
            for fileInd in range(len(fileNames)):
                # Plot the recorded data.
                legendLabels.append(fileNames[fileInd])
                legendAxes.extend(ax.plot(potential, signalData[fileInd]))
                # Compile axis information.
                axisLimits = self.getAxisLimits([signalData[fileInd]], axisLimits) # Adjust axes limits.
                self.setAxisInfo(ax, title = "Compiled Analysis", xLabel = self.xLabel, yLabel = self.yLabel, yLim = axisLimits)
                
                # Save Figure
                self.saveplot(fig, plotTitles[plotInd], ax, legendAxes, legendLabels)
        
        
        
        
        
        

        
        