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



# CHECK PYTHON VERSION



if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")



# CONSTANTS



SAMPLE_FREQUENCY = 30 # minutes
SAMPLE_FREQUENCY_TOLERANCE = 5 # minutes
assert SAMPLE_FREQUENCY_TOLERANCE >= 0
# This means there will be at least INTERVAL - TOLERANCE minutes between datapoints
MINIMUM_DATAPOINTS_PER_INTERVAL = 2



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
INTERVALS = list(range(0, LENGTH_OF_DAY_IN_SECONDS, INTERVAL_LENGTH_IN_SECONDS))



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

def calculateDistance(previousRow, row):
    """
    Returns distance in meters between the UTM coordinates in two rows
    """
    # Distance formula or Pythagorean Theorem
    return sqrt(pow( float(previousRow['X_UTM']) - float(row['X_UTM']), 2 ) + pow( float(previousRow['Y_UTM']) - float(row['Y_UTM']), 2))

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



# MAIN SCRIPT



# Replace "/original" with "/output" and append "_out" to the end of the filename (but before the extension)
outputfilepath = inputfilepath.replace('/original','/output').replace('.csv','_out.csv')

with open(inputfilepath, 'r', newline='') as inputCSVfile, \
    open(outputfilepath, 'w', newline='') as outputCSVfile, \
    open(inputfilepath + '_logfile.txt', 'w') as logfile:
    # DictReader will use the first row to name the fields
    reader = csv.DictReader(inputCSVfile)

    # Start the output file
    fieldnames = ['HorseID', 'Date', 'Interval', 'StartTime', 'EndTime', 'Distance']
    writer = csv.DictWriter(outputCSVfile, fieldnames=fieldnames)
    writer.writeheader()

    # Get the first row
    previousRow = reader.__next__()
    distance = 0
    thisHorse = previousRow['HorseID']
    startDatetime = getDatetime(previousRow)
    previousDatetime = startDatetime
    currentInterval = isInWhatInterval(previousDatetime)
    numberOfDatapoints = 1 # We just counted the first one

    # Loop until all rows have been read
    while True:
        try:
            currentRow = reader.__next__()
            numberOfDatapoints += 1
            currentDatetime = getDatetime(currentRow) # This won't execute when it gets to the end of the file
        except StopIteration:
            # We got to the end!
            logfile.write((previousDatetime.date()).isoformat() + ': ' + str(distance) + ' meters\n')

            # Write data for the last interval
            writer.writerow({'HorseID': thisHorse, 'Date': (startDatetime.date()).isoformat(), 'Interval': isInWhatInterval(startDatetime),'StartTime': (startDatetime.time()).isoformat(timespec='minutes'), 'EndTime': (previousDatetime.time()).isoformat(timespec='minutes'), 'Distance': distance})
            break # Exit the loop
        
        assert currentRow['HorseID'] == previousRow['HorseID'] # Here I am forcing there to be only one horse per file

        if (previousDatetime.date()).isoformat() == currentRow['Date_Time'] and isInSameInterval(startDatetime, currentDatetime):
            # assert currentDatetime.timestamp() > previousDatetime.timestamp()
            # Only use this datapoint if it is in the desired sampling frequency
            if abs( int(currentRow['Minute']) - int(previousRow['Minute']) ) > (SAMPLE_FREQUENCY - SAMPLE_FREQUENCY_TOLERANCE):
                # Application of Pythagorean Theorem
                distance += calculateDistance(previousRow, currentRow)

                logfile.write('Using ' + previousRow['Date_Time'] + ': ' + previousRow['Hour'] + ' hours ' + previousRow['Minute'] + ' minutes' \
                    + '\n\tand '+ currentRow['Date_Time'] + ': ' + currentRow['Hour'] + ' hours ' + currentRow['Minute'] + ' minutes\n')
            else:
                # Keep the same previous row (don't do the assignment at the end of the loop)
                continue
        else:
            # We are done calculating distance for the last set

            # OPTION: throw out data for intervals that don't have enough datapoints
            if numberOfDatapoints >= MINIMUM_DATAPOINTS_PER_INTERVAL:
                # I will take the distance from the last point of interval one to the first point of interval two
                # and add that distance to interval one
                # However, if it is delayed too much then I will not use this datapoint
                distance += calculateDistance(previousRow, currentRow)

                writer.writerow({'HorseID': thisHorse, 'Date': (startDatetime.date()).isoformat(), 'Interval': isInWhatInterval(startDatetime), 'StartTime': (startDatetime.time()).isoformat(timespec='minutes'), 'EndTime': (currentDatetime.time()).isoformat(timespec='minutes'), 'Distance': distance})
 
                logfile.write((previousDatetime.date()).isoformat() + ': ' + str(distance) + ' meters\n') #debug
            else:
                logfile.write('Insufficient number of datapoints on ' + (startDatetime.date()).isoformat() + ' Interval ' + str(currentInterval))
            # Now we will start a new interval
            startDatetime = currentDatetime
            distance = 0
            numberOfDatapoints = 1
            currentInterval = isInWhatInterval(currentDatetime)
            # If we want to divide the distance between the intervals, use this code:
                #lastDistance = calculateDistance(previousRow, row) / 2 # Split the distance between the days
                #distance = lastdistance

        previousRow = currentRow
        previousDatetime = currentDatetime
