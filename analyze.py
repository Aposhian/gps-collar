"""
analyze.py

Originally written for Python 3.6.7

For calculating the distance between GPS coordinates at particular sampling intervals
The data is sourced from a .csv file

@author: Adam Aposhian

This script expects at least two commandline arguments:

python3 analyze.py [inputCSVfilepath] [numberofintervals] [optional:-v/--verbose]

"""

import csv
import sys
import time
import datetime
from math import sqrt, pow
from shapely.geometry import Polygon, Point, MultiPoint, LineString
#from matplotlib import pyplot


# CHECK PYTHON VERSION



if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")



# CONSTANTS



SAMPLE_FREQUENCY = 30*60 # seconds
SAMPLE_FREQUENCY_TOLERANCE = 5*60 # seconds
assert SAMPLE_FREQUENCY_TOLERANCE >= 0
# This means there will be at least INTERVAL - TOLERANCE minutes between datapoints



# PROCESS COMMAND LINE ARGUMENTS



try:
    inputfilepath = sys.argv[1]
except IndexError:
    raise IndexError('You must specify the file path of the csv file to target')

try:
    NUMBER_OF_INTERVALS = int(sys.argv[2])
    assert 1 <= NUMBER_OF_INTERVALS <= 24 # I will disallow intervals smaller than an hour
except (IndexError, AssertionError):
    raise AssertionError('You must specify a number of intervals between 1 and 24 in the command line arguments')

# Calculate the interval boundaries (in minutes)
LENGTH_OF_DAY_IN_SECONDS = 24*3600 # 24 hours * 3600 seconds per hour
INTERVAL_LENGTH_IN_SECONDS = (24 / NUMBER_OF_INTERVALS)*3600


# HELPER FUNCTIONS


def getDatetime(row):
    """
    Returns datetime.datetime object generated from data in the row
    """
    date = (datetime.datetime.strptime(row['Date_Time'], "%Y-%m-%d")).date()
    # Assuming secondTimestamp is in seconds from midnight of the day before
    return datetime.datetime.combine( date, datetime.time(int(row['Hour']), int(row['Minute'])) )

def isInSameInterval(datetime1, datetime2):
    """
    Returns true if the datetime.datetime objects are in the same interval
    """
    if datetime1.date() != datetime2.date():
        return False
    else:
        return isInWhatInterval(datetime1) == isInWhatInterval(datetime2)

