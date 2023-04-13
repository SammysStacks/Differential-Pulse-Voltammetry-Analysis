
# -------------------------------------------------------------------------- #
# ---------------------------- Imported Modules ---------------------------- #

# Basic Modules
import os
import sys
import time
import numpy as np
import pandas as pd
from natsort import natsorted
# Read/Write to Excel
import csv
import pyexcel
import openpyxl as xl
from openpyxl import load_workbook, Workbook
# Openpyxl Styles
from openpyxl.styles import Alignment
from openpyxl.styles import Font

class handlingExcelFormat:   

    def __init__(self):
        # Hardcoded sheetnames for different types of excel information
        self.emptySheetName = "empty"
        self.peakInfo_SheetName = "Signal Data; File 0"
        self.signalData_Sheetname = "Peak Info; File 0"
        
        # Excel parameters
        self.maxAddToexcelSheet = 1048500  # Max Rows in a Worksheet
        
    def convertToXLSX(self, inputExcelFile):
        """
        Converts .xls Files to .xlsx Files That OpenPyxl Can Read
        If the File is Already a .xlsx Files, Do Nothing
        If the File is Neither a .xls Nor .xlsx, it Exits the Program
        """
        # Check That the Current Extension is .xls or .xlsx
        _, extension = os.path.splitext(inputExcelFile)
        # If the Extension is .xlsx, the File is Ready; Do Nothing
        if extension == '.xlsx':
            return inputExcelFile
        # If the Extension is Not .xls/.xlsx, Then the Data is in the Wrong Format; Exit Program
        if extension not in ['.xls', '.xlsx']:
            print("Cannot Convert File to .xlsx")
            sys.exit()
        
        # Create Output File Directory to Save Data ONLY If None Exists
        newExcelFolder = os.path.dirname(inputExcelFile) + "/Excel Files/"
        os.makedirs(newExcelFolder, exist_ok = True)
        
        # Convert '.xls' to '.xlsx'
        filename = os.path.basename(inputExcelFile)
        newExcelFile = newExcelFolder + filename + "x"
        pyexcel.save_as(file_name = inputExcelFile, dest_file_name = newExcelFile, logfile=open(os.devnull, 'w'))
        
        # Save New Excel name
        return newExcelFile
    
    def txt2csv(self, txtFile, csvFile, csvDelimiter = ",", overwriteCSV = False):
        # Check to see if csv conversion alreayd happened
        if not os.path.isfile(csvFile) or overwriteCSV:
            with open(txtFile, "r") as inputData:
                in_reader = csv.reader(inputData, delimiter = csvDelimiter)
                with open(csvFile, 'w', newline='') as out_csv:
                    out_writer = csv.writer(out_csv)
                    for row in in_reader:
                        out_writer.writerow(row)
    
    def convertToExcel(self, inputFile, excelFile, excelDelimiter = ",", overwriteXL = False, testSheetNum = 0):
        # If the File is Not Already Converted: Convert the CSV to XLSX
        if not os.path.isfile(excelFile) or overwriteXL:
            if excelDelimiter == "fixedWidth":
                df = pd.read_fwf(inputFile)
                df.drop(index=0, inplace=True) # drop the underlines
                df.to_excel(excelFile, index=False)
                # Load the Data from the Excel File
                xlWorkbook = xl.load_workbook(excelFile, data_only=True, read_only=True)
                xlWorksheets = xlWorkbook.worksheets[testSheetNum:]
            else:
                # Make Excel WorkBook
                xlWorkbook = xl.Workbook()
                xlWorksheet = xlWorkbook.active
                # Write the Data from the CSV File to the Excel WorkBook
                with open(inputFile, "r") as inputData:
                    inReader = csv.reader(inputData, delimiter = excelDelimiter)
                    with open(excelFile, 'w+', newline=''):
                        for row in inReader:
                            xlWorksheet.append(row)    
                # Save as New Excel File
                xlWorkbook.save(excelFile)
                xlWorksheets = [xlWorksheet]
        # Else Load the Data from the Excel File
        else:
            # Load the Data from the Excel File
            xlWorkbook = xl.load_workbook(excelFile, data_only=True, read_only=True)
            xlWorksheets = xlWorkbook.worksheets[testSheetNum:]
        
        # Return Excel Sheet
        return xlWorkbook, xlWorksheets
    
    def splitExcelSheetsToExcelFiles(self, inputFile):
        wb = load_workbook(filename=inputFile)
        
        for sheet in wb.worksheets:
            new_wb = Workbook()
            ws = new_wb.active
            for row_data in sheet.iter_rows():
                for row_cell in row_data:
                    ws[row_cell.coordinate].value = row_cell.value
        
            new_wb.save('{0}.xlsx'.format(sheet.title))
    
    def addExcelAesthetics(self, worksheet):
        # Initialize variables
        align = Alignment(horizontal='center',vertical='center',wrap_text=True) 
        
        # Loop through each header cell
        for headerCell in worksheet[1]:
            column_cells = worksheet[headerCell.column_letter]
            
            # Set the column width
            length = max(len(str(cell.value) if cell.value else "") for cell in column_cells)
            worksheet.column_dimensions[headerCell.column_letter].width = max(length, worksheet.column_dimensions[headerCell.column_letter].width)
            worksheet.column_dimensions[headerCell.column_letter].bestFit = True
            # Center the Data in the Cells
            for cell in column_cells:
                cell.alignment = align
            # Set the header text color
            headerCell.font = Font(color='00FF0000', italic=True, bold=True)
        
        return worksheet
    

