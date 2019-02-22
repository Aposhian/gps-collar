#!/bin/bash

# Test code
# exit on non-zero exit code from test case
python3 analyze.py test/test.csv 6

cmp test/test_out.csv test/expected.csv -s

if test $? -ne 0
then
        echo "Failed test case found in test/test.csv"
	exit 1
else
        echo "All tests passed"
	rm test/test_out.csv
	rm test/test.csv_logfile.txt
fi

# Main code

# Specify how many intervals to split each day into
NUMBER_OF_INTERVALS=6 # Default to 6 intervals

for filename in ../PWS/csv/original/*.csv; do
	echo "Calculating data for $filename"
	python3 analyze.py "$filename" $NUMBER_OF_INTERVALS
done
echo "Zipping output csv files together"
zip ../PWS/outputs.zip ../PWS/csv/output/*_out.csv -q
echo "Creating combined csv file"
./combinecsv.sh
echo "Done"
