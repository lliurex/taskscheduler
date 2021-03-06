#!/usr/bin/env python
###
#
###

# -*- coding: utf-8 -*-
import os,socket
import threading
import time
from  datetime import date
#import xmlrpclib as xmlrpc
import signal
import n4d.responses
import n4d.client as n4dclient
import n4d.server.core as n4dCore

class SchedulerClient():
	def __init__(self):
		self.dbg=False
		self.task_prefix='remote-' #Temp workaround->Must be declared on a n4d var
		self.cron_dir='/etc/cron.d'
		self.count=0
		self.holidays_shell="/usr/bin/check_holidays.py"
		self.pidfile="/tmp/taskscheduler.pid"
		self.core=n4dCore.Core.get_core()
		self.n4dclient=self._n4d_connect('localhost')

	def startup(self,options):
		t=threading.Thread(target=self._main_thread)
		t.daemon=True
		t.start()

	def _debug(self,msg):
		if self.dbg:
			print("{}".format(msg))

	def _main_thread(self):
		self.core.register_variable_trigger("SCHEDULED_TASKS","SchedulerClient",self.process_tasks)
		tries=10
		for x in range (0,tries):
			#self.scheduler_var=objects["VariablesManager"].get_variable("SCHEDULED_TASKS")
			self.scheduler_var=self.core.get_variable("SCHEDULED_TASKS")["return"]
			if self.scheduler_var!=self.count:
				self.count=self.scheduler_var
				self.process_tasks()
			else:
				time.sleep(1)

	def process_tasks(self,data=None):
		self._debug("Scheduling tasks2")
		today=date.today()
		prefixes={'remote':True,'local':False}
		tasks={}
		try:
			socket.gethostbyname('server')
		except:
				prefixes={'local':False}
		for prefix,sw_remote in prefixes.items():
			if prefix=='remote':
				plugin="SchedulerServer"
				method="get_remote_tasks"
				proxy=n4dclient.Proxy(self.n4dclient,plugin,method)
				tasks=proxy.call()
			else:
				plugin="SchedulerServer"
				method="get_local_tasks"
				proxy=n4dclient.Proxy(self.n4dclient,plugin,method)
				tasks=proxy.call()

			#Delete files
			for f in os.listdir(self.cron_dir):
				if f.startswith(prefix):
					os.remove(self.cron_dir+'/'+f)
			#Create the cron files
			for name in tasks.keys():
				task_names={}
				self._debug("Processing task: %s"%name)
				for serial in tasks[name].keys():
					self._debug("Item {}".format(serial))
					sw_pass=False
					if 'autoremove' in tasks[name][serial]:
						if (tasks[name][serial]['mon'].isdigit()):
							mon=int(tasks[name][serial]['mon'])
							if mon<today.month:
								sw_pass=True
						if sw_pass==False:
							if (tasks[name][serial]['dom'].isdigit()):
								dom=int(tasks[name][serial]['dom'])
								if dom<today.day:
									sw_pass=True
					if sw_pass:
						continue
					self._debug("Scheduling {}".format(name))
					fname=name.replace(' ','_')
					task_names[fname]=tasks[name][serial].copy()
					self._write_crontab_for_task(task_names,prefix)
		#Launch refresh signal to gui
		if os.path.isfile(self.pidfile):
			with open(self.pidfile,'r') as p_file:
				pid=p_file.read()
				self._debug("Sending signal to %s"%pid)
				try:
					os.kill(int(pid),signal.SIGUSR1)
				except Exception as e:
					print("{}".format(e))
					pass
		return n4d.responses.build_successful_call_response()

	#def process_tasks

	def _write_crontab_for_task(self,ftask,prefix):
		cron_array=[]
		for task_name,task_data in ftask.items():
			self._debug("Writing data %s: %s"%(task_name,task_data))
			fname=self.cron_dir+'/'+prefix+task_name.replace(' ','_')
			m=task_data['m']
			h=task_data['h']
			dom=task_data['dom']
			mon=task_data['mon']
			if '/' in m:
				m=m.replace('0/','*/')
			if '/' in h:
				h=h.replace('0/','*/')
			if '/' in dom:
				dom=dom.replace('1/','*/')
			if '/' in mon:
				mon=mon.replace('1/','*/')
			cron_task=("%s %s %s %s %s root %s"%(m,h,dom,mon,task_data['dow'],u""+task_data['cmd']))
			if 'holidays' in task_data.keys():
				if task_data['holidays']:
					cron_task=("%s %s %s %s %s root %s && %s"%(m,h,dom,mon,task_data['dow'],self.holidays_shell,u""+task_data['cmd']))
			cron_array.append(cron_task)
			if task_data:
				if os.path.isfile(fname):
					mode='a'
				else:
					mode='w'
				with open(fname,mode) as data:
					if mode=='w':
						data.write('#Scheduler tasks\n')
						data.write('SHELL=/bin/bash\n')
						data.write('PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin\n')
						data.write('DISPLAY=:0\n')
						#Get authority file
						xauth=""
						for f in os.listdir("/var/run/sddm"):
							if f.startswith("{"):
								xauth="/var/run/sddm/%s"%f
						data.write('XAUTHORITY=%s\n'%xauth)
						if 'https_proxy' in os.environ.keys():
							https_proxy=os.environ['https_proxy']
							data.write('https_proxy=%s\n'%https_proxy)
						if 'http_proxy' in os.environ.keys():
							http_proxy=os.environ['http_proxy']
							data.write('http_proxy=%s\n'%http_proxy)
					for cron_line in cron_array:
						data.write("{}\n".format(cron_line))
	#def _write_crontab_for_task

	def _n4d_connect(self,server,user="",pwd=""):
		if not server.startswith("http"):
			server="https://{}".format(server)
		if len(server.split(":")) < 3:
				server="{}:9779".format(server)
			
		if user:
			return(n4dclient.Client(server,user,pwd))
		else:
			return(n4dclient.Client(server))
	#def _n4d_connect
