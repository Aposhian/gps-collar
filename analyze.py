import csv
import sys
from math import sqrt, pow

inputfilepath = sys.argv[1]

outputfilepath = inputfilepath[:inputfilepath.find('.csv')] + '_out' + inputfilepath[inputfilepath.find('.csv'):]

with open(inputfilepath, 'r', newline='') as csvfile, open(outputfilepath, 'w', newline='') as outputfile:
    reader = csv.DictReader(csvfile)
    fieldnames = ['HorseID', 'Date_Time', 'Distance']
    writer = csv.DictWriter(outputfile, fieldnames=fieldnames)
    writer.writeheader()
    # DictReader will use the first row to name the fields
    previousRow = reader.__next__()
    distance = 0
    thisHorse = previousRow['HorseID']
    thisDay = previousRow['Date_Time']
    while True:
        try:
            row = reader.__next__()
        except StopIteration:
            # We got to the end!
            break
        if row['HorseID'] != thisHorse or row['Date_Time'] != thisDay:
            # We are done calculating distance for the last set
            # print(thisDay + ': ' + str(distance))
            writer.writerow({'HorseID': thisHorse, 'Date_Time': thisDay, 'Distance': distance})
            # Now we will start a new set
            distance = 0
            thisHorse = row['HorseID']
            thisDay = row['Date_Time']
        else:
            distance += sqrt(pow( float(previousRow['X_UTM']) - float(row['X_UTM']), 2 ) + pow( float(previousRow['Y_UTM']) - float(row['Y_UTM']), 2))
        # do stuff
        previousRow = row