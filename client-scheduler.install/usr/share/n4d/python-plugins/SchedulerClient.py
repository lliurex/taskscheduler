#!/usr/bin/env python
###
#
###

# -*- coding: utf-8 -*-
import os,socket
import threading
import time
from  datetime import date
import xmlrpclib as xmlrpc

class SchedulerClient():
	def __init__(self):
		self.cron_dir='/etc/cron.d'
		self.task_prefix='remote-' #Temp workaround->Must be declared on a n4d var
		self.cron_dir='/etc/cron.d'
		self.count=0
		self.dbg=0
		self.holidays_shell="/usr/bin/check_holidays.py"
		self.pidfile="/tmp/taskscheduler.pid"

	def startup(self,options):
		t=threading.Thread(target=self._main_thread)
		t.daemon=True
		t.start()

	def _debug(self,msg):
		if self.dbg:
			print("%s"%msg)

	def _main_thread(self):
		objects["VariablesManager"].register_trigger("SCHEDULED_TASKS","SchedulerClient",self.process_tasks)
		tries=10
		for x in range (0,tries):
			self.scheduler_var=objects["VariablesManager"].get_variable("SCHEDULED_TASKS")
			if self.scheduler_var!=self.count:
				self.count=self.scheduler_var
				self.process_tasks()
				break
			else:
				time.sleep(1)

	def process_tasks(self,data=None):
		self._debug("Scheduling tasks")
		today=date.today()
		prefixes={'remote':True,'local':False}
		tasks={}
		try:
			socket.gethostbyname('server')
		except:
				prefixes={'local':False}
		for prefix,sw_remote in prefixes.iteritems():
			if prefix=='remote':
				n4d=xmlrpc.ServerProxy("https://server:9779")
				tasks=n4d.get_remote_tasks("","SchedulerServer")['data'].copy()
			else:
				n4d=xmlrpc.ServerProxy("https://localhost:9779")
				tasks=n4d.get_local_tasks("","SchedulerServer")['data'].copy()

			#Delete files
			for f in os.listdir(self.cron_dir):
				if f.startswith(prefix):
					os.remove(self.cron_dir+'/'+f)
			#Create the cron files
			for name in tasks.keys():
				task_names={}
				self._debug("Processing task: %s"%name)
				for serial in tasks[name].keys():
					self._debug("Item %s"%serial)
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
					self._debug("Scheduling %s"%name)
					fname=name.replace(' ','_')
					task_names[fname]=tasks[name][serial].copy()
					self._write_crontab_for_task(task_names,prefix)
		#Launch refresh signal to gui
		if os.path.isfile(self.pidfile):
			with open(self.pidfile,'r') as p_file:
				pid=p_file.read()
				try:
					os.kill(int(pid),signal.SIGUSR1)
				except:
					pass

	#def process_tasks

	def _write_crontab_for_task(self,ftask,prefix):
		cron_array=[]
		for task_name,task_data in ftask.iteritems():
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
						data.write('XAUTHORITY=/var/run/lightdm/root/:0\n')
						if 'https_proxy' in os.environ.keys():
							https_proxy=os.environ['https_proxy']
							data.write('https_proxy=%s\n'%https_proxy)
						if 'http_proxy' in os.environ.keys():
							http_proxy=os.environ['http_proxy']
							data.write('http_proxy=%s\n'%http_proxy)
					for cron_line in cron_array:
						data.write(cron_line.encode('utf8')+"\n")
	#def _write_crontab_for_task

