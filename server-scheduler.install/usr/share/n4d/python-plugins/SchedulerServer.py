#!/usr/bin/env python
######
#Scheduler library for Lliurex
#Add to N4D the scheduled tasks
#This class reads the json file with the scheduled tasks and
#distributes the info among the clients
# -*- coding: utf-8 -*-
import os
import json
from  datetime import date

class SchedulerServer():
	def __init__(self):
		self.dbg=1
		self.tasks_dir="/etc/scheduler/tasks.d"
		self.available_tasks_dir="/etc/scheduler/conf.d/tasks"
		self.conf_dir="/etc/scheduler/conf.d/"
		self.conf_file="%s/scheduler.conf"%self.conf_dir
	#def __init__

	def _debug(self,msg):
		if (self.dbg):
			print("Scheduler: %s" %msg)
	#def _debug
	
	def read_config(self):
		status=True
		data={}
		if not os.path.isdir(self.conf_dir):
			try:
				os.makedirs(self.conf_dir)
			except Exception as e:
				status=False
				data=e
				self._debug("Couldn't create conf dir %s"%self.conf_dir)
		if os.path.isfile(self.conf_file):
			try:
				data=json.loads(open(self.conf_file).read())
			except Exception as e:
				data=e
				status=False
				self._debug(("unable to open %s") % self.conf_file)
		return ({'status':status,'data':data})
	#def read_config

	def write_config(self,task,color):
		status=True
		data={}
		if os.path.isfile(self.conf_file):
			try:
				config=json.loads(open(self.conf_file).read())
			except Exception as e:
				data=e
				status=False
				self._debug(("unable to open %s") % self.conf_file)
		if task in config.keys():
			config[task].update({'background':color})
		else:
			config[task]={'background':color}
		try:
			with open(self.conf_file,'w') as f:
				json.dump(config,f,indent=4)
		except Exception as e:
			data=e
			self._debug(("unable to write %s") % self.conf_file)
			status=False
		return ({'status':status,'data':data})
	#def write_config

	def get_tasks(self,*args):
		return(self._read_wrkfiles(self.tasks_dir))
	#def get_tasks

	def get_local_tasks(self,*args):
		today=date.today()
		local_tasks={}
		tasks_data=self._read_wrkfiles(self.tasks_dir)['data'].copy()
		status=False
		for task_name,serial_data in tasks_data.items():
			sw_continue=False
			for serial,data in serial_data.items():
				sw_pass=False
				if 'autoremove' in data.keys():
					if (data['mon'].isdigit()):
						mon=int(data['mon'])
						if mon<today.month:
							sw_pass=True
					if sw_pass==False:
						if (data['dom'].isdigit()):
							dom=int(data['dom'])
							if dom<today.day:
								sw_pass=True
					if sw_pass:
						task={}
						self._debug("Autoremoving %s %s"%(task_name,serial))
						task['name']=task_name
						task['serial']=serial
						self.remove_task(task)
						continue
