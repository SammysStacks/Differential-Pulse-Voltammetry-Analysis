#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Need to Install on the Anaconda Prompt:
    $ pip install pyexcel
"""


# Basic Modules
import os
import sys
import numpy as np
# Read/Write to Excel
import csv
import pyexcel
import openpyxl as xl

class dataProcessing:        
        
    def xls2xlsx(self, excelFile, outputFolder):
        """
        Converts .xls Files to .xlsx Files That OpenPyxl Can Read
        If the File is Already a .xlsx Files, Do Nothing
        If the File is Neither a .xls Nor .xlsx, it Exits the Program
        """
        # Check That the Current Extension is .xls or .xlsx
        _, extension = os.path.splitext(excelFile)
        # If the Extension is .xlsx, the File is Ready; Do Nothing
        if extension == '.xlsx':
            return excelFile
        # If the Extension is Not .xls/.xlsx, Then the Data is in the Wrong Format; Exit Program
        if extension not in ['.xls', '.xlsx']:
            print("Cannot Convert File to .xlsx")
            sys.exit()
        
        # Create Output File Directory to Save Data ONLY If None Exists
        os.makedirs(outputFolder, exist_ok = True)
        # Convert '.xls' to '.xlsx'
        filename = os.path.basename(excelFile)
        newExcelFile = outputFolder + filename + "x"
        pyexcel.save_as(file_name = excelFile, dest_file_name = newExcelFile, logfile=open(os.devnull, 'w'))
        
        # Return New Excel File Name
        return newExcelFile
    
    def txt2csv(self, txtFile, csvFile, csvDelimiter = ",", overwriteCSV = False):
        # Check to See if CSV Conversion Alreayd Occurred
        if not os.path.isfile(csvFile) or overwriteCSV:
            with open(txtFile, "r") as inputData:
                in_reader = csv.reader(inputData, delimiter = csvDelimiter)
                with open(csvFile, 'w', newline='') as out_csv:
                    out_writer = csv.writer(out_csv)
                    for row in in_reader:
                        out_writer.writerow(row)
    
    def convertToExcel(self, inputFile, excelFile, excelDelimiter = ",", overwriteXL = False, testSheetNum = 0):
        """
        inputFile: The Input TXT/CSV File to Convert XLSX
        excelFile: The Output Excel File Name (XLSX)
        """
        # If the File is Not Already Converted: Convert the CSV to XLSX
        if not os.path.isfile(excelFile) or overwriteXL:
            # Make Excel WorkBook
            xlWorkbook = xl.Workbook()
            xlWorksheet = xlWorkbook.active
            # Write the Data from the CSV File to the Excel WorkBook
            with open(inputFile, "r") as inputData:
                inReader = csv.reader(inputData, delimiter = excelDelimiter)
                with open(excelFile, 'w+', newline='') as newFile:
                    for row in inReader:
                        xlWorksheet.append(row)
            # Save as New Excel File
            xlWorkbook.save(excelFile)
        # Else Load the GSR Data from the Excel File
        else:
            # Load the GSR Data from the Excel File
            xlWorkbook = xl.load_workbook(excelFile, data_only=True, read_only=True)
            xlWorksheet = xlWorkbook.worksheets[testSheetNum]
        
        # Return Excel Sheet
        return xlWorkbook, xlWorksheet
    

class processFiles(dataProcessing):
    
    def getFiles(self, dataDirectory, fileDoesntContain, fileContains):
        # If Using All the CSV Files in the Folder
        dpvFiles = []; filesAdded = set();
        for fileName in os.listdir(dataDirectory):
            fileBase = os.path.splitext(fileName)[0]
            if fileName.endswith((".txt",'csv','xlsx')) and fileDoesntContain not in fileName and fileContains in fileName and fileBase not in filesAdded:
                dpvFiles.append(fileName)
                filesAdded.add(fileBase)
        if len(dpvFiles) == 0:
            print("No TXT/CSV/XLSX Files Found in the Data Folder:", dataDirectory)
            print("Found the Following Files:", os.listdir(dataDirectory))
            sys.exit()
        
        return dpvFiles

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
            
            if findStart:
                # If Peak Found by CHI, Get Peak Potential
                if cellVal.startswith("Ep = "):
                    peakPotential = float(cellVal.split(" = ")[-1][:-1])
                    peakPotentialList.append(peakPotential)
                # If Peak Found by CHI, Get Peak Current
                elif cellVal.startswith("ip = "):
                    peakCurrent = float(cellVal.split(" = ")[-1][:-1])
                    peakCurrentList.append(peakCurrent)
                elif cellVal == "Potential/V":
                    next(rowGenerator) # Skip Over Empty Cell After Title
                    findStart = False
            else:
                # Break out of Loop if no More Data (edge effect if someone edits excel)
                if cell[0].value == None:
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
            print("The following Input File Does Not Exist:", oldFile)
            sys.exit()

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
            xlWorksheet = xlWorkbook.worksheets[testSheetNum]
        else:
            print("The Following File is Neither CSV, TXT, Nor XLSX:", excelFile)
            sys.exit()
        
        # Extract the Data
        print("Extracting Data from the Excel File:", excelFile)
        potential, current, peakPotentialList, peakCurrentList = self.extractCHIData_DPV(xlWorksheet)
        
        xlWorkbook.close()
        # Finished Data Collection: Close Workbook and Return Data to User
        print("Done Collecting Data");
        return potential, current, peakPotentialList, peakCurrentList


if __name__ == "__main__":
    
    inputFile = './diffusion_4.txt'
    processPulseData().getData(inputFile)
    
    
    
    