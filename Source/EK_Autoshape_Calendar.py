 # EarthKAM AutoShape Calendar Tool
 # EK_Autoshape_Calendar.py
 # Tim Klug


import arcgisscripting

import csv
import glob
import sys
import os
import time
import string
import datetime
from arcpy import env

arcpy.env.overwriteOutput = True

gp = arcgisscripting.create(9.3)


 # 
 # This file consists of two functions and a main level program designed to be run as an ArcGIS python tool.
 # These functions are designed to read and input csv file containing subpoint lighting intervals for the ISS
 # during EarthKAM missions. The first function reads the input csv file and returns the lighting interval 
 # times as a tuple of datetime object arrays. The second function reformats these datetime objects and outputs
 # them to a format compatible with Google Calendar's import csv feature. See attached documentation for input
 # csv format requirements.
 #
 # Author: 
 #   Tim Klug
 #
 # History:
 #   tklug, March 23, 2017: script exported as ArcGIS python tool
 #


 # set parameters in ArcGIS python tool

inCSV = gp.GetParameterAsText(0)

baseOrbitNum = gp.GetParameterAsText(1)

calCSV = gp.GetParameterAsText(2)


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

def export_gCal(calCSV, startTimes, endTimes, current):

 # Export subpoint lighting times to an output csv file to be used for 
 # importing orbit times to Google Calendar.
 #
 # Params:
 #   calCSV: in, required, type = string
 #   path to the output csv file containing orbit lighting intervals in Google Calendar format
 #
 #   startTimes: in, required, type = datetime array
 #   array of subpoint lighting start times retrieved from input csv
 #
 #   endTimes: in, required, type = datetime array
 #   array of subpoint lighting end times retrieved from input csv
 #
 #   current: in, required, type = integer
 #   integer storing value of current orbit number being iterated processed
 #
 

# Specify date and time formats for output
  date_fmt = '%m/%d/%Y'                                                      
  
  time_fmt = '%H:%M:%S'
  
  with open(calCSV, 'wb') as csvfile:
  
    csvfile.write("Subject,Start Date,Start Time,End Date,End Time\n")       # Write column headers to csv output
    
    for i, val in enumerate(startTimes):                                     # Non-pythonic loop. Sue me.
    
      csvfile.write('Orbit ' + str(current) + ',' \                          # Output each line corresponding to subpoint lighting times from input csv
                    + startTimes[i].strftime(date_fmt)+ ',' \
                    + startTimes[i].strftime(time_fmt)+ ',' \
                    + endTimes[i].strftime(date_fmt)+ ',' \
                    + endTimes[i].strftime(time_fmt)+ '\n')
                    
      current += 1                                                           # Iterate current orbit number and loop index
      
      i += 1
      
  return

## Main level program ##

 # Define start and end datetime object arrays for subpoint lighting intervals
startTimes = []
endTimes = []

# Assign tuple of dto arrays to output of ReadCSV()
(startTimes,endTimes) = ReadCSV(inCSV)

# Export Google Calendar csv input file using formatted lighting interval times
export_gCal(calCSV, startTimes, endTimes, baseOrbitNum)




