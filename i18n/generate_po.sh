#!/bin/bash

PROJECT="taskscheduler"
PYTHON_FILES="../src/*.py ../src/stacks/*.py"

mkdir -p ${PROJECT}

xgettext $PYTHON_FILES -o ${PROJECT}/${PROJECT}.pot

echo "#: qtextrawidgets" >> ${PROJECT}/${PROJECT}.pot
echo 'msgid "'Apply'"' >> ${PROJECT}/${PROJECT}.pot
echo 'msgstr ""'>> ${PROJECT}/${PROJECT}.pot
echo 'msgid "'Undo'"' >> ${PROJECT}/${PROJECT}.pot
echo 'msgstr ""'>> ${PROJECT}/${PROJECT}.pot

