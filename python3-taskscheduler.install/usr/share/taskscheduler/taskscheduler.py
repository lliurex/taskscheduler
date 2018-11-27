#!/usr/bin/env python3
###
#
###
import os
import json
import sys
import collections
import datetime
from operator import itemgetter

try:
	import xmlrpc.client as n4d
except ImportError:
	raise ImportError("xmlrpc not available. Disabling server queries")
import ssl

class TaskScheduler():
	def __init__(self):
		self.dbg=1
		self.credentials=["",""]
		self.n4dserver=None
		self.n4dclient=self._n4d_connect('localhost')
		self.conf_dir="/etc/scheduler/conf.d/"
		self.conf_file="%s/scheduler.conf"%self.conf_dir
		self.tasks_dir=self.conf_dir+'/tasks'
		self.commands_file=self.conf_dir+'/commands/commands.json'
		self.sched_dir="/etc/scheduler/tasks.d"
	#def __init__

	def _debug(self,msg):
		if (self.dbg):
			print("Scheduler lib: %s" % msg)
	#def _debug
	
	def set_credentials(self,user,pwd,server):
		self.credentials=[user,pwd]
		if server!='localhost':
			self.n4dserver=self._n4d_connect(server)
	#def set_credentials

	def read_config(self):
		result=self.n4dclient.read_config("","SchedulerServer")
		return (result['data'])
	#def read_config

	def write_config(self,task,color):
		result=self.n4dclient.write_config(self.credentials,"SchedulerServer",task,color)
		return(result['status'])
	#def write_config

	def get_available_tasks(self):
		tasks={}
		if self.n4dserver:
			result=self.n4dserver.get_available_tasks("","SchedulerServer")
			if type(result)==type({}):
				tasks=result['data'].copy()
		result=self.n4dclient.get_available_tasks("","SchedulerServer")
		if type(result)==type({}):
			tasks.update(result['data'].copy())
		return tasks
	#def get_available_tasks

	def get_scheduled_tasks(self):
		tasks={}
		if self.n4dserver:
			self._debug("Retrieving server task list")
			result=self.n4dserver.get_remote_tasks("","SchedulerServer")['data']
			if type(result)==type({}):
				tasks=result.copy()
		self._debug("Retrieving local task list")
		result=self.n4dclient.get_local_tasks("","SchedulerServer")['data']
		if type(result)==type({}):
			if tasks:
				#Merge values
				for key,data in result.items():
					if key in tasks.keys():
						tasks[key].update(data)
					else:
						tasks.update({key:data})
			else:
				tasks.update(result.copy())
		tasks=self._sort_tasks(tasks)
		return tasks
	#def get_scheduled_tasks

	def _sort_tasks(self,tasks):
		timestamp=int(datetime.datetime.now().timestamp())
		timenow=datetime.datetime.now()
		sorted_tasks=collections.OrderedDict()
		sorted_indexes={}
		for task_type,index_task in tasks.items():
			for index,task in index_task.items():
				(mon,sw_allm,date_incyear)=self._calculate_date(task['mon'],timenow,'month')
				(dom,sw_alld,date_incmon)=self._calculate_date(task['dom'],timenow,'day')
				(h,sw_allh,date_incday)=self._calculate_date(task['h'],timenow,'hour')
				(m,sw_allmin,date_inch)=self._calculate_date(task['m'],timenow,'minute')
				#DOW
				sw_dowday=False
				if task['dow'].isdigit():
					sw_dowday=True
					d_week=timenow.weekday()+1
					if int(task['dow'])==d_week:
						dom=timenow.day
					else:
						diff_days=int(task['dom'])-d_week
						if diff_days>=0:
							dom=timenow.day+diff_days
						else:
							dom=timenow.day+(7+diff_days)
						if dom>30:
							dom=1
							sw_incmon=True
				elif ',' in task['dow']:
					sw_dowday=True
					d_week=timenow.weekday()+1
					dow_array=task['dow'].split(',')
					if d_week in dow_array:
						dom=timenow.day
					else:
						#Get days diff to most recent day
						diff_days=8
						for d in dow_array:
							d=int(d)
							if abs(d-d_week)<abs(diff_days):
								if d-d_week==0:
									diff_days=0
									break
								diff_days=d-d_week
						if diff_days>=0:
							dom=timenow.day+diff_days
						else:
							dom=timenow.day+(7+diff_days)
						if dom>31:
							dom=1
							sw_incmon=True
				year=timenow.year
				if date_inch:
					h=h+date_inch
					if h>23:
						h=1
						date_incday=date_inch%23
				if date_incday:
					dom=dom+date_incday
					if dom>31:
						dom=1
						date_incmon=date_incday%31
				if date_incmon:
					mon=mon+date_incmon
					if mon>12:
						mon=1
						date_incyear=date_incmon%12
				if date_incyear:
					year+=date_incyear
				time_task=self._calculate_timestamp(year,mon,dom,h,m)
				val=time_task-timestamp
				if val<0:
					if sw_dowday:
						val=time_task+(7*24*60*60)-timestamp
					elif sw_alld:
						val=time_task+(24*60*60)-timestamp
					elif sw_allm:
						mon+=1
						year=timenow.year
						if mon>12:
							mon=1
							year=timenow.year+1
						time_task=self._calculate_timestamp(year,mon,dom,h,m)
						val=time_task-timestamp
					else:
						time_task=self._calculate_timestamp(year+1,mon,dom,h,m)
						val=time_task-timestamp
				sorted_indexes.update({"%s||%s"%(task_type,index):val})
			
		for t_index,value in sorted(sorted_indexes.items(),key=itemgetter(1)):
			(name,index)=t_index.split('||')
			tasks[name][index].update({'val':value})
			sorted_tasks.update({t_index:tasks[name][index]})
		return (sorted_tasks)

	def _calculate_date(self,date_unit,timenow,date_type):
		date_inc,sw_allu=(0,False)
		if date_type=='month':
			time_date=timenow.month
			max_units=12
			start=1
		if date_type=='day':
			time_date=timenow.day
			max_units=31
			start=1
		if date_type=='hour':
			time_date=timenow.hour
			max_units=23
			start=0
		if date_type=='minute':
			time_date=timenow.minute
			max_units=59
			start=0
		if  not date_unit.isdigit():
			if '/' in date_unit:
				e_units=int(date_unit.split('/')[-1])
				if date_type=='minute':
					time_date+=(60*timenow.hour)
					max_units=59*24
				units_left=time_date%e_units
				if units_left and time_date>1:
					if time_date+units_left<=max_units:
						unit=time_date+units_left
						if unit>max_units:
							date_inc=unit//max_units
							unit=unit-max_units
					else:
						#All cycles start at month/day 1 or hour/minute 0
						unit=start
						date_inc=(time_date+units_left)//max_units
				else:
					unit=time_date
			else:
				unit=time_date
				sw_allu=True
		else:
			unit=int(date_unit)
		return (unit,sw_allu,date_inc)

	def _calculate_timestamp(self,year,mon,dom,h,m):
		time_task=0
		try:
			time_task=int(datetime.datetime(year,mon,dom,h,m).timestamp())
		except:
			if dom==31:
				if mon==2:
					dom=29
				else:
					dom=30
				try:
					time_task=int(datetime.datetime(year,mon,dom,h,m).timestamp())
				except:
					try:
						if mon==2:
							dom=28
						time_task=int(datetime.datetime(year,mon,dom,h,m).timestamp())
					except Exception as e:
						print(e)
		return time_task

	def get_task_description(self,i18n_desc):
		desc=i18n_desc
		sw_found=False
		self._debug("Getting desc for %s"%i18n_desc)
		tasks=self.get_available_tasks()
		try:
			for task_desc,task_data in tasks.items():
				for action,cmd in task_data.items():
					if cmd==i18n_desc:
						desc=action
						sw_found=True
						break
				if sw_found:
					break
		except Exception as e:
			print(e)
			self._debug(("Error ocurred when looking for %s")%task_cmd)
		return desc
	#def get_task_description

	def get_task_command(self,i18n_cmd):
		cmd=i18n_cmd
		self._debug("Getting cmd for %s"%i18n_cmd)
		tasks=self.get_available_tasks()
		for task_desc,task_data in tasks.items():
			if task_desc in task_data.keys():
				cmd=task_data[i18n_cmd]
				break
		return cmd
	#def get_task_command

	def add_command(self,task,cmd,cmd_desc):
		if self.n4dserver:
			ret=self.n4dserver.add_command(self.credentials,"SchedulerServer",task,cmd,cmd_desc)
		else:
			ret=self.n4dclient.add_command(self.credentials,"SchedulerServer",task,cmd,cmd_desc)
		return(ret['status'])

	def get_commands(self):
		cmds={}
		if os.path.isfile(self.commands_file):
			try:
				cmds=json.loads(open(self.commands_file).read())
			except Exception as e:
				print(e)
				self._debug(("unable to open %s") % self.commands_file)
		return(cmds)
	#def get_commands

	def get_command_cmd(self,cmd_desc):
		commands=self.get_commands()
		cmd=cmd_desc
		if cmd_desc in commands.keys():
			cmd=commands[cmd_desc]
		return cmd
	#def get_command_cmd

	def _read_tasks_file(self,wrkfile):
		self._debug("Opening %s" % wrkfile)
		tasks=None
		if os.path.isfile(wrkfile) and wrkfile!=self.commands_file:
			try:
				tasks=json.loads(open(wrkfile).read())
			except Exception as e:
				print(e)
				self._debug(("unable to open %s") % wrkfile)
		return(tasks)
	#def _read_tasks_file

	def write_tasks(self,tasks):
		status=False
		self._debug("Sending task info to server")
		result=self.n4dserver.write_tasks(self.credentials,"SchedulerServer",tasks)
		if type(result)==type({}):
			(status,msg)=(result['status'],result['data'])
		return (status,msg)
	#def write_tasks

	def remove_task(self,task):
		status=False
		sw_remote=False
		self._debug("Removing task %s"%task)
		if task['spread']:
			result=self.n4dserver.remove_task(self.credentials,"SchedulerServer",task)
		else:
			result=self.n4dclient.remove_task(self.credentials,"SchedulerServer",task)
		if type(result)==type({}):
			status=result['status']
		self._debug("Status %s"%status)
		return status
	#def remove_task

	def _n4d_connect(self,server):
		#Setup SSL
		context=ssl._create_unverified_context()
		n4dclient = n4d.ServerProxy("https://"+server+":9779",context=context,allow_none=True)
		return(n4dclient)
	#def _n4d_connect
