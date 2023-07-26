#!/bin/bash

PYTHON_FILES="../src/*.py ../src/stacks/*.py"

mkdir -p taskscheduler/

xgettext $PYTHON_FILES -o taskscheduler/taskscheduler.pot

