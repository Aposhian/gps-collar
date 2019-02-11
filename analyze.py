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
INTERVAL_LENGTH_IN_SECONDS = int((24 / NUMBER_OF_INTERVALS)*3600)
INTERVALS = list(range(0, LENGTH_OF_DAY_IN_SECONDS, INTERVAL_LENGTH_IN_SECONDS)) # Timestamps of interval starts
MINIMUM_DATAPOINTS_PER_INTERVAL = 1 #( INTERVAL_LENGTH_IN_SECONDS // (SAMPLE_FREQUENCY) ) // 2 # It will be accepted if it has at least half the datapoints


# HELPER FUNCTIONS



# Beginning in Python 3.7 can use datetime.date.fromisoformat(YYYY-MM-DD)
def convertDateToUnixTimestamp(date_string):
    """
    Converts a date formatted in YYYY-MM-DD to a Unix timestamp,
    or the number of seconds passed since 1 Jan 1970 12:00 AM in the current timezone
    THIS ASSUMES THE DATE GIVEN IS IN THE TIMEZONE THAT THE PROGRAM IS RUN IN
    because of this, these timestamps are only relative, and should not be exported
    """
    assert len(date_string) == 10 # Format YYYY-MM-DD
    return int(datetime.datetime.strptime(date_string, "%Y-%m-%d").timestamp())

def getDatetime(row):
    """
    Returns datetime.datetime object generated from data in the row
    """
    dateSeconds = convertDateToUnixTimestamp(row['Date_Time'])
    # Assuming secondTimestamp is in seconds from midnight of the day before
    return datetime.datetime.fromtimestamp(dateSeconds + int(row['Hour'])*3600 + int(row['Minute'])*60)

def isInSameInterval(datetime1, datetime2):
    """
    Returns true if the datetime.datetime objects are in the same interval
    """
    if datetime1.date() != datetime2.date():
        return False
    else:
        return isInWhatInterval(datetime1) == isInWhatInterval(datetime2)

def isInWhatInterval(datetime):
    """
    Returns the index of the interval in which the minuteTimestamp falls
    """
    return ( (datetime.hour * 3600) + (datetime.minute * 60) + datetime.second ) // INTERVAL_LENGTH_IN_SECONDS

def getIntervalStart(middleDatetime):
    return datetime.datetime.fromtimestamp(convertDateToUnixTimestamp((middleDatetime.date()).isoformat()) + INTERVALS[isInWhatInterval(middleDatetime)])

def getPoint(row):
    return Point( (float(row['X_UTM']), float(row['Y_UTM'])) )

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
    fieldnames = ['HorseID', 'Date', 'Interval', 'StartTime', 'EndTime', 'Distance', 'Spay']
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
                    'Spay': SPAY})
            else:
                logfile.write('Insufficient number of datapoints on ' + (startDatetime.date()).isoformat() + ' Interval ' + str(isInWhatInterval(startDatetime)) + '\n')            
            break # Exit the loop
        
        currentDatetime = getDatetime(currentRow) # This won't execute when it gets to the end of the file
        currentPoint = getPoint(currentRow)
        assert currentRow['HorseID'] == previousRow['HorseID'] # Here I am forcing there to be only one horse per file

        if previousDatetime.date() == currentDatetime.date() and isInSameInterval(startDatetime, currentDatetime):
            # assert currentDatetime.timestamp() > previousDatetime.timestamp()
            # Only use this datapoint if it is in the desired sampling frequency
            if (currentDatetime - previousDatetime).total_seconds() > (SAMPLE_FREQUENCY - SAMPLE_FREQUENCY_TOLERANCE):
                intervalPoints.append(currentPoint)
                logfile.write('Calculating distance for ' + previousRow['Date_Time'] + ': ' + previousRow['Hour'] + ' hours ' + previousRow['Minute'] + ' minutes' \
                    + '\n\tand '+ currentRow['Date_Time'] + ': ' + currentRow['Hour'] + ' hours ' + currentRow['Minute'] + ' minutes\n')
            else:
                # Keep the same previous row (don't do the assignment at the end of the loop)
                continue
        else:
            # We are done calculating distance for the last set

            # Throw out data for intervals that don't have enough datapoints
            #if numberOfDatapoints >= MINIMUM_DATAPOINTS_PER_INTERVAL:
            # I will take the distance from the last point of interval one to the first point of interval two
            # and add that distance to interval one
            # Restrict the merging to be between two intervals
            intermediate_point = None
            if (getIntervalStart(currentDatetime) - previousDatetime).total_seconds() <= INTERVAL_LENGTH_IN_SECONDS:
                logfile.write('boundary: ' + str(getIntervalStart(currentDatetime).timestamp()) + '\n')
                logfile.write('currentDatetime: ' + str(currentDatetime.timestamp()) + '\n')
                logfile.write('previousDatetime: ' + str(previousDatetime.timestamp()) + '\n')
        
                proportion_to_midpoint = (getIntervalStart(currentDatetime) - previousDatetime) / (currentDatetime - previousDatetime)
                
                x = previousPoint.x + proportion_to_midpoint*(currentPoint.x - previousPoint.x)
                y = previousPoint.y + proportion_to_midpoint*(currentPoint.y - previousPoint.y)
                intermediate_point = Point( (x,y) )
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
                    'Spay': SPAY})

                logfile.write((previousDatetime.date()).isoformat() + ': ' + str((LineString(intervalPoints)).length) + ' meters\n') #debug
            else:
                logfile.write('Insufficient number of datapoints on ' + (startDatetime.date()).isoformat() + ' Interval ' + str(isInWhatInterval(startDatetime)) + '\n')            
            # Only write datapoints for the day if all intervals are present
            if previousDatetime.date() != currentDatetime.date():
                # Reject a day if it does not have all intervals represented
                if len(rowsToWrite) == NUMBER_OF_INTERVALS:
                    for row in rowsToWrite:
                        writer.writerow(row)
                else:
                    logfile.write('Insufficient number of intervals on ' + (previousDatetime.date()).isoformat() + '\n')
                rowsToWrite.clear()
            
            # Now we will start a new interval
            startDatetime = currentDatetime
            intervalPoints.clear()
            if intermediate_point != None:
                intervalPoints.append(intermediate_point)

        previousRow = currentRow
        previousDatetime = currentDatetime
        previousPoint = currentPoint
