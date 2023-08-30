# TaskScheduler


## Introduction

TaskScheduler aims to be a simple GUI for scheduling tasks on a LliureX system.

## Tasks and jobs

From the gui is possible to manage both cron tasks and at jobs.
AT is the mechanism through a job is executed at a fixed day and hour. Cron is a scheduler for launching jobs at determinated times. For example with at a job runs the 21 of August of present year.With cron a job runs all 21 of August despite the year.

## Add jobs

For adding a new job simpluy go to the add advanced task or the add simple task sections. From there set if is a cron or at job and give the desired dates.

## Modify or remove

Select the job and simply remove it or change desired values

## Inspect jobs from cli

./taskscheduler.py --show

./taskscheduler.py --show-cron

./taskscheduler.py --show-at

## More info

TaskScheduler relies on the python3-taskscheduler python module. See its documentation for available options.
