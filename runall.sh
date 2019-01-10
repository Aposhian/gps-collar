#!/bin/bash

# Test code
# exit on non-zero exit code from test case
# set -e


# Main code
for filename in ../PWS/csv/original/*.csv; do
	python3 analyze.py "$filename" 4 -v
done
zip ../PWS/outputs.zip ../PWS/csv/output/*_out.csv
./combinecsv.sh
