#!/usr/bin/env python3
###
#
###

import os
import json
import sys
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
		self.tasks_dir=self.conf_dir+'/tasks'
		self.custom_tasks=self.tasks_dir+"/personal.json"
		self.commands_file=self.conf_dir+'/commands/commands.json'
		self.sched_dir="/etc/scheduler/tasks.d"
		self.local_tasks_dir=self.sched_dir+"/local"
	#def __init__

	def _debug(self,msg):
		if (self.dbg):
			print("Scheduler lib: %s" % msg)
	#def _debug
	
	def set_credentials(self,user,pwd,server):
		self.credentials=[user,pwd]
		self.n4dserver=self._n4d_connect(server)
	#def set_credentials

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
						tasks[key]=data

			else:
				tasks.update(result.copy())
		return tasks
	#def get_scheduled_tasks

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

	def _get_wrkfiles(self,sw_remote=None):
		if sw_remote=='available':
			wrkdir=self.tasks_dir
		else:
			wrkdir=self.local_tasks_dir
		wrkfiles=[]
		self._debug("Opening %s"%wrkdir)
		if os.path.isdir(wrkdir):
			for f in os.listdir(wrkdir):
				wrkfiles.append(wrkdir+'/'+f)
		return wrkfiles
	#def _get_wrkfiles

	def add_command(self,cmd_name,cmd):
		if self.n4dserver:
			self.n4dserver.add_command(self.credentials,"SchedulerServer",cmd_name,cmd)
		else:
			self.n4dclient.add_command(self.credentials,"SchedulerServer",cmd_name,cmd)

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

	def write_custom_task(self,cmd_name,cmd,parms):
		status=False
		n4d_server=self.n4dserver
		result=n4d_server.write_custom_task(self.credentials,"SchedulerServer",cmd_name,cmd,parms)
		if type(result)==type({}):
			status=result['status']
		return status
	#def write_custom_task

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

	def write_tasks(self,tasks,sw_remote):
		status=False
		self._debug("Sending task info to %s server"%sw_remote)
		if sw_remote=='remote':
			result=self.n4dserver.write_tasks(self.credentials,"SchedulerServer",sw_remote,tasks)
		else:
			result=self.n4dclient.write_tasks(self.credentials,"SchedulerServer",sw_remote,tasks)
		if type(result)==type({}):
			status=result['status']
		return status
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
