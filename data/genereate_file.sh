#!/usr/bin/env bash
cp test_file file.txt
for i in {1..25}; do cat file.txt file.txt > file2.txt && mv file2.txt file.txt; done
