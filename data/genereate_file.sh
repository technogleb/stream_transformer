#!/usr/bin/env bash
for i in {1..30}; do cat file.txt file.txt > file2.txt && mv file2.txt file.txt; done
