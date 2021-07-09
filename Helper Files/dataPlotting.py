
"""

"""

# -------------------------------------------------------------------------- #
# ------------------------- Imported Modules --------------------------------#

# Modules to Plot
import matplotlib.pyplot as plt

# -------------------------------------------------------------------------- #
# ------------------------- Plotting Functions ------------------------------#

class plots:
    
    def __init__(self, yLabel, outputDirectory):
        self.yLabel = yLabel
        self.outputDirectory = outputDirectory
    
    def saveplot(self, figure, axisLimits, base):
        # Plot and Save
        plt.title(base + " DPV Graph")
        plt.xlabel("Potential (V)")
        plt.ylabel(self.yLabel)
        plt.ylim(axisLimits)
        plt.legend()
        figure.savefig(self.outputDirectory + base + ".png", dpi=300)
    
    
    def saveSubplot(self, fig):
        # Plot and Save
        plt.title("Subplots of all DPV")
        #fig.legend(bbox_to_anchor=(.5, 1))
        #plt.subplots_adjust(hspace=0.5, wspace=0.5)
        fig.savefig(self.outputDirectory + "subplots.png", dpi=300)
    
    def normalize(self, point, low, high):
        return (point-low)/(high-low)