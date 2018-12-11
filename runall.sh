#!/bin/bash
for filename in ../PWS/csv/*.csv; do
	python3 analyze.py "$filename"
done
