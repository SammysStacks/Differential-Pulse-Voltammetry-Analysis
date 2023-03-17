
# -------------------------------------------------------------------------- #
# ------------------------- Imported Modules --------------------------------#

# General modules
import os
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
        self.finalYLim = [0,0]
        self.yLabel = yLabel

    
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
            print("numSubPlotsX CANNOT be < 1. Currently it is: ", self.numSubPlotsX)
            exit
        
        # Plot Data in Subplots
        if self.useCHIPeaks and len(peakCurrents) != 0 and len(peakPotentials) != 0:
            currentAxes.plot(potential, current, label="True Data: " + fileName, color='C0')
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]    
                currentAxes.axvline(x=Vp, ymin=max(current) - Ip, ymax=max(current), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            # Set Legend Location
            currentAxes.legend(loc='upper left')  
        elif not self.plotBaselineSteps:
            currentAxes.plot(potential, baselineCurrent, label="Current After Baseline Subtraction", color='k', linewidth=2)
            # Plot the Peak Current (Verticle Line) for Visualization
            for peakNum in range(len(peakCurrents)):
                Ip = peakCurrents[peakNum]
                Vp = peakPotentials[peakNum]                
                currentAxes.vlines(x=Vp, ymin=0, ymax=float(Ip), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
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
            currentAxes.vlines(x=Vp, ymin=baseline[peakInd], ymax=float(Ip+baseline[peakInd]), linewidth=2, color='tab:red', label="Peak Current: " + "%.3g"%Vp + " V, " + "%.4g"%Ip + " uAmps")
            # Set Legend Location
            currentAxes.legend(loc='best')  
    
        currentAxes.set_xlabel("Potential (V)")
        currentAxes.set_ylabel(self.yLabel)
        currentAxes.set_title(fileName)
        # Find Full Axis Width
        self.finalYLim[0] = min(self.finalYLim[0], currentAxes.get_ylim()[0])
        self.finalYLim[1] = max(self.finalYLim[1], currentAxes.get_ylim()[1])
        
        