# EarthKAM Autoshape Daylight Tool
# EK_Autoshape_Daylight.py
# Tim Klug

from arcpy import env
from arcpy import da
from arcpy import ta
import arcgisscripting

import csv
import glob
import sys
import os
import time
import string
import datetime
from sets import Set

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("tracking")

gp = arcgisscripting.create(9.3)

 #
 # This file consists of three functions and a main level program designed to be run as an ArcGIS python tool.
 # These functions are designed to read subpoint lighting intervals of coasting arcs of the ISS from a csv input.
 # Each coasting arc shapefile (exported from AGI Systems Toolkit) is assigned an orbit number based on the 
 # subpoint lighting schedule read from the input csv. Each daylight orbit is exported from the coasting arc layer 
 # as a shapefile containing an arc of points spanning 45 minutes of daylight on the station's ground track.
 #
 # Author:
 #   Tim Klug
 #
 # History:
 #   tklug, March 22, 2017: script exported as ArcGIS python tool
 #
 

 # set parameters in ArcGIS python tool

 # Set main workspace. Should be named "Mission_XX"
arcpy.env.workspace = gp.GetParameterAsText(0)

# Input csv file with subpoint sunlight start and end times formatted as Y/m/d H:M:S.f, Y/m/d H:M:S.f
inCSV = gp.GetParameterAsText(1)

# Mission number read as long integer
MissionNum = gp.GetParameter(2)

# Optional offset parameter. Used to correct indices for orbit numbers
orbitOffset = gp.GetParameter(3) 



 # set workspace parameters

 # Location of raw "coasting arc" orbit layers exported from STK. Should be located at \Mission_XX\MXX_Raw_Orbits
rawDir = glob.glob(arcpy.env.workspace + r'\M' + str(MissionNum) + '_Raw_Orbits\*.shp')

 # Set location of processing directory. All exported outputs will appear here. Should be located at \Mission_XX\MXX_Processed_Orbits
procDir = arcpy.env.workspace + r'\M' + str(MissionNum) + '_Processed_Orbits'

 # Create processing directory if nonexistent.
if not os.path.isdir(procDir):
  os.makedirs(procDir)



 # Global variables set to keep track of orbit indices.
 # Necessary for linking subpoint lighting times from input csv with sunlit segments of coasting arcs through each iteration of FillOrbs()

 # OrbInd stores ordinal number of orbit increments e.g. first, second, third... 
global OrbInd
OrbInd  = 0

 # OrbFill calculates the actual orbit number for each coasting arc.
 # Values range from [0, ~6000]. Note addition of offset parameter for future adjustment
global OrbFill
OrbFill = int(rawDir[0][-8:-4]) - 2 + orbitOffset




def ReadCSV(inCSV):

 # Read input subpoint lighting intervals csv file and returns a tuple of datetime arrays.
 #
 # Params:
 #   inCSV : in, required, type = string
 #   path to the input csv file containing subpoint lighting intervals for each coasting arc
 #
 #   (startTimes, endTimes), out, required, type = tuple
 #   tuple of two arrays of datetime objects representing start and stop times of 
 #   subpoint lighting intervals

 # Define two arrays for storing datetime objects of start and end subpoint lighting times
  startTimes = []
  endtimes   = []

 # Define input format for datetime objects being read from input csv
  input_fmt  = '%Y/%m/%d %H:%M:%S.%f'

 # Open input csv file in read mode
  f = open(inCSV, 'rb')

 # Set reader variable to begin parsing csv
  reader = csv.reader(f, delimiter=',')

 # Begin parsing csv by declaring a 2 element list of lines from input file
  lines = list(reader)

 # Parse each line for both start and end times
 #   strip datetime objects and appending them to the appropriate list
  for row in lines:
    startTimes.append(datetime.datetime.strptime(row[0], input_fmt) )
    endTimes.append(datetime.datetime.strptime(row[1], input_fmt) )
    
 # Return datetime arrays as a tuple
  return (startTimes, endTimes)

