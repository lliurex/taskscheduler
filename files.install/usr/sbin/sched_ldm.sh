#!/bin/bash
#Script that executes a task last day of month
#Input: task to execute
first_day=$(date "+%Y%m01")
last_day=$(date -d "$firstday + 1 month - 1 day" +%Y%m%d)
today=$(date "+%Y%m%d")
[[ $last_day -eq $today ]] && $@
