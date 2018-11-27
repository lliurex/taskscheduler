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
		self.dbg=0
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

	def get_scheduled_tasks(self,sw_remote):
		tasks={}
		self._debug("Retrieving task list remote=%s"%sw_remote)
		if self.n4dserver:
			result=self.n4dserver.get_remote_tasks("","SchedulerServer")['data']
			if type(result)==type({}):
				tasks=result.copy()
#		result=self.n4dclient.get_tasks("","SchedulerServer")['data']
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
				sw_allm=False
				sw_alld=False
				sw_incyear=False
				sw_incmon=False
				if  not task['mon'].isdigit():
					if '/' in task['mon']:
						e_mon=int(task['mon'].split('/')[-1])
						months_left=timenow.month%e_mon
						if months_left and timenow.month>1:
							if timenow.month+months_left<=12:
								mon=timenow.month+months_left
							else:
								#All cycles start at month 1
								mon=1
								sw_incyear=True
						else:
							mon=timenow.month
						print("LAUNCH IN %s (incyear: %s)"%(mon,sw_incyear))
					else:
						mon=timenow.month
						sw_allm=True
				else:
					mon=int(task['mon'])
				if not task['dom'].isdigit():
					if '/' in task['dom']:
						e_dom=int(task['dom'].split('/')[-1])
						days_left=timenow.day%e_dom
						if timenow.day%e_dom and timenow.day>1:
							if timenow.day+days_left<=30:
								dom=timenow.day+days_left
							else:
								#All cycles start at day 1
								dom=1
								sw_incmon=True
						else:
							dom=timenow.day
					else:
						dom=timenow.day
						sw_alld=True
				else:
					dom=int(task['dom'])
				if not task['h'].isdigit():
					h=timenow.hour
				else:
					h=int(task['h'])
				if not task['m'].isdigit():
					m=timenow.minute
				else:
					m=int(task['m'])
				year=timenow.year
				if sw_incmon:
					mon=mon+1
					if mon>12:
						mon=1
						sw_incyear=True
				if sw_incyear:
					year+=1
				time_task=int(datetime.datetime(year,mon,dom,h,m).timestamp())
				val=time_task-timestamp
				if val<0:
					if sw_alld:
						val=time_task+(24*60*60)-timestamp
					elif sw_allm:
						mon+=1
						year=timenow.year
						if mon>12:
							mon=1
							year=timenow.year+1
						time_task=int(datetime.datetime(year,mon,dom,h,m).timestamp())
						val=time_task-timestamp
					else:
						time_task=int(datetime.datetime(timenow.year+1,mon,dom,h,m).timestamp())
						val=time_task-timestamp
				sorted_indexes.update({"%s||%s"%(task_type,index):val})
			
		for t_index,value in sorted(sorted_indexes.items(),key=itemgetter(1)):
			(name,index)=t_index.split('||')
			tasks[name][index].update({'val':value})
			sorted_tasks.update({t_index:tasks[name][index]})
		return (sorted_tasks)

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
