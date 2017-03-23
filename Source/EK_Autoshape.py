 # EarthKAM AutoShape
 # EK_Autoshape.py
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
 # This file consists of five functions and a main level program designed to be run as an ArcGIS python tool.
 # These functions are designed to process a directory of point-arc shapefiles of ISS orbits during EarthKAM
 # missions. The main level program establishes a workflow that exports time-enabled polylines from each
 # point-arc ephemeris shapefile, converts those polylines to buffered polygon shapes that reflect the field
 # of view of each camera lens being used, and reformats buffer shapefiles to contain orbit numbers and photo 
 # request formatted datetime objects.
 #
 # Author:
 #   Tim Klug
 #
 # History:
 #   tklug, March 23, 2017: script exported as ArcGIS python tool
 #

 
 # set parameters in ArcGIS python tool

 # Set main workspace. Should be named "Mission_XX"
arcpy.env.workspace = gp.GetParameterAsText(0)

 # Set lens swap orbit as a long integer
SwapLens = gp.GetParameter(1)

 # Set mission number as a long integer
MissionNum = gp.GetParameter(2)


 # set workspace parameters

 # Set location of processing directory. All exported outputs will appear here.
 #   Should be located at \Mission_XX\MXX_Processed_Orbits
procDir = arcpy.env.workspace + r'\M' + str(MissionNum) + '_Processed_Orbits'

 # Create processing directory if nonexistent.
if not os.path.isdir(procDir):
  os.makedirs(procDir)
  
 # Convert Ephemeris Time (MM/DD/YY HH:MM:SS) to Request Time format (YYYY/DDD/HH:MM:SS)
def ConvertEphTime(EphTime):

 # Convert Ephemeris Time (MM/DD/YY HH:MM:SS) to Request Time format (YYYY/DDD/HH:MM:SS)
 # 
 # Params:
 #   EphTime: in, required, type = datetime object
 #   datetime object containing the date and time to be reformatted
 #
 #   ReqTime: out, required, type = string
 #   string containing the reformatted date and time 
 
 # Define input EphTime format string
  ArcEph_fmt = '%m/%d/%y %H:%M:%S'
  
 # Define output ReqTime format string
  ReqTime_fmt = '%Y/%j/%H:%M:%S'
  
 # Declare a datetime object of ArcEph_fmt datetime format
  dt = datetime.datetime.strptime(EphTime, ArcEph_fmt)
 
 # Strip the dt datetime object in the ReqTime_fmt format
  ReqTime = dt.strftime(ReqTime_fmt)
  
 # Return the reformatted date and time string 
  return ReqTime

def ReqFmt(buffFC_in, buffOrbNum):

 # Inserts converted request times to new ReqTime field using arcpy update cursors.
 # Also reorders MYD H:M:S format so request times are easier to find in the feature class
 # "Start_Time" field will be deleted outside of this function.
 # 
 # Params:
 #   buffFC_in: in, required, type = string
 #   string containing the path to the feature class being processed
 #
 #   buffOrbNum: in, required, type = string
 #   string containing the current orbit of the buffer feature classes being processed
 #
 
 # Declare array of field names to be referenced by the arcpy update cursor
  fields = ["Start_Time", "OrbitNum", "ReqTime", "MDYTime"]
  
 # Instantiate arcpy update cursor using the input buffer feature class and the referenced fields
  with arcpy.da.UpdateCursor(buffFC_in, fields) as cursor:
  
    for row in cursor:                     # Loop through each row of the cursor in the feature class
    
      row[1] = "Orbit " + buffOrbNum       # Give an orbit name to the "OrbitNum" field
      
      row[2] = ConvertEphTime(row[0])      # Convert the ephemeris time found in "Start_Time" field and write to "ReqTime"
      
      row[3] = row[0]                      # Copy "Start_Time" to "MDYTime" to reorder
      
      cursor.updateRow(row)
      
  return

def ExportLines(procDir):

# Exports time-enabled polylines from each point-arc ephemeris feature class in the MXX_Processed_Orbits\Arc" directory
# 
# Params:
#   procDir: in, required, type = string
#   string containing the path to the processing directory
#

# Set arc-point input directory within processing directory
  arcDir_in = glob.glob(procDir + r'\Arc\*.shp')
  
