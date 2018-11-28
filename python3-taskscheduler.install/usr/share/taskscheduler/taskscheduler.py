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
		else:
			self.n4dserver=self.n4dclient
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
		sorted_tasks=collections.OrderedDict()
		sorted_indexes={}
		date_now=datetime.datetime.now()
		timestamp=int(date_now.timestamp())
		for task_type,index_task in tasks.items():
			for index,task in index_task.items():
				#Get months left
				inc_mon=0
				inc_dom=0
				inc_h=0
				inc_m=0
				if task['mon'].isdigit() and task['dom'].isdigit() and task['h'].isdigit() and task['m'].isdigit():
					time_task=self._calculate_timestamp(date_now.year,int(task['mon']),int(task['dom']),int(task['h']),int(task['m']))
				else:
					if task['mon'].isdigit():
						l_mon=int(task['mon'])
						if l_mon<date_now.month:
							#year left
							inc_mon=((12-date_now.month)+l_mon)*30*24*60*60
						else:
							inc_mon=(l_mon-date_now.month)*30*24*60*60
					elif '*' in task['mon']:
					#Repeat
						l_mon=date_now.month
					elif '/' in task['mon']:
					#Cyclic
						c_mon=int(task['mon'].split('/')[-1])
						l_mon=date_now.month
						if c_mon<date_now.month:
							l_mon=date_now.month
							if date_now.month%c_mon:
								months_left=(((date_now.month//c_mon)+1)*c_mon)-date_now.month
								if date_now.month+months_left>12:
									months_left=12-date_now.month
								inc_mon=months_left*30*24*60*60
						elif c_mon>12:
							cycles=c_mom//12
							inc_mon=inc_mon+(cycles*12*30*24*60*60)
					#Get days left
					inc_dom=0
					if task['dom'].isdigit():
						l_dom=int(task['dom'])
						if l_dom<date_now.day:
							#month left
							inc_dom=((30-date_now.day)+l_dom)*24*60*60
						else:
							inc_dom=(l_dom-date_now.day)*24*60*60
					elif '*' in task['dom']:
					#Repeat
						l_dom=date_now.day
					elif '/' in task['dom']:
					#Cyclic
						c_dom=int(task['dom'].split('/')[-1])
						l_dom=date_now.day
						if c_dom<date_now.day:
							l_dom=date_now.day
							if date_now.day%c_dom:
								days_left=(((date_now.day//c_dom)+1)*c_dom)-date_now.day
	#							if date_now.days+days_left>31:
	#								days_left=31-date_now.days
								inc_dom=days_left*24*60*60
						elif c_dom>31:
							cycles=c_dom//31
							inc_dom=inc_dom+(cycles*30*24*60*60)
					if inc_mon:
						inc_mon=inc_mon-inc_dom

					#get hours left
					inc_h=0
					if task['h'].isdigit():
						l_h=int(task['h'])
						if l_h<date_now.hour:
							#day left
							inc_h=((24-date_now.hour)+l_h)*60*60
						else:
							inc_h=(l_h-date_now.hour)*60*60
					elif '*' in task['h']:
					#Repeat
						l_h=date_now.hour
					elif '/' in task['h']:
					#Cyclic
						c_h=int(task['h'].split('/')[-1])
						l_h=date_now.hour
						if c_h<date_now.hour:
							l_h=date_now.hour
							if date_now.hour%c_h:
								hours_left=(((date_now.hour//c_h)+1)*c_h)-date_now.hour
	#							if date_now.hour+hours_left>23:
	#								hours_left=23-date_now.hour
								inc_h=hours_left*60*60
						elif c_h>23:
							cycles=c_h//23
							inc_h=inc_h+(cycles*24**60*60)
					if inc_dom:
						inc_dom=inc_dom-inc_h

					#get minutes left
					inc_m=0
					if task['m'].isdigit():
						l_m=int(task['m'])
						if l_m<date_now.minute:
							#hour left
							inc_m=((60-date_now.minute)+l_m)*60
						else:
							inc_m=(l_m-date_now.minute)*60
					elif '*' in task['m']:
					#Repeat
						l_m=date_now.minute
					elif '/' in task['m']:
					#Cyclic
						c_m=int(task['m'].split('/')[-1])
						l_m=date_now.minute
						if c_m<date_now.minute:
							l_m=date_now.minute
							if date_now.minute%c_m:
								mins_left=(((date_now.minute//c_m)+1)*c_m)-date_now.minute
	#							if date_now.minute+mins_left>59:
	#								mins_left=59-date_now.minute
								inc_m=mins_left*60
						elif c_m>59:
							cycles=c_m//59
							inc_m=inc_m+(cycles*60*60)
					if inc_h:
						inc_h=inc_h-inc_m

					inc_dow=0
					if task['dow']!='*' and task['mon']=='*':
					#Get days left to dow
						next_dow=0
						weekday=date_now.weekday()+1
						if (l_h<date_now.hour or (l_h==date_now.hour and l_m<date_now.minute)):
							weekday+=1
							if weekday>7:
								weekday=1
						if str(weekday) not in task['dow']:
							if task['dow'].isdigit():
								dow=int(task['dow'])
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
										if dow<weekday:
											next_week=7
										else:
											next_week=0
										next_dow=day_diff
								next_dow+=next_week
						inc_dow=next_dow*24*60*60	
					time_task=timestamp+inc_mon+inc_dom+inc_h+inc_m+inc_dow

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