def isInWhatInterval(datetime1):
    """
    Returns the index of the interval in which the minuteTimestamp falls
    """
    return int( ( (datetime1.hour * 3600) + (datetime1.minute * 60) + datetime1.second ) // INTERVAL_LENGTH_IN_SECONDS )

def getIntervalStart(datetime1):
    t = getTime(INTERVAL_LENGTH_IN_SECONDS*isInWhatInterval(datetime1))
    d = datetime1.date()
    return datetime.datetime.combine(d,t)

def getTime(seconds):
    hour = int(seconds // 3600)
    minute = int((seconds % 3600) // 60)
    second = int((seconds % 60))
    return datetime.time(hour,minute,second)

def getPoint(row):
    return ( (float(row['X_UTM']), float(row['Y_UTM'])) )

def getMaxDisplacement(listofPoints):
    # There should be a more efficient way to do this
    maxDistance = 0
    for point1 in listofPoints:
        for point2 in listofPoints:
            length = LineString((point1,point2)).length
            if length > maxDistance:
                maxDistance = length
    return maxDistance

def areInAdjacentIntervals(datetime1,datetime2):
    assert datetime1 < datetime2, 'datetime1 should come before datetime2'
    interval1 = isInWhatInterval(datetime1)
    interval2 = isInWhatInterval(datetime2)

    adjacentWithinDay = datetime1.date() == datetime2.date() and \
        abs( isInWhatInterval(datetime1) - isInWhatInterval(datetime2) ) <= 1

    lastAndFirst = ( datetime1.date() + datetime.timedelta(days=1) ) == datetime2.date() and \
        interval1 == NUMBER_OF_INTERVALS - 1 and \
        interval2 == 0
    
    return adjacentWithinDay or lastAndFirst

# MAIN SCRIPT

if inputfilepath.find('AS') != -1:
    SPAY = 'A'
elif inputfilepath.find('BS') != -1:
    SPAY = 'B'
else:
    SPAY = 'N'

# Replace "/original" with "/output" and append "_out" to the end of the filename (but before the extension)
outputfilepath = inputfilepath.replace('/original','/output').replace('.csv','_out.csv')

with open(inputfilepath, 'r', newline='') as inputCSVfile, \
    open(outputfilepath, 'w', newline='') as outputCSVfile, \
    open(inputfilepath + '_logfile.txt', 'w') as logfile:
    # DictReader will use the first row to name the fields
    reader = csv.DictReader(inputCSVfile)

    # Start the output file
    fieldnames = ['HorseID', 'Date', 'Interval', 'StartTime', 'EndTime', 'Distance', 'Area', 'MaxDisplacement','Spay']
    writer = csv.DictWriter(outputCSVfile, fieldnames=fieldnames)
    writer.writeheader()

    # Get the first row
    previousRow = reader.__next__()
    thisHorse = previousRow['HorseID']
    startDatetime = getDatetime(previousRow)
    previousDatetime = startDatetime
    previousPoint = getPoint(previousRow)

    # Store rows to write until all datapoints are confirmed
    # (Sequence of Dictionaries)
    rowsToWrite = []

    # Store all the coordinates for an interval
    intervalPoints = []
    # Loop until all rows have been read
    while True:
        try:
            currentRow = reader.__next__()
        except StopIteration:
            # We got to the end!
            if len(intervalPoints) >= 2:
                logfile.write((previousDatetime.date()).isoformat() + ': ' + str((LineString(intervalPoints)).length) + ' meters\n')
                # Write data for the last interval
                rowsToWrite.append({'HorseID': thisHorse, \
                    'Date': (startDatetime.date()).isoformat(), \
                    'Interval': isInWhatInterval(startDatetime), \
                    'StartTime': (startDatetime.time()).isoformat(timespec='minutes'), \
                    'EndTime': (previousDatetime.time()).isoformat(timespec='minutes'), \
                    'Distance': (LineString(intervalPoints)).length, \
                    'Area': ((MultiPoint(intervalPoints)).convex_hull).area, \
                    'MaxDisplacement': getMaxDisplacement(intervalPoints), \
                    'Spay': SPAY})
                # For debug only
                #pyplot.scatter(*zip(*intervalPoints))
                #pyplot.show()

                # Reject a day if it does not have all intervals represented
                if len(rowsToWrite) == NUMBER_OF_INTERVALS:
                    for row in rowsToWrite:
                        writer.writerow(row)
                else:
                    logfile.write('Insufficient number of intervals on ' + (previousDatetime.date()).isoformat() + '\n')
                rowsToWrite.clear()

            else:
                logfile.write('Insufficient number of datapoints on ' + (startDatetime.date()).isoformat() + ' Interval ' + str(isInWhatInterval(startDatetime)) + '\n')            
            break # Exit the loop
        
        currentDatetime = getDatetime(currentRow) # This won't execute when it gets to the end of the file
        assert currentDatetime > previousDatetime, "Dates are not in sequential order at " + currentDatetime.isoformat()
        currentPoint = getPoint(currentRow)
        assert currentRow['HorseID'] == previousRow['HorseID'], "There is more than one horse in this file"

        if previousDatetime.date() == currentDatetime.date() and isInSameInterval(startDatetime, currentDatetime):
            # Only use this datapoint if it is in the desired sampling frequency
            if (currentDatetime - previousDatetime).total_seconds() > (SAMPLE_FREQUENCY - SAMPLE_FREQUENCY_TOLERANCE):
                intervalPoints.append(currentPoint)
                logfile.write('Calculating distance from ' + previousDatetime.isoformat() + ' to ' + currentDatetime.isoformat() + '\n')
            else:
                # Keep the same previous row (don't do the assignment at the end of the loop)
                continue
        else:
            # We are done calculating distance for the last set
            logfile.write('Found datapoint in new interval\n')
            # Throw out data for intervals that don't have enough datapoints
            # I will take the distance from the last point of interval one to the first point of interval two
            # and add that distance to interval one
            # Restrict the merging to be between two intervals
            intermediate_point = None
            if areInAdjacentIntervals(previousDatetime, currentDatetime):
                logfile.write('boundary: ' + str((getIntervalStart(currentDatetime)).isoformat()) + '\n')
                logfile.write('currentDatetime: ' + str(currentDatetime.isoformat()) + '\n')
                logfile.write('previousDatetime: ' + str(previousDatetime.isoformat()) + '\n')
        
                proportion_to_midpoint = (getIntervalStart(currentDatetime) - previousDatetime) / (currentDatetime - previousDatetime)
                assert 0 <= proportion_to_midpoint <= 1, "Intermediate point calculation error at " + previousDatetime.isoformat()
                
                x = previousPoint[0] + proportion_to_midpoint*(currentPoint[0] - previousPoint[0])
                y = previousPoint[1] + proportion_to_midpoint*(currentPoint[1] - previousPoint[1])
                intermediate_point = (x,y)
                intervalPoints.append(intermediate_point)
                logfile.write('Adding ' + str(proportion_to_midpoint) +' to first interval\n')
            else:
                logfile.write('Too large a gap to add distance to next interval\n')
            
            if len(intervalPoints) >= 2:
                rowsToWrite.append({'HorseID': thisHorse, \
                    'Date': (startDatetime.date()).isoformat(), \
                    'Interval': isInWhatInterval(startDatetime), \
                    'StartTime': (startDatetime.time()).isoformat(timespec='minutes'), \
                    'EndTime': (currentDatetime.time()).isoformat(timespec='minutes'), \
                    'Distance': (LineString(intervalPoints)).length, \
                    'Area': ((MultiPoint(intervalPoints)).convex_hull).area, \
                    'MaxDisplacement': getMaxDisplacement(intervalPoints), \
                    'Spay': SPAY})
                # For debug only
                #pyplot.scatter(*zip(*intervalPoints))
                #pyplot.show()

                logfile.write((previousDatetime.date()).isoformat() + ': ' + str((LineString(intervalPoints)).length) + ' meters\n') #debug
            else:
                logfile.write('Insufficient datapoints on ' + (startDatetime.date()).isoformat() + ' Interval ' + str(isInWhatInterval(startDatetime)) + ' - rejecting interval\n')            
            # Only write datapoints for the day if all intervals are present
            if previousDatetime.date() != currentDatetime.date():
                # Reject a day if it does not have all intervals represented
                if len(rowsToWrite) == NUMBER_OF_INTERVALS:
                    for row in rowsToWrite:
                        writer.writerow(row)
                else:
                    logfile.write('Insufficient intervals on ' + (previousDatetime.date()).isoformat() + ' - rejecting day\n')
                rowsToWrite.clear()
            
            # Now we will start a new interval
            startDatetime = currentDatetime
            intervalPoints.clear()
            if intermediate_point != None:
                intervalPoints.append(intermediate_point)

        previousRow = currentRow
        previousDatetime = currentDatetime
        previousPoint = currentPoint