# Set line output directory within processing directory
  lineDir_out = procDir + r'\Line'
  
# Create line output directory if nonexistent
  if not os.path.isdir(lineDir_out):
    os.makedirs(lineDir_out)
   
# Loop for each feature class in the arc-point directory
  for arcFC in arcDir_in:
  
# Strip orbit number integer current arc-point feature class
    arcOrbNum = int(arcFC[-12:-8])

# Set arcpy time-enabled polyline function parameters
    outLineFC = lineDir_out + r'\orb' + str(arcOrbNum).zfill(4) + "_line.shp"
    time_field = "TA_DATE"
    distance_field_units = "KILOMETERS"
    distance_field_name = "D_KM"
    duration_field_units = "SECONDS"
    duration_field_name = "DURATION"
    speed_field_units = "KILOMETERS_PER_HOUR"
    speed_field_name = "SPP_KM_H"
    course_field_units = "DEGREES"
    course_field_name = "HEADING"
  
# Convert arc-point shapes from current feature class to time-enabled polylines
    arcpy.TrackIntervalsToLine_ta(arcFC, outLineFC, time_field, "", "", "", "", "",
                                  distance_field_units,   distance_field_name,
                                  duration_field_units,   duration_field_name,
                                  speed_field_units,      speed_field_name,
                                  course_field_units,     course_field_name)
    #arcOrbNum += 1
    
  return

def BufferFOV(procDir, SwapLens):

# 
# Converts time-enabled polyline features to buffered polygon feature classes
# 
# Params:
#   procDir: in, required, type = string
#   string containing the path to the processing directory
# 
#   SwapLens: in, required, type = integer
#   index of the lens swap orbit
#

# Set polyline input directory within processing directory
  lineDir_in = glob.glob(procDir + r'\Line\*.shp')
  
# Set buffer output directory within processing directory
  buffDir_out = procDir + r'\Buff'
  
# Create line output directory if nonexistent
  if not os.path.isdir(buffDir_out):
    os.makedirs(buffDir_out)
 
 # Loop for each feature class in the polylines directory
  for lineFC in lineDir_in:             
  
 # Strip current orbit number from current feature class
    current = int(lineFC[-13:-9])       
    
    if current <= SwapLens:

# Set buffer distance for pre-lens swap cases
      buffDist = "56 Kilometers"
      
    else:
    
# Set buffer distance for post-lens swap cases
      buffDist = "17 Kilometers"
      
# Convert polyline feature class to a buffered polygons  
    buff = arcpy.Buffer_analysis(in_features=lineFC,
                      out_feature_class= buffDir_out + '\orb' + str(current).zfill(4) + '_buff.shp',
                      buffer_distance_or_field=buffDist,
                      line_side="FULL",
                      line_end_type="FLAT",
                      dissolve_option="LIST",
                      dissolve_field=["Start_Time"],
                      method="PLANAR")

  return

def FormatBuffer(procDir):

# Reformats buffered polygon feature classes to display request formatted times and orbit numbers
# 
# Params:
#
#   procDir: in, required, type = string
#   string containing the path to the processing directory
#

# Set buffer polygon input directory within processing directory
  BuffDir_in = glob.glob(procDir + r'\Buff\*.shp')

# Loop for each feature class in buffer directory
  for BuffFC in BuffDir_in:
  
# Strip orbit number string from current ceature class
    buffOrbNum = BuffFC[-13:-9]
    
# Add "OrbitNum" field to buffer feature class using arcpy
    arcpy.AddField_management(BuffFC, "OrbitNum", "STRING")

# Add "ReqTime" field to buffer feature class using arcpy    
    arcpy.AddField_management(BuffFC, "ReqTime", "STRING")
    
# Add "MDYTime" field to buffer feature class using arcpy
    arcpy.AddField_management(BuffFC, "MDYTime", "STRING")

# Convert date time string found in "Start_Time" field to request format
    ReqFmt(BuffFC, buffOrbNum)

# Delete "Start_Time" field using arcpy (This data has now been moved to "MDYTime")
    arcpy.DeleteField_management(BuffFC, ["Start_Time"])
      
  return

#  ************************************ Main level loop ******************************************

ExportLines(procDir)

BufferFOV(procDir, SwapLens)

FormatBuffer(procDir)