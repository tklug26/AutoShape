# EarthKAM Autoshape KML Tool
# EK_Autoshape_KML.py
# Tim Klug

import os
import string
import glob

from arcpy import env
from arcpy import conversion
import arcgisscripting
arcpy.env.overwriteOutput = True

gp = arcgisscripting.create(9.3)

# This file contains one function and one main level program designed to run as an ArcGIS python tool.
# This function is designed to process a directory of buffered polygon shapefiles of ISS orbits during 
# EarthKAM missions. Note: the ArcGIS tool for exporting Google Earth layers refers to KML layers. The
# files actually exported by this tool are of .kmz format. For the purposes of this script, the
# nomenclatures are interchangeable.
#
# Author:
#   Tim Klug
#
# History:
#   tklug, March 23, 2017: script exported as ArcGIS python tool
#


# Set parameters in ArcGIS python tool

# Set main workspace. Should be named "Mission_XX"
arcpy.env.workspace = gp.GetParameterAsText(0)

# Set mission number as a long integer
MissionNum = gp.GetParameter(1)


# set workspace parameters

# Set location of processing directory. All exported outputs will appear here.
#  Should be located at \Mission_XX\MXX_Processed_Orbits
procDir = arcpy.env.workspace + r'\M' + str(MissionNum) + '_Processed_Orbits'


def ExportGoogle(procDir):

# Exports Google Earth .kmz files of buffered orbit polygons to the
# MXX_Processed_Orbits\Google" directory
# 
# Params:
#   procDir: in, required, type = string
#   string containing the path to the processing directory
#

# Set polygon buffer input directory within processing directory
  buffDir_in = glob.glob(procDir + r'\Buff\*.shp')

# Set .kmz output directory within processing directory
  googleDir_out = procDir + r'\Google'

# Create .kmz output directory if nonexistent
  if not os.path.isdir(googleDir_out):
    os.makedirs(googleDir_out)

# Loop for each buffered polygon in input directory
  for buffFC in buffDir_in:
  
# Strip orbit number from current feature class
    current = buffFC[-13:-9]

# Set output file name
    outKMZ = googleDir_out + r'\Orbit_' + current.zfill(4) + ".kmz"

# Create an arcpy mapping layer from current feature class
    lyr = arcpy.mapping.Layer(buffFC)
    
# Use arcpy tool to convert layer to .kmz file
    arcpy.LayerToKML_conversion(lyr, outKMZ)
    
  return

# Ensure preprocessing of ephemeris data has occurred before kmz conversion
if not os.path.isdir(procDir):
  print "ERROR: Please run EK_AUTOSHAPE before exporting KMLs!"
  
# Export kmz files from buffered polylines in processing directory
else:
  ExportGoogle(procDir)