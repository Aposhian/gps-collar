#!/bin/bash
for filename in ../PWS/csv/original/*.csv; do
	python3 analyze.py "$filename"
done
zip ../PWS/outputs.zip ../PWS/csv/output/*_out.csv
./combinecsv.sh
