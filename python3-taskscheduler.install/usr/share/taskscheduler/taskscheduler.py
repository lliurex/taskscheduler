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
		self.dbg=False
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
		else:
			self.n4dserver=self.n4dclient
	#def set_credentials

	def read_config(self):
		result=self.n4dclient.read_config("","SchedulerServer")
		return (result['data'])
	#def read_config

	def write_config(self,task,key,value):
		result=self.n4dclient.write_config(self.credentials,"SchedulerServer",task,key,value)
		return(result['status'])
	#def write_config

	def get_available_tasks(self):
		tasks={}
		if self.n4dserver and self.n4dserver!=self.n4dclient:
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
		if self.n4dserver and self.n4dserver!=self.n4dclient:
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
		timenow=datetime.datetime.now()
		timestamp=int(timenow.timestamp())
		sorted_tasks=collections.OrderedDict()
		sorted_indexes={}
		for task_type,index_task in tasks.items():
			for index,task in index_task.items():
				time_task=self.get_task_timestamp(task,timenow,timestamp)
				val=time_task-timestamp
				if val<0:
					time_task+=(365*24*60*60)
					val=time_task-timestamp
				sorted_indexes.update({"%s||%s"%(task_type,index):val})
		for t_index,value in sorted(sorted_indexes.items(),key=itemgetter(1)):
			(name,index)=t_index.split('||')
			tasks[name][index].update({'val':value})
			sorted_tasks.update({t_index:tasks[name][index]})
		return (sorted_tasks)
	#def _sort_tasks

	def get_task_timestamp(self,task,timenow,timestamp):
		time_task=inc_mon=inc_dom=inc_h=inc_m=inc_dow=0
		if task['mon'].isdigit() and task['dom'].isdigit() and task['h'].isdigit() and task['m'].isdigit():
			time_task=self._calculate_timestamp(timenow.year,int(task['mon']),int(task['dom']),int(task['h']),int(task['m']))
		else:
			#Get months left
			(inc_mon,l_mon)=self._get_time_for_next_execution(task['mon'],'mon',timenow)
			#Get days left
			(inc_dom,l_dom)=self._get_time_for_next_execution(task['dom'],'dom',timenow)
			if inc_mon:
				inc_mon=inc_mon-inc_dom
			#get hours left
			(inc_h,l_h)=self._get_time_for_next_execution(task['h'],'h',timenow)
			if inc_dom:
				inc_dom=inc_dom-inc_h
			#get minutes left
			(inc_m,l_m)=self._get_time_for_next_execution(task['m'],'m',timenow)
			if inc_h:
				inc_h=inc_h-inc_m
			#Get days left to dow. As is a special inc must be calculated aside
			if task['dow']!='*' and task['mon']=='*':
				next_dow=0
				weekday=timenow.weekday()+1
				sw_inc=False
				if (l_h<timenow.hour or (l_h==timenow.hour and l_m<timenow.minute)):
					weekday+=1
					sw_inc=True
					if weekday>7:
						weekday=1
				if str(weekday) not in task['dow']:
					if task['dow'].isdigit():
						dow=int(task['dow'])
						if sw_inc and dow==weekday:
							weekday-=1
							if weekday==0:
								weekday=7
						if dow<weekday:
							next_dow=7-(weekday-dow)
						elif dow>weekday:
							next_dow=dow-weekday
					else:
						next_dow=7
						next_week=0
						for str_dow in task['dow'].split(','):
							dow=int(str_dow)
							day_diff=abs(weekday-dow)
							if day_diff<next_dow:
								next_week=0
								if dow<weekday:
									next_week=7
								next_dow=day_diff
						next_dow+=next_week
				inc_dow=next_dow*24*60*60	
			time_task=timestamp+inc_mon+inc_dom+inc_h+inc_m+inc_dow
		return time_task
	#def get_task_timestamp

	###
	#This function returns the seconds left till next execution for a time unit
	#Isn't perfect but is a nice piece of code 
	###
	def _get_time_for_next_execution(self,data,data_type,timenow):
		inc_data=0
		timestamp={'year':timenow.year,'mon':timenow.month,'dom':timenow.day,'h':timenow.hour,'m':timenow.minute}
		timelimit={'mon':12,'dom':31,'h':23,'m':59}
		if data_type=='mon':
			timeconv=30*24*60*60
		elif data_type=='dom':
			timeconv=24*60*60
		elif data_type=='h':
			timeconv=60*60
		else:
			timeconv=60

		if data.isdigit():
			l_data=int(data)
			if l_data<timestamp[data_type]:
				#time exceeded
				inc_data=((timelimit[data_type]-timestamp[data_type])+l_data)*timeconv
			else:
				inc_data=(l_data-timestamp[data_type])*timeconv
		elif '*' in data:
		#Repeat. As is an "all-times" time unit is set to actual date/time unit
			l_data=timestamp[data_type]
		elif '/' in data:
		#Cyclic. If current time<step then next execution is at step. If step>timelimit (each 61 minutes,ie) then current_time will ever be<step so extract parent units (1h for 61min) and convert
			c_data=int(data.split('/')[-1])
			l_data=timestamp[data_type]
			if c_data<l_data:
				if l_data%c_data:
					data_left=(((l_data//c_data)+1)*c_data)-l_data
					if l_data+data_left>timelimit[data_type]:
						data_left=timelimit[data_type]-l_data
					inc_data=data_left*timeconv
			elif c_data>timelimit[data_type]:
				cycles=c_data//timelimit[data_type]
				inc_data=inc_data+(cycles*timelimit[data_type]*timeconv)
		return (inc_data,l_data)
	#def _get_time_for_next_execution

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
	#def _calculate_timestamp

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
		if self.n4dserver and self.n4dserver!=self.n4dclient:
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
