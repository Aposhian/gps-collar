import csv
import sys
from math import sqrt, pow

INTERVAL = 30 # minutes
TOLERANCE = 5 # minutes

# This means there will be at least INTERVAL - TOLERANCE minutes between datapoints

inputfilepath = sys.argv[1]

# Enabling VERBOSE mode will enable the print statements
VERBOSE = None
try:
    if sys.argv[2] == '-v' or sys.argv[2] == '--verbose':
        VERBOSE = True
    else:
        VERBOSE = False
except:
    VERBOSE = False
    pass

# Replace "/original" with "/output" and append "_out" to the end of the filename (but before the extension)

outputfilepath = inputfilepath.replace('/original','/output').replace('.csv','_out.csv')

with open(inputfilepath, 'r', newline='') as csvfile, open(outputfilepath, 'w', newline='') as outputfile:
    # DictReader will use the first row to name the fields
    reader = csv.DictReader(csvfile)

    # Start the output file
    fieldnames = ['HorseID', 'Date_Time', 'Distance']
    writer = csv.DictWriter(outputfile, fieldnames=fieldnames)
    writer.writeheader()

    # Get the first datapoint
    previousRow = reader.__next__()
    distance = 0
    thisHorse = previousRow['HorseID']
    thisDay = previousRow['Date_Time']
    while True:
        try:
            row = reader.__next__()
        except StopIteration:
            # We got to the end!
            if VERBOSE:
                print(thisDay + ': ' + str(distance)) #debug
            writer.writerow({'HorseID': thisHorse, 'Date_Time': thisDay, 'Distance': distance})
            break
        if row['HorseID'] != thisHorse or row['Date_Time'] != thisDay:
            # We are done calculating distance for the last set
            if VERBOSE:
                print(thisDay + ': ' + str(distance) + ' meters\n') #debug
            writer.writerow({'HorseID': thisHorse, 'Date_Time': thisDay, 'Distance': distance})
            # Now we will start a new set
            distance = 0
            thisHorse = row['HorseID']
            thisDay = row['Date_Time']
        else:
            # Only use this datapoint if it is in the desired interval
            if abs( int(row['Minute']) - int(previousRow['Minute']) ) > (INTERVAL - TOLERANCE):
                if VERBOSE:
                    print('Using ' + previousRow['Date_Time'] + ': ' + previousRow['Hour'] + ' hours ' + previousRow['Minute'] + ' minutes' \
                        + '\n\tand '+ row['Date_Time'] + ': ' + row['Hour'] + ' hours ' + row['Minute'] + ' minutes') #debug
                # Application of Pythagorean Theorem
                distance += sqrt(pow( float(previousRow['X_UTM']) - float(row['X_UTM']), 2 ) + pow( float(previousRow['Y_UTM']) - float(row['Y_UTM']), 2))
            else:
                # Keep the same previous row
                continue
        previousRow = row
