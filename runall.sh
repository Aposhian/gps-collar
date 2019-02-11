#!/bin/bash

# Test code
# exit on non-zero exit code from test case
python3 analyze.py test/test.csv 6

cmp test/test.csv test/expected.csv -s

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
for filename in ../PWS/csv/original/*.csv; do
	echo "Calculating data for $filename"
	python3 analyze.py "$filename" 6 -v
done
echo "Zipping output csv files together"
zip ../PWS/outputs.zip ../PWS/csv/output/*_out.csv -q
echo "Creating combined csv file"
./combinecsv.sh
echo "Done"
