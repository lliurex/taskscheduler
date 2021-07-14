#!/usr/bin/env python3
###
#
###
import os
import json
import sys
import collections
import datetime
import os,sys,socket
from operator import itemgetter
from PySide2.QtCore import QObject,Signal
import n4d.responses
import n4d.client as n4dclient
from appconfig.appConfigN4d import appConfigN4d
import subprocess
sys.path.insert(1, '/usr/lib/python3/dist-packages/appconfig')
import n4dCredentialsBox as login

#try:
#	import xmlrpc.client as n4d
#except ImportError:
#	raise ImportError("xmlrpc not available. Disabling server queries")
#import ssl

USERNOTALLOWED_ERROR=-10
class TaskScheduler(QObject):
	onCredentials=Signal(dict)
	def __init__(self):
		super(TaskScheduler, self).__init__()
		self.dbg=False
		self.credentials=["",""]
		self.n4dserver=None
		self.result=[]
		self.username=''
		self.password=''
		self.launchQueue={}
		self.server='localhost'
		self.n4dClient=self._n4d_connect()
		self.n4dMaster=None
		self.n4d=appConfigN4d()
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

	def read_config(self):
		result=self.n4dClient.read_config("","SchedulerServer")
		if 'data' in result.keys():
			return (result['data'])
		else:
			return({})
	#def read_config

	def write_config(self,task,key,value):
		n4dclass="SchedulerServer"
		n4dmethod="write_config"
		n4parms=[task,key,value]
		result=self.n4d.n4dQuery(n4dclass,n4dmethod,n4dparms)
	#	result=self.n4dClient.write_config(self.credentials,"SchedulerServer",task,key,value)
		return(result['status'])
	#def write_config

	def get_available_tasks(self):
		tasks={}
		plugin="SchedulerServer"
		method="get_available_tasks"
		proxy=n4dclient.Proxy(self.n4dClient,plugin,method)
		result=proxy.call()
		if isinstance(result,dict) and result.get('data',{}):
			if tasks:
				#Merge values
				for key,data in result['data'].items():
					if key in tasks.keys():
						tasks[key].update(data)
					else:
						tasks.update({key:data})
			else:
				tasks.update(result['data'].copy())
		return tasks
	#def get_available_tasks

	def get_scheduled_tasks(self):
		tasks={}
		if not self.n4dserver:
			self.n4dserver=self._n4d_connect(server='server')
		self._debug("SERVER {} CLIENT {}".format(self.n4dserver,self.n4dClient))
		if self.n4dserver and self.n4dserver!=self.n4dClient:
			self._debug("Retrieving server task list")
			plugin="SchedulerServer"
			method="get_remote_tasks"
			proxy=n4dclient.Proxy(self.n4dserver,plugin,method)
			result=proxy.call()
			if type(result)==type({}):
				tasks=result.copy()
		self._debug("Retrieving task list")
		plugin="SchedulerServer"
		method="get_tasks"
		proxy=n4dclient.Proxy(self.n4dClient,plugin,method)

		#result=self.n4dClient.get_local_tasks("","SchedulerServer")['return']
		result=proxy.call().get('data',{})
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
				self._debug("Total: %s"%val)
				if val<0:
					time_task+=(365*24*60*60)
					val=time_task-timestamp
				self._debug("Left: %s"%val)
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
			if (task['dow']!='*' and task['mon']=='*') or (task['mon']=='*' and task['dom']=='*'):
				next_dow=0
				days_dow=task['dow']
				weekday=timenow.weekday()+1
				sw_inc=False
				if (l_h<timenow.hour or (l_h==timenow.hour and l_m<timenow.minute)):
					weekday+=1
					self._debug("Inc for dow. Weekday: %s"%weekday)
					sw_inc=True
					if weekday>7:
						weekday=1
				if days_dow=='*':
					days_dow="1,2,3,4,5,6,7"
				if str(weekday) not in days_dow:
					if days_dow.isdigit():
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
						for str_dow in days_dow.split(','):
							dow=int(str_dow)
							day_diff=abs(weekday-dow)
							if day_diff<next_dow:
								next_week=0
								if dow<weekday:
									next_week=7
								next_dow=day_diff
							elif dow>weekday:
								next_week=0
						next_dow+=next_week
				if sw_inc:
					inc_dow=next_dow*24*60*60+(((l_h)*60*60)+((timenow.minute-l_m)*60))
					if timenow.hour>=l_h:
						inc_dow=inc_dow+((24-timenow.hour)*60*60)
				else:
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
			self._debug("Calc: %s"%data_type)
			self._debug("Inc: %s"%inc_data)
			self._debug("Now: %s"%timestamp[data_type])
			self._debug("Pro: %s"%l_data)
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
		if self.n4dserver and self.n4dserver!=self.n4dClient:
			ret=self.n4dserver.add_command(self.credentials,"SchedulerServer",task,cmd,cmd_desc)
		else:
			plugin="SchedulerServer"
			method="add_command"
			arguments=[task,cmd,cmd_desc]
			result=self.n4d.n4dQuery(plugin,method,arguments)
		#	proxy=n4dclient.Proxy(self.n4dClient,plugin,method)
		#	result={}
		#	try:
		#		result=proxy.call(arguments)
		#	except n4d.client.UserNotAllowedError:
				#Credentials not valid, ask for
		#		print("ERROR")
			#ret=self.n4dClient.add_command(self.credentials,"SchedulerServer",task,cmd,cmd_desc)
			#return(ret['status'])
		return(True)

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
		plugin="SchedulerServer"
		method="write_tasks"
		#proxy=n4dclient.Proxy(self.n4dClient,plugin,method)
		result={}
		ip=''
		for group,g_data in tasks.items():
			for index,i_data in g_data.items():
				if i_data['spread']:
					ip='server'
				#result=proxy.call(tasks)
				result=self._proxyLaunch(plugin,method,tasks,ip=ip)
				#result=self.n4d.n4dQuery(plugin,method,tasks)
		self._debug("Sending task to cron")
		plugin="SchedulerClient"
		method="process_tasks"
		#proxy=n4dclient.Proxy(self.n4dClient,plugin,method)
		#result=self.n4d.n4dQuery(plugin,method,tasks)
		result=self._proxyLaunch(plugin,method,tasks)

		if isinstance(result,dict):
			(status,msg)=(result.get('status',1),result.get('result',{}))
		else:
			(status,msg)=(0,{'data':True})

		return (status,msg)
	#def write_tasks

	def remove_task(self,task):
		status=False
		sw_remote=False
		self._debug("Removing task %s"%task)
		plugin="SchedulerServer"
		method="remove_task"
		if task['spread']:
			result=self._proxyLaunch(plugin,method,task)
			#result=self.n4dserver.remove_task(self.credentials,"SchedulerServer",task)
		else:
			result=self._proxyLaunch(plugin,method,task)
			#result=self.n4dClient.remove_task(self.credentials,"SchedulerServer",task)
		if isinstance(result,dict):
			(status,msg)=(result.get('status',1),result.get('result',{}))
		else:
			(status,msg)=(0,{'data':True})
		self._debug("Status %s"%status)
		return status
	#def remove_task

	def setCredentials(self,tickets):
		client=None
		master=None
		if not self.key in self.launchQueue.keys():
			return
		for ticket in tickets:
			if not 'localhost' in str(ticket) and not self.server_ip in str(ticket):
				self._debug("Discard ticket {} for {}".format(ticket,self.server_ip))
				continue
			n4dProxy=self._n4d_connect(ticket,self.server_ip)
			self._debug("N4d client: {}".format(n4dProxy))
			self._debug("N4d old client: {}".format(self.n4dClient))
			if 'localhost:' in str(ticket):
				self._debug("Relaunching n4dMethod on client")
				oldProxy=self.n4dClient
				self.n4dClient=n4dProxy
			elif self.server_ip in str(ticket):
				self._debug("Relaunching n4dMethod on master")
				oldProxy=self.n4dMaster
				self.n4dMaster=n4dProxy
			data=self.launchQueue.get(self.key,None)
			if not data:
				continue
			del(self.launchQueue[self.key])
			#Update all n4dcalls
			delKeys=[]
			for key in self.launchQueue.keys():
				if key.startswith(str(oldProxy)):
					delKeys.append(key)
			for delKey in delKeys:
				a=delKey
				a=a.replace(str(oldProxy),str(n4dProxy))
				self.launchQueue[a]=self.launchQueue.pop(delKey)
				self.launchQueue[a]['client']=n4dProxy
			key=self.key.replace(str(oldProxy),str(n4dProxy))
			self.launchQueue[key]={'client':n4dProxy,'n4dClass':data['n4dClass'],'n4dMethod':data['n4dMethod'],'args':data['args'],'kwargs':data.get('kwargs','')}
		if self.launchQueue:
			self.onCredentials.emit(self.launchQueue)
	#def set
	def setCredentials2(self,tickets):
		client=None
		master=None
		if not self.key in self.launchQueue.keys():
			return
		for ticket in tickets:
			n4dProxy=self._n4d_connect(ticket)
			self._debug("N4d client: {}".format(n4dProxy))
			self._debug("N4d old client: {}".format(self.n4dClient))
			if 'localhost:' in ticket:
				self._debug("Relaunching n4dMethod on client")
				oldProxy=self.n4dClient
				self.n4dClient=n4dProxy
			elif self.server_ip in ticket:
				self._debug("Relaunching n4dMethod on master")
				oldProxy=self.n4dMaster
				self.n4dMaster=n4dProxy
			data=self.launchQueue[self.key]
			del(self.launchQueue[self.key])
			#Update all n4dcalls
			delKeys=[]
			for key in self.launchQueue.keys():
				if key.startswith(str(oldProxy)):
					delKeys.append(key)
			for delKey in delKeys:
				a=delKey
				a=a.replace(str(oldProxy),str(n4dProxy))
				self.launchQueue[a]=self.launchQueue.pop(delKey)
				self.launchQueue[a]['client']=n4dProxy
			key=self.key.replace(str(oldProxy),str(n4dProxy))
			self.launchQueue[key]={'client':n4dProxy,'n4dClass':data['n4dClass'],'n4dMethod':data['n4dMethod'],'args':data['args'],'kwargs':data.get('kwargs','')}
		self.onCredentials.emit(self.launchQueue)
		self.launchN4dQueue(self.launchQueue)
	#def setCredentials

	def _proxyLaunch(self,n4dClass,n4dMethod,*args,**kwargs):
		client=""
		server_ip="localhost"
		self._debug("Kwargs: {}".format(kwargs))
		self._debug("Query: {}.{}".format(n4dClass,n4dMethod))
		if kwargs:
			server_ip=kwargs.get('ip','server')
			self._debug("Received server: {}".format(server_ip))
			
		result={'status':-1,'return':''}
		if server_ip=='localhost' and self.n4dClient==None:
			self._debug("Creating client connection")
			self.n4dClient=self._n4d_connect(server=server_ip)
		elif self.n4dMaster==None or (self.n4dMaster!=None and server_ip not in self.n4dMaster.address):
			self._debug("Creating server connection")
			self.n4dMaster=self._n4d_connect(server=server_ip)

		#Launch and pray. If there's validation error ask for credentials
		try:
			if server_ip and server_ip!='localhost':
				self._debug("Launching n4dMethod on master")
				key="{}:{}:{}".format(str(self.n4dMaster),n4dClass,n4dMethod)
				result=self._launch(self.n4dMaster,n4dClass,n4dMethod,*args)
			else:
				self._debug("Launching n4dMethod on client")
				key="{}:{}:{}".format(str(self.n4dClient),n4dClass,n4dMethod)
				result=self._launch(self.n4dClient,n4dClass,n4dMethod,*args)
			if key in self.launchQueue.keys():
				del(self.launchQueue[key])
		except n4d.client.UserNotAllowedError as e:
			#User not allowed, ask for credentials and relaunch
			result={'status':-1,'code':USERNOTALLOWED_ERROR}
			if server_ip and server_ip!='localhost':
				self.launchQueue[key]={'client':self.n4dMaster,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			else:
				self.launchQueue[key]={'client':self.n4dClient,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			self.key=key
			#Get credentials
			self.server_ip=server_ip
			self._debug("Registering to server: {}".format(server_ip))
			self.onCredentials.connect(self.launchN4dQueue)
			credentials=login.n4dCredentials(server_ip)
			self.loginBox=credentials.dialog
			self.loginBox.onTicket.connect(self.setCredentials)
			if self.loginBox.exec():
				result={'status':0,'code':USERNOTALLOWED_ERROR}
				result=self.result
		except n4d.client.InvalidServerResponseError as e:
			self._debug("Response: {}".format(e))
		except Exception as e:
			print('Error: {}'.format(e))
		self._debug("N4d response: {}".format(result))
		return(result)
	#def n4dQuery(self,n4dclass,n4dmethod,*args):
	
	def launchN4dQueue(self,launchQueue):
		self._debug("Launch: {}".format(self.launchQueue))
		self.result=[]
		launch=self.launchQueue.copy()
		for client,callData in launch.items():
			self._debug("Exec: {}".format(callData))
			try:
				self.result=self._launch(callData['client'],callData['n4dClass'],callData['n4dMethod'],*callData['args'])
			except:
				print("***********************************************")
				pass
	#def launchN4dQueue(self,launchQueue):
	def _proxyLaunch2(self,n4dClass,n4dMethod,*args,**kwargs):
		client=""
		server_ip="localhost"
		self._debug("Kwargs: {}".format(kwargs))

		if kwargs:
			server_ip=kwargs.get('ip','server')
			self._debug("Received server: {}".format(server_ip))
			
		result={'status':-1,'return':''}
		if server_ip=='localhost' and self.n4dClient==None:
			self._debug("Creating client connection")
			self.n4dClient=self._n4d_connect(server=server_ip)
		elif self.n4dMaster==None:
			self._debug("Creating server connection for {}".format(server_ip))
				#	if self.n4dMaster==None and server_ip and server_ip!='localhost':
			self.n4dMaster=self._n4d_connect(server=server_ip)

		self.server_ip=server_ip
		#Launch and pray. If there's validation error ask for credentials
		try:
			if server_ip and server_ip!='localhost':
				self._debug("Launching n4dMethod on master")
				result=self._launch(self.n4dMaster,n4dClass,n4dMethod,*args)
			else:
				self._debug("Launching n4dMethod on client")
				result=self._launch(self.n4dClient,n4dClass,n4dMethod,*args)
			del(self.launchQueue["{}:{}".format(n4dClass,n4dMethod)])
		except n4d.client.UserNotAllowedError as e:
			#User not allowed, ask for credentials and relaunch
			result={'status':-1,'code':USERNOTALLOWED_ERROR}
			if server_ip and server_ip!='localhost':
				key="{}:{}:{}".format(str(self.n4dMaster),n4dClass,n4dMethod)
				self.launchQueue[key]={'client':self.n4dMaster,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			else:
				key="{}:{}:{}".format(str(self.n4dClient),n4dClass,n4dMethod)
				self.launchQueue[key]={'client':self.n4dClient,'n4dClass':n4dClass,'n4dMethod':n4dMethod,'args':list(args),'kwargs':kwargs}
			self.key=key
			#Get credentials
			self._debug("Registering to server: {}".format(server_ip))
			credentials=login.n4dCredentials(server_ip)
			self.loginBox=credentials.dialog
			#self.loginBox.loginBox(server_ip)
			#self.loginBox.loginBox(self.server)
			self.loginBox.onTicket.connect(self.setCredentials)
			self.loginBox.exec()
			self._debug("2Registering to server: {}".format(server_ip))
			self.onCredentials.connect(self.launchN4dQueue)
		except n4d.client.InvalidServerResponseError as e:
			self._debug("Response: {}".format(e))
		except Exception as e:
			print('Error: {}'.format(e))
		self._debug("N4d response: {}".format(result))
		return(result)
	#def n4dQuery(self,n4dclass,n4dmethod,*args):
	
	def launchN4dQueue(self,launchQueue):
		self._debug("Launch: {}".format(launchQueue))
		launch=launchQueue.copy()
		for client,callData in launch.items():
			self._debug("Exec: {}:{}".format(client,callData))
			try:
				result=self._launch(callData['client'],callData['n4dClass'],callData['n4dMethod'],*callData['args'])#,callData['kwargs'])
			except Exception as e:
				self._debug("Client: {} Error: {}".format(callData['client'],e))
	
	def _launch(self,n4dClient,n4dClass,n4dMethod,*args):
		proxy=n4d.client.Proxy(n4dClient,n4dClass,n4dMethod)
		if "{}:{}:{}".format(str(n4dClient),n4dClass,n4dMethod) in self.launchQueue.keys():
			del(self.launchQueue["{}:{}:{}".format(str(n4dClient),n4dClass,n4dMethod)])
		try:
			self._debug("Call client: {}".format(n4dClient))
			self._debug("Call class: {}".format(n4dClass))
			self._debug("Call method: {}".format(n4dMethod))
			if len(args):
				self._debug("Call Args: {}".format(*args))
				result=proxy.call(*args)
			else:
				result=proxy.call()
		except Exception as e:
			print(e)
			raise e
		self._debug("Launch Result: {}".format(result))
		return result
	#def _launch
	def _launch2(self,n4dClient,n4dClass,n4dMethod,*args):
		proxy=n4d.client.Proxy(n4dClient,n4dClass,n4dMethod)
		if "{}:̣{}".format(n4dClass,n4dMethod) in self.launchQueue.keys():
			del(self.launchQueue["{}:̣{}".format(n4dClass,n4dMethod)])
		try:
			self._debug("Call client: {}".format(n4dClient))
			self._debug("Call class: {}".format(n4dClass))
			self._debug("Call method: {}".format(n4dMethod))
			if len(args):
				if isinstance(args,dict):
					args1=json.dumps(args)
				else:
					args1=args
				self._debug("Call Args: {}".format(args1))
				result=proxy.call(args1)
			else:
				result=proxy.call()
			del(self.launchQueue["{}:{}:{}".format(str(n4dClient),n4dClass,n4dMethod)])
		except Exception as e:
			print(e)
			raise e
		print("Launch Result: {}".format(result))
		return result

	def _n4d_connect(self,ticket='',server='localhost'):
		#self.n4dClient=None
		self._debug("Connecting to n4d at {}".format(server))
		client=""
		if ticket:
			ticket=ticket.replace('##U+0020##',' ').rstrip()
			tk=n4d.client.Ticket(ticket)
			client=n4d.client.Client(ticket=tk)
			self._debug("N4d Object2: {}".format(client.credential.auth_type))
		else:
			try:
				socket.gethostbyname(server)
			except:
				#It could be an ip
				try:
					socket.inet_aton(server)
				except Exception as e:
					self.error(e)
					self.error("No server found. Reverting to localhost")
					self.server='https://localhost:9779'
			if not server.startswith("http"):
				server="https://{}".format(server)
			if len(server.split(":")) < 3:
					server="{}:9779".format(server)
				
			if self.username:
				client=n4d.client.Client(server,self.username,self.password)
			else:
				client=n4d.client.Client(server)
		#self.n4dClient=client
		self._debug("N4d Object2: {}".format(client.credential.auth_type))
		return(client)
	#def _n4d_connect

