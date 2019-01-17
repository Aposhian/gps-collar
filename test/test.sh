#!/bin/bash

python3 ../analyze.py test.csv 6

cmp test_out.csv expected.csv -s

if test $? -ne 0
then
	echo "Failed test case found in test/test.csv"
else
	echo "All tests passed"
fi
