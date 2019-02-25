#!/bin/bash

PYTHON_FILES="../scheduler-gui.install/usr/share/taskscheduler/bin/taskScheduler.py ../python3-taskscheduler.install/usr/share/taskscheduler/*.py ../scheduler-gui.install/usr/share/taskscheduler/bin/detailDateBox.py"
CMD_DIR="../files.install/etc/scheduler/conf.d/commands"
TASKS_DIR="../files.install/etc/scheduler/conf.d/tasks"

mkdir -p taskscheduler/

xgettext $PYTHON_FILES -o taskscheduler/taskscheduler.pot

DIR=$PWD
cd $CMD_DIR
for i in *json
do
	awk -v wrkdir=$DIR -v filename=$CMD_DIR"/"$i '{
	if ($0~":")
	{ 
		outfile=wrkdir"/taskscheduler/taskscheduler.pot"
		printf ("#: %s:%s\n",filename,NR) >> outfile
		split($0,a,":")
		gsub(/\"/,"",a[1])
		gsub(/\t*/,"",a[1])
		printf ("msgid \"%s\"\n",a[1]) >> outfile
		printf("msgstr \"\"\n\n") >> outfile

	}
	}' $i
done
cd $DIR
cd $TASKS_DIR
for i in *json
do
	awk -v wrkdir=$DIR  -v filename=$TASKS_DIR"/"$i '{
	if ($0~":")
	{ 
		outfile=wrkdir"/taskscheduler/taskscheduler.pot"
		printf ("#: %s:%s\n",filename,NR) >> outfile
		split($0,a,":")
		gsub(/\"/,"",a[1])
		gsub(/\t*/,"",a[1])
		printf ("msgid \"%s\"\n",a[1]) >> outfile
		printf("msgstr \"\"\n\n") >> outfile
	}
	}' $i
done
cd $DIR