class processFiles(handlingExcelFormat):
    
    def getFiles(self, dataDirectory, removeFilesContaining, analyzeFilesContaining):
        # Setup parameters
        analysisFiles = []; filesAdded = set();
        
        # For each file in the directory
        for fileName in os.listdir(dataDirectory):
            fileBase = os.path.splitext(fileName)[0]
            
            # Do not analyze files with a certain substring in the name.
            for substring in removeFilesContaining:
                if substring in fileName:
                    continue
            # Only analyze files with a certain substring in the name.
            for substring in analyzeFilesContaining:
                if substring not in fileName:
                    continue            
            
            # Keep track of previously unseen analysis files.
            if fileName.endswith((".txt",'csv','xlsx')) and fileBase not in filesAdded:
                analysisFiles.append(dataDirectory + fileName)
                filesAdded.add(fileBase)
        
        # If not analysis files found.s
        if len(analysisFiles) == 0:
            # Stop the program.
            print("Found the Following Files:", os.listdir(dataDirectory))
            sys.exit("No TXT/CSV/XLSX Files Found in the Data Folder: " + dataDirectory)
        
        # Sort the files and return them
        analysisFiles = natsorted(analysisFiles)
        return analysisFiles
    
    class cellObject:
        def __init__(self, value):
            self.value = value

    def extractCHIData_DPV(self, chiWorksheet):
        
        peakCurrentList = []; peakPotentialList = []; 
        potential = []; current = []; findStart = True
        # Loop Through the Info Section and Extract the Needxed Run Info from Excel
        rowGenerator = chiWorksheet.rows
        for cell in rowGenerator:
            # Get Cell Value
            cellVal = cell[0].value
            if cellVal == None:
                continue
            elif ',' in cellVal:
                cellValues = cellVal.split(",")
                cell = []
                for cellValue in cellValues:
                    cell.append(self.cellObject(cellValue))
                cellVal = cell[0].value
            
            if findStart:
                # If Peak Found by CHI, Get Peak Potential
                if cellVal.startswith("Ep = "):
                    peakPotential = float(cellVal.split(" = ")[-1][:-1])
                    peakPotentialList.append(peakPotential)
                # If Peak Found by CHI, Get Peak Current
                elif cellVal.startswith("ip = "):
                    peakCurrent = float(cellVal.split(" = ")[-1][:-1])
                    peakCurrentList.append(peakCurrent)
                elif "Potential/V" in cellVal:
                    next(rowGenerator) # Skip Over Empty Cell After Title
                    findStart = False
            else:
                # Break out of Loop if no More Data (edge effect if someone edits excel)
                if cell[0].value == None and len(potential) != 0:
                    break
                
                # Find the Potential and Current Data points
                potential.append(float(cell[0].value))
                current.append(float(cell[1].value))

        # Convert to Numpy Array
        current = np.array(current)
        potential = np.array(potential)
        
        return potential, current, peakPotentialList, peakCurrentList
    
    
    def getData(self, oldFile, outputFolder, testSheetNum = 0, excelDelimiter = ","):
        """
        --------------------------------------------------------------------------
        Input Variable Definitions:
            oldFile: The Path to the Excel File Containing the Data: txt, csv, xls, xlsx
            testSheetNum: An Integer Representing the Excel Worksheet (0-indexed) Order.
        --------------------------------------------------------------------------
        """ 
        
        # Check if File Exists
        if not os.path.exists(oldFile):
            sys.exit("\nThe following Input File Does Not Exist: " + oldFile)

        # Convert TXT and CSV Files to XLSX
        if oldFile.endswith((".txt", ".csv")):
            # Extract Filename Information
            oldFileExtension = os.path.basename(oldFile)
            filename = os.path.splitext(oldFileExtension)[0]
            newFilePath = outputFolder + "Excel Files/"
            # Make Output Folder Directory if Not Already Created
            os.makedirs(newFilePath, exist_ok = True)

            # Convert CSV or TXT to XLSX
            excelFile = newFilePath + filename + ".xlsx"
            xlWorkbook, xlWorksheet = self.convertToExcel(oldFile, excelFile, excelDelimiter = excelDelimiter, overwriteXL = False, testSheetNum = testSheetNum)
        # If the File is Already an Excel File, Just Load the File
        elif oldFile.endswith(".xlsx"):
            excelFile = oldFile
            # Load the GSR Data from the Excel File
            xlWorkbook = xl.load_workbook(excelFile, data_only=True, read_only=True)
            xlWorksheet = xlWorkbook.worksheets[testSheetNum:]
        else:
            sys.exit("\nThe Following File is Neither CSV, TXT, Nor XLSX: " + excelFile)
        
        # Extract the Data
        print("\nExtracting Data from the Excel File:", excelFile)
        potential, current, peakPotentialList, peakCurrentList = self.extractCHIData_DPV(xlWorksheet[0])
        
        xlWorkbook.close()
        # Finished Data Collection: Close Workbook and Return Data to User
        return potential, current, peakPotentialList, peakCurrentList