def FillOrbs(coastingArc, sTime, eTime):

 # Fill daylight sections of coasting arc layers with their appropriate orbit number
 #
 # Params:
 #   coastingArc : in, required, type = string
 #   path to the input feature class containing a coasting arc with multiple orbits to be sorted
 #
 #   sTime : in, required, type = datetime array
 #   array of subpoint lighting start times retrieved from input csv
 #
 #   eTime : in, required, type = datetime array
 #   array of subpoint lighting end times retrieved from input csv

 # Declare use of global variables defined above
  global OrbInd
  global OrbFill

 # Define input format of datetime objects being compared in each row of the update cursorclass
  ReqTime_fmt = '%m/%d/%y %H:%M:%S'

 # Define fields being referenced by update cursor
  fields = ["TA_DATE","OrbitNum"]

 # Create arcpy update cursor referencing the fields defined above
  with arcpy.da.UpdateCursor(coastingArc, fields) as cursor:
    for row in cursor:                                            # Iterate through each row of the feature class
    
      if OrbInd < len(sTime):                                     # Continue making comparisons while the number of orbits
                                                                  #   processed is less than the total number of lighting times
                                                                  #   found in input file
                                                                  
        rowDT = datetime.datetime.strptime(row[0], ReqTime_fmt)   # Read and store the dto of the current row
        
        if rowDT < sTime[OrbInd]:                                 # Compare current row's dto with current subpoint lighting time
        
          continue                                                # Loop continues without updating row with orbit number for non-lighting times (night orbits)
          
        elif rowDT <= eTime[OrbInd]:                              # Row dto is less than the next end of subpoint lighting (day orbits)
        
          row[1] = 'Orbit ' + str(OrbFill)                        # Set orbit number field to equal current orbit number 
          
          cursor.updateRow(row)                                   # Update cursor to save changes before moving to next row
          
        elif rowDT > eTime[OrbInd]:                               # Row dto has exceeded next end of subpoint lighting (night has now fallen)
        
          OrbInd  += 1                                            # Increment OrbInd global variable to begin making comparisons to next subpoint lighting schedule
          
          OrbFill += 1                                            # Increment OrbFill global variable to begin filling next orbit number 
          
  return

def ExportArcs(coastingArc, fcOrbNum, procDir):

 # Export point-arc shapefiles of individual sunlight orbits from current coasting arc layer
 # 
 # Params:
 #   coastingArc, in, required, type = string
 #   path to feature class of coasting arc being sorted for dayligh orbits
 #
 #   fcOrbNum, in, required, type = integer
 #   Integer representing the orbit number of the first element of the coasting arc input
 #
 #   procDir, in, required, type = string
 #   path to processing directory

 # Set output directory within processing directory
  arcDir_out = procDir + r'\Arc'
  
 # Create point-arc output directory if nonexistent
  if not os.path.isdir(arcDir_out):
    os.makedirs(arcDir_out)
    
 # Define a set to store a record of all orbit numbers within coasting arc
  s = set()
  
 # Define a search cursor referencing orbit number field of the coasting arc 
  with arcpy.da.SearchCursor(coastingArc, "OrbitNum") as cursor:
 
 # Add each non-empty row of the cursor to the set of all orbit numbers within coasting arc
    for row in cursor:
      if row[0] != '':
        s.add(row[0])    # sets ignore duplicates

  while fcOrbNum <= int(max(s)[-4:]):                                       # Continue exporting daylight orbits from coasting arc
                                                                            #   while fcOrbNum is less than the max orbit number found in the set
  
    outArcFC = arcDir_out + r'\\orb' + str(fcOrbNum).zfill(4) + "_arc.shp"  # Define output filename using output directory and orbit number
    
    if not os.path.isfile(outArcFC):                                        # Check if output arc-point file already exists
          
      arcpy.Select_analysis(coastingArc,
                            outArcFC,
                            '"OrbitNum" = \'Orbit ' + str(fcOrbNum) +'\'')  # select features with current orbit number and export to new arc-point shapefile
      
    fcOrbNum += 1                                                           # Increment orbit number to export next daylight orbit

    
## Main level program ##

 # Define start and end datetime object arrays for subpoint lighting intervals
startTimes = []
endTimes = []

# Assign tuple of dto arrays to output of ReadCSV()
(startTimes,endTimes) = ReadCSV(inCSV)

# Loop through raw input directory of coasting arcs
for coastingArc in rawDir:

  fcOrbNum = int(coastingArc[-8:-4])                            # Read first orbit number of the current coasting arc
    
  arcpy.AddField_management(coastingArc, "OrbitNum", "STRING")  # Add "OrbitNum" field to coasting arc feature
  
  arcpy.DeleteField_management(coastingArc, ["TRACKID"])        # Delete "TrackID" field from coasting arc feature
  
  FillOrbs(coastingArc, startTimes, endTimes)                   # Fill coasting arc feature's orbit numbers using FillOrbs()
  
  ExportArcs(coastingArc, fcOrbNum, procDir)                    # Export all daylight intervals within current coasting arc to new arc-point shapefiles