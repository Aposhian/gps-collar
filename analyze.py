import csv
import sys
from math import sqrt, pow

SAMPLE_FREQUENCY = 30 # minutes
SAMPLE_FREQUENCY_TOLERANCE = 5 # minutes

INTERVAL_LENGTH = 6 # hours


# This means there will be at least INTERVAL - TOLERANCE minutes between datapoints

inputfilepath = 'csv/original/Horse004.csv' #sys.argv[1]

# Enabling VERBOSE mode will enable the print statements
VERBOSE = None
"""
try:
    if sys.argv[2] == '-v' or sys.argv[2] == '--verbose':
        VERBOSE = True
    else:
        VERBOSE = False
except:
    VERBOSE = False
    pass
"""
def calculateDistance(previousRow, row):
    if VERBOSE:
        print('Using ' + previousRow['Date_Time'] + ': ' + previousRow['Hour'] + ' hours ' + previousRow['Minute'] + ' minutes' \
            + '\n\tand '+ row['Date_Time'] + ': ' + row['Hour'] + ' hours ' + row['Minute'] + ' minutes') #debug

    return sqrt(pow( float(previousRow['X_UTM']) - float(row['X_UTM']), 2 ) + pow( float(previousRow['Y_UTM']) - float(row['Y_UTM']), 2))

def calculateTimeStamp(row):
    # Assuming timestamp is in minutes
    return int(row['Hour'])*60 + int(row['Minute'])

def getHour(timestamp):
    # Assuming timestamp is in minutes
    return timestamp / 60

def isInInterval(startIntervalTime, row):
    return (startIntervalTime + INTERVAL_LENGTH*60) >= calculateTimeStamp(row)

# Replace "/original" with "/output" and append "_out" to the end of the filename (but before the extension)
outputfilepath = inputfilepath.replace('/original','/output').replace('.csv','_out.csv')

with open(inputfilepath, 'r', newline='') as csvfile, open(outputfilepath, 'w', newline='') as outputfile:
    # DictReader will use the first row to name the fields
    reader = csv.DictReader(csvfile)

    # Start the output file
    fieldnames = ['HorseID', 'Date', 'StartHour', 'EndHour', 'Distance']
    writer = csv.DictWriter(outputfile, fieldnames=fieldnames)
    writer.writeheader()

    # Get the first datapoint
    previousRow = reader.__next__()
    distance = 0
    thisHorse = previousRow['HorseID']
    thisDay = previousRow['Date_Time']
    startIntervalTime = calculateTimeStamp(previousRow)
    previousTime = startIntervalTime

    while True:
        try:
            currentRow = reader.__next__()
            currentTime = calculateTimeStamp(currentRow) # This won't execute when it gets to the end of the file
        except StopIteration:
            # We got to the end!
            if VERBOSE:
                print(thisDay + ': ' + str(distance) + ' meters\n') #debug

            writer.writerow({'HorseID': thisHorse, 'Date': thisDay, 'StartHour': getHour(startIntervalTime), 'EndHour': getHour(previousTime), 'Distance': distance})
            break
        
        assert currentRow['HorseID'] == previousRow['HorseID'] # Here I am forcing there to be only one horse per file

        if isInInterval(startIntervalTime, currentRow):
            # Only use this datapoint if it is in the desired sampling frequency
            if abs( int(currentRow['Minute']) - int(previousRow['Minute']) ) > (SAMPLE_FREQUENCY - SAMPLE_FREQUENCY_TOLERANCE):
                # Application of Pythagorean Theorem
                distance += calculateDistance(previousRow, currentRow)
            else:
                # Keep the same previous row (don't do the assignment at the end of the loop)
                continue
        else:
            # We are done calculating distance for the last set

            # I will take the distance from the last point of interval one to the first point of interval two
            # and add that distance to interval one
            distance += calculateDistance(previousRow, currentRow)

            writer.writerow({'HorseID': thisHorse, 'Date': thisDay, 'StartHour': getHour(startIntervalTime), 'EndHour': getHour(currentTime), 'Distance': distance})

            if VERBOSE:
                print(thisDay + ': ' + str(distance) + ' meters\n') #debug

            # Now we will start a new interval
            distance = 0
            startIntervalTime = calculateTimeStamp(currentRow)
            # If we want to divide the distance between the intervals, use this code:
                #lastDistance = calculateDistance(previousRow, row) / 2 # Split the distance between the days
                #distance = lastdistance
            thisHorse = currentRow['HorseID']
            thisDay = currentRow['Date_Time']

        previousRow = currentRow
        previousTime = calculateTimeStamp(previousRow)