#				if 'spread' in data.keys():
#					if data['spread']==False:
#						if task_name in local_tasks.keys():
#							local_tasks[task_name][serial]=tasks_data[task_name][serial]
#							status=True
#						else:
#							local_tasks[task_name]={serial:tasks_data[task_name][serial]}
#							status=True
#				else:
				if task_name in local_tasks.keys():
					local_tasks[task_name][serial]=tasks_data[task_name][serial]
					status=True
				else:
					local_tasks[task_name]={serial:tasks_data[task_name][serial]}
					status=True
		return ({'status':status,'data':local_tasks})

	def get_remote_tasks(self,*args):
		remote_tasks={}
		tasks_data=self._read_wrkfiles(self.tasks_dir)['data'].copy()
		status=False

		for task_name,serial_data in tasks_data.items():
			sw_continue=False
			for serial,data in serial_data.items():
				if 'spread' in data.keys():
					if data['spread']==True:
						if task_name in remote_tasks.keys():
							remote_tasks[task_name]['r'+serial]=tasks_data[task_name][serial]
							status=True
						else:
							remote_tasks[task_name]={'r'+serial:tasks_data[task_name][serial]}
							status=True
		return ({'status':status,'data':remote_tasks})

	def get_available_tasks(self):
		return(self._read_wrkfiles(self.available_tasks_dir))

	def _read_wrkfiles(self,folder):
		tasks={}
		wrkfiles=self._get_wrkfiles(folder)
		self._debug(folder)
		for wrkfile in wrkfiles:
			task=self._read_tasks_file(wrkfile)
			if task:
				tasks.update(task)
		self._debug("Tasks loaded")
		self._debug(str(tasks))
		return({'status':True,'data':tasks})

	def _get_wrkfiles(self,folder):
		wrkfiles=[]
		if not os.path.isdir(folder):
			os.makedirs(folder)
		for f in os.listdir(folder):
			wrkfiles.append(folder+'/'+f)
		return wrkfiles
	#def _get_wrkfiles

	def _read_tasks_file(self,wrkfile):
		self._debug("Opening %s" % wrkfile)
		tasks={}
		if os.path.isfile(wrkfile):
			try:
				tasks=json.loads(open(wrkfile,"rb").read())
			except Exception as e:
				errormsg=(("unable to open %s") % wrkfile)
				errormsg=(("Reason: %s") %e)
				self._debug(errormsg)
		return(tasks)
	#def _read_tasks_file
	
	def remove_task(self,task,*args):
		#Retrocompatibility
		if type(task)==type(""):
			task_compat={}
			if task=='remote':
				task_compat['sw_remote']=True
			else:
				task_compat['sw_remote']=False
			if args[0]:
				task_compat['name']=args[0]
			if args[1]:
				task_compat['serial']=args[1]
			if args[2]:
				task_compat['cmd']=args[2]
			task=task_compat
		wrk_dir=self.tasks_dir
		self._debug("Removing task from system")
		sw_del=False
		msg=''
		wrkfile=wrk_dir+'/'+task['name']
		wrkfile=wrkfile.replace(' ','_')
		tasks=self._read_tasks_file(wrkfile)
		if task['name'] in tasks.keys():
			self._debug("Serial: %s"%task['serial'])
			if task['serial'] in tasks[task['name']].keys():
				del tasks[task['name']][task['serial']]
				self._debug("Task deleted")
				sw_del=True
			elif task['serial'][0]=='r':
				serial=task['serial'].strip('r')
				if serial in tasks[task['name']].keys():
					if tasks[task['name']][serial]['spread']:
						del tasks[task['name']][serial]
						self._debug("Task deleted")
						sw_del=True


		if sw_del:
			tasks=self._serialize_task(tasks)
			with open(wrkfile,'w') as json_data:
				json.dump(tasks,json_data,indent=4)
			self._register_cron_update()
		return ({'status':sw_del,'data':msg})
	#def remove_task

	def _serialize_task(self,task):
		serial_task={}
		for name,task_data in task.items():
			cont=0
			serial_task[name]={}
			for serial,data in task_data.items():
				serial_task[name].update({cont+1:data})
				cont+=1
		return(serial_task)
	#def _serialize_task
	
	def write_tasks(self,task):
		msg=''
		status=False
		#Ensure that dest path exists
		if not os.path.isdir(self.tasks_dir):
			os.makedirs(self.tasks_dir)
		#Retrieve task data
		for name,serial in task.iteritems():
			task_name=name
			for index,data in serial.iteritems():
				task_serial=index
				task_data=data
		#Open dest file
		wrkfile=self.tasks_dir+'/'+task_name
		wrkfile=wrkfile.replace(' ','_')
		task_data=self._fill_task_data(task_data)
		sched_tasks={}
		if os.path.isfile(wrkfile):
			sched_tasks=json.loads(open(wrkfile).read())
			if not task_serial:
				serials=[str(i) for i in sched_tasks[task_name].keys()]
				self._debug("Serials %s"%serials)
				task_serial="0"
				if task_name in sched_tasks.keys():
					for ser in range(len(sched_tasks[task_name])+1):
						if not str(ser) in serials:
							task_serial=str(ser)
							self._debug("New serial %s"%task_serial)
							break
		else:
			self._debug("%s doen't exists"%wrkfile)
			task_serial="0"
		self._debug("Writing task info %s - %s"%(task_name,task_serial))
		if task_name in sched_tasks.keys():
			if task_serial in sched_tasks[task_name].keys():
				sched_tasks[task_name][task_serial].update(task_data)
			else:
				sched_tasks[task_name].update({task_serial:task_data})
		else:
			sched_tasks.update({task_name:{task_serial:task_data}})
		
		try:
			with open(wrkfile,'w') as json_data:
				json.dump(sched_tasks,json_data,indent=4)
			status=True
			msg=task_serial
		except Exception as e:
			msg=e
		self._register_cron_update()
		self._debug("%s updated" % task_name)
		return({'status':status,'data':msg})
	#def write_tasks

	def _fill_task_data(self,task):
		task['kind']=[]
		if 'spread' not in task.keys():
			task['spread']=False
		#set task kind
		if task['dow']!='*':
			task['kind'].append('daily')
		try:
			int(task['mon'])
			int(task['dom'])
			int(task['h'])
			int(task['m'])
			task['kind']=['fixed']
		except:
			if '/' in (task['mon']+task['dom']+task['h']+task['m']):
				task['kind'].append('repeat')
		return task

	def add_command(self,task,cmd,cmd_desc):
		self._debug("Adding command %s - %s - %s"%(task,cmd,cmd_desc))
		tasks={}
		status=True
		msg=''
		wrkfile="%s/%s.json"%(self.available_tasks_dir,task)
		if os.path.isfile(wrkfile):
			tasks=json.loads(open(wrkfile).read())
		if task in tasks.keys():
			tasks[task].update({cmd_desc:cmd})
		else:
			tasks.update({task:{cmd_desc:cmd}})
		try:
			with open(wrkfile,'w') as json_data:
				json.dump(tasks,json_data,indent=4)
		except Exception as e:
			status=False
			msg=str(e)
		return({'status':status,'data':msg})
	#def add_command

	def _register_cron_update(self):
		self._debug("Registering trigger var")
		val=0
		if not objects["VariablesManager"].get_variable("SCHEDULED_TASKS"):
			self._debug("Initializing trigger var")
			objects["VariablesManager"].add_variable("SCHEDULED_TASKS",{},"","Scheduled tasks trigger","n4d-scheduler-server",False,False)
		val=objects["VariablesManager"].get_variable("SCHEDULED_TASKS")
		if not val:
			val=0
		if val>=1000:
			val=0
		val+=1
		objects["VariablesManager"].set_variable("SCHEDULED_TASKS",val)
		self._debug("New value is %s"%val)
	#def _register_cron_update