class saveExcelData(handlingExcelFormat):
    
    def getExcelDocument(self, excelFile, overwriteSave = False):
        # If the excel file you are saving already exists.
        if os.path.isfile(excelFile):
            # If You Want to Overwrite the Excel.
            if overwriteSave:
                print("\t\tDeleting Old Excel Workbook")
                os.remove(excelFile) 
            else:
                print("\t\tNot overwriting the file ... but your file already exists??")
            
        # If the File is Not Present: Create The Excel File
        if not os.path.isfile(excelFile):
            print("\t\tCreating New Excel Workbook")
            # Make Excel WorkBook
            WB = xl.Workbook()
            worksheet = WB.active 
            worksheet.title = self.emptySheetName
        else:
            print("\t\tExcel File Already Exists. Adding New Sheet to File")
            WB = xl.load_workbook(excelFile, read_only=False)
            worksheet = WB.create_sheet(self.emptySheetName)
        return WB, worksheet
    
    def saveDataDPV(self, potential, current, baselineCurrent, baselineSubtractedCurrent, peakCurrents, peakPotentials, saveExcelPath):
        print("Saving the Data")
        # ------------------------------------------------------------------ #
        # -------------------- Setup the excel document -------------------- #
        # Create the path to save the excel file.
        os.makedirs(os.path.dirname(saveExcelPath), exist_ok=True) # Create Output File Directory to Save Data: If None Exists
        
        # Get the excel document.
        WB, worksheet = self.getExcelDocument(saveExcelPath, overwriteSave = True)
        
        # ------------------------------------------------------------------ #
        # ---------------------- Add data to document ---------------------- #   
        
        # Get the Header for the Data
        header = ["Potential (V)", "Recorded Current (uAmps)"]
        # Add baseline headers if availible.
        if len(baselineCurrent) != 0:
            header.extend(["Baseline Current (uAmps)", "Baseline Subtracted Current (uAmps)"])
        # Add peak information to the headers.
        header.extend(["", "Peak Potentials (V)", "Peak Currents (uAmps)"])
            
        # Loop through/save all the data in batches of maxAddToexcelSheet.
        for firstIndexInFile in range(0, len(potential), self.maxAddToexcelSheet):
            # Add the information to the page
            worksheet.title = self.signalData_Sheetname
            worksheet.append(header)  # Add the header labels to this specific file.
                        
            # Loop through all data to be saved within this sheet in the excel file.
            for dataInd in range(firstIndexInFile, min(firstIndexInFile+self.maxAddToexcelSheet, len(potential))):
                # Organize all the data
                row = [potential[dataInd], current[dataInd]]
                if len(baselineCurrent) != 0:
                    row.extend([baselineCurrent[dataInd], baselineSubtractedCurrent[dataInd]])
                # Add peak information if present.
                if dataInd < len(peakPotentials):
                    row.extend(["", peakPotentials[dataInd], peakCurrents[dataInd]])
                
                # Add the row to the worksheet
                worksheet.append(row)
    
            # Finalize document
            worksheet = self.addExcelAesthetics(worksheet) # Add Excel Aesthetics
            worksheet = WB.create_sheet(self.emptySheetName) # Add Sheet

        # Remove empty page
        if worksheet.title == self.emptySheetName:
            WB.remove(worksheet)

        # ------------------------------------------------------------------ #
        # ---------------- Add peak information to document ---------------- # 
        
        # Start a new sheet.
        worksheet = WB.create_sheet(self.emptySheetName) # Add Sheet
        # Get the header for the peak information
        header = ["Peak Potentials (V)", "Peak Currents (uAmps)"]
            
        # Loop through/save all the data in batches of maxAddToexcelSheet.
        for firstIndexInFile in range(0, len(peakPotentials), self.maxAddToexcelSheet):
            # Add the information to the page
            worksheet.title = self.peakInfo_SheetName
            worksheet.append(header)  # Add the header labels to this specific file.
                        
            # Loop through all data to be saved within this sheet in the excel file.
            for dataInd in range(firstIndexInFile, min(firstIndexInFile+self.maxAddToexcelSheet, len(peakPotentials))):
                # Organize all the data
                row = [peakPotentials[dataInd], peakCurrents[dataInd]]
                
                # Add the row to the worksheet
                worksheet.append(row)
    
            # Finalize document
            worksheet = self.addExcelAesthetics(worksheet) # Add Excel Aesthetics
            worksheet = WB.create_sheet(self.emptySheetName) # Add Sheet

        # Remove empty page
        if worksheet.title == self.emptySheetName:
            WB.remove(worksheet)
        
        # ------------------------------------------------------------------ #
        # ------------------------ Save the document ----------------------- #  
        # Save as New Excel File
        WB.save(saveExcelPath)
        WB.close()
    

    