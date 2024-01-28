#!/usr/bin/python3
import os,shutil
from PySide2.QtWidgets import QLabel, QPushButton,QGridLayout,QLineEdit,QComboBox,QCheckBox,QCalendarWidget,QDialog
from PySide2 import QtGui
from PySide2.QtCore import Qt,QDate
from appconfig import appConfig 
from QtExtraWidgets import QStackedWindowItem
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"MENU":_("Schedule task"),
	"DESC":_("Add schedule for task"),
	"TOOLTIP":_("Add scheduled tasks"),
	"CMD":_("Task"),
	"USERCRON":_("User's cron"),
	"SYSCRON":_("System cron"),
	"ATJOB":_("At job"),
	"ATNOTMOD":_("This at job can't be modified"),
	"MALFORMED":_("Jobs can run only on fixed dates"),
	"REPEAT":_("Repeat"),
	"NOREPEAT":_("No repeat"),
	"DELETE":_("Delete"),
	"CANCEL":_("Cancel"),
	"CONFIRM":_("Sure?"),
	"YEARLY":_("Yearly"),
	"MONTHLY":_("Monthly"),
	"DAILY":_("Daily"),
	"HOURLY":_("Hourly"),
	"MONTH_SCHED":_("Month"),
	"DAY_SCHED":_("Day"),
	"HOUR_SCHED":_("Hour"),
	"MINUTE_SCHED":_("Minute")
	}

MONTHS={1:_("Jan"),
	2:_("Feb"),
	3:_("Mar"),
	4:_("Apr"),
	5:_("May"),
	6:_("Jun"),
	7:_("Jul"),
	8:_("Aug"),
	9:_("Sep"),
	10:_("Oct"),
	11:_("Nov"),
	12:_("Dec")
	}

class simple(QStackedWindowItem):
	def __init_stack__(self):
		self.dbg=True
		self._debug("detail Load")
		self.scheduler=taskscheduler.TaskScheduler()
		self.setProps(shortDesc=i18n.get("MENU"),
			longDesc=i18n.get("DESC"),
			icon="appointment-new",
			tooltip=i18n.get("TOOLTIP"),
			index=2,
			visible=True)
		self.appconfig=appConfig.appConfig()
		self.appconfig.setConfig(confDirs={'system':'/usr/share/taskscheduler','user':'{}/.config/taskscheduler'.format(os.environ['HOME'])},confFile="alias.conf")
		self.appconfig.setLevel("user")
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('appointment-new')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=2
		self.enabled=True
		self.level='user'
		self.task={}
		self.currentTaskData={}
	#def __init__
	
	def __initScreen__(self):
		self.lay=QGridLayout()
		self.lay.addWidget(QLabel(i18n.get("CMD")),0,0,1,1,Qt.AlignRight|Qt.AlignBottom)
		self.cmbCmd=QComboBox()
		self.cmbCmd.setEditable(True)
		self.lay.addWidget(self.cmbCmd,0,1,1,3,Qt.AlignBottom)
		self.lay.addWidget(QLabel(i18n.get("HOUR_SCHED")),1,0,1,1,Qt.AlignBottom)
		self.hours=QComboBox()
		self.lay.addWidget(self.hours,2,0,1,1)#,Qt.AlignTop)
		self.lay.addWidget(QLabel(i18n.get("MINUTE_SCHED")),1,1,1,1,Qt.AlignBottom)
		self.minutes=QComboBox()
		self.lay.addWidget(self.minutes,2,1,1,1)#,Qt.AlignTop)
		self.lay.addWidget(QLabel(i18n.get("REPEAT")),1,2,1,1,Qt.AlignBottom)
		self.cmbRepeat=QComboBox()
		self.cmbRepeat.currentTextChanged.connect(self._lockCalendar)
		self.lay.addWidget(self.cmbRepeat,2,2,1,1,Qt.AlignTop)
		self.calendar=QCalendarWidget()
		self.lay.addWidget(self.calendar,3,1,1,2)#,Qt.AlignCenter)#|Qt.AlignCenter)
		self.btnDelete=QPushButton(i18n.get("DELETE"))
		self.btnDelete.clicked.connect(self._delTask)
		self.lay.addWidget(self.btnDelete,2,3,1,1,Qt.AlignRight)
		self.cmbType=QComboBox()
		self.cmbType.currentTextChanged.connect(self._lockRepeat)
		self.cmbType.addItem(i18n.get("USERCRON"))
		self.cmbType.addItem(i18n.get("SYSCRON"))
		self.cmbType.addItem(i18n.get("ATJOB"))
		self.cmbType.currentTextChanged.connect(self._lockRepeat)
		self.lay.addWidget(self.cmbType,2,3,1,1,Qt.AlignRight)
		self.lay.setRowStretch(0,0)
		self.lay.setRowStretch(1,0)
		self.lay.setRowStretch(2,1)
		self.lay.setRowStretch(3,2)
		self.setLayout(self.lay)
		self.btnAccept.clicked.connect(self.writeConfig)
		self.calendar.setMaximumHeight(self.sizeHint().height()/1)
		return(self)
	#def _load_screen

	def _lockCalendar(self):
		if self.cmbRepeat.currentText()==i18n.get("DAILY"):
			self.calendar.setEnabled(False)
		else:
			self.calendar.setEnabled(True)
	#def _lockCalendar

	def _drawRepeat(self):
		for i in ["DAILY","MONTHLY","YEARLY"]:
			text=i18n.get(i)
			self.cmbRepeat.addItem(text,userData=i)
	#def _drawRepeat

	def _lockRepeat(self):
		if self.cmbType.currentText()==i18n.get("ATJOB"):
			self.cmbRepeat.setEnabled(False)
		else:
			self.cmbRepeat.setEnabled(True)
	#def _lockRepeat

	def _drawHours(self):
		for i in range(0,24):
			self.hours.addItem(str(i).zfill(2))
	#def _drawHours

	def _drawMinutes(self):
		for i in range(0,60,5):
			self.minutes.addItem(str(i).zfill(2))
	#def _drawMinutes

	def _loadCommands(self):
		self.refresh=True
		cmds=[]
		config=self.appconfig.getConfig("user")
		cmds.extend(config.get("user",{}).get("alias",{}).keys())
		cmds.sort()
		hst=config.get("user",{}).get("cmd",[])
		hst.sort()
		cmds.extend(hst)
		return(cmds)
	#def _loadCommands

	def initScreen(self):
		self.task={}
	#def initScreen

	def updateScreen(self):
		self._clearScreen()
		if len(self.currentTaskData)>0:
			self.task=self.currentTaskData
			self.currentTaskData={}
		if len(self.task.get("atid",""))>0:
			self.cmbType.setVisible(False)
			self.btnDelete.setVisible(True)
			self.cmbRepeat.setEnabled(False)

		if (self.task.get("cmd","")!=""):
			self.cmbCmd.addItem(self.task.get("cmd"))
		else:
			cmds=self._loadCommands()
			for cmd in cmds:
				if len(cmd)>0:
					self.cmbCmd.addItem(cmd)
		self.cmbCmd.setCurrentText(self.task.get("cmd"))
		data=self.task.get("raw","")
		ldata=data.split(" ")
		if len(ldata)>1:
			self._loadDataFromTask(data)
		#self.task={}
	#def _udpate_screen

	def _loadDataFromTask(self,data):
		(m,h,mon,dom,dow)=["*","*","*","*","*"]
		if len(data)>3:
			(m,h,dom,mon,dow)=data.split(" ")[0:5]
		if m.isnumeric()==False:
			m="1"
		if h.isnumeric()==False:
			h="1"
		if dom.isnumeric()==False:
			dom="1"
		if mon.isnumeric()==False:
			mon="1"
		self.minutes.setCurrentText(m)
		self.hours.setCurrentText(h)
		qdate=QDate(self.calendar.yearShown(),int(mon),int(dom))
		self.calendar.setSelectedDate(qdate)
	#def _loadDataFromTask

	def _clearScreen(self):
		self.task={}
		self.cmbCmd.clear()
		processWdg=[self.minutes,self.hours,self.cmbRepeat]
		for wdg in processWdg:
			wdg.clear()
		self._drawHours()
		self._drawMinutes()
		self._drawRepeat()
		self.calendar.setSelectedDate(QDate.currentDate())
		self.cmbType.setVisible(True)
		self.btnDelete.setVisible(False)
		self.cmbRepeat.setEnabled(True)
	#def _resetScreen

	def setParms(self,*args):
		self.currentTaskData=args[0]
	#def setParms

	def _addCmdToHistory(self,cmd):
		self._debug(self.level)
		config=self.appconfig.getConfig("user")
		userconf=config.get("user")
		usercmd=userconf.get("cmd",[])
		if cmd not in usercmd:
			usercmd.append(cmd)
			self.appconfig.saveChanges("cmd",usercmd,level="user")
	#def _addCmdToHistory

	def _delTask(self):
		dlg=QDialog()
		lay=QGridLayout()
		dlg.setLayout(lay)
		lblQ=QLabel("{0} <strong>{1}</strong><br>{2}".format(i18n.get("DELETE"),self.task.get("cmd"),i18n.get("CONFIRM")))
		lay.addWidget(lblQ,0,0,1,2)
		btn_ok=QPushButton(i18n.get("DELETE"))
		btn_ok.clicked.connect(dlg.accept)
		btn_cancel=QPushButton(i18n.get("CANCEL"))
		btn_cancel.clicked.connect(dlg.reject)

		lay.addWidget(btn_ok,1,0,1,1,Qt.AlignRight)
		lay.addWidget(btn_cancel,1,1,1,1,Qt.AlignLeft)
		if dlg.exec_():
			raw=self.task.get("raw","")
			if len(raw)>0:
				if len(self.task.get("atid",""))>0:
					self.scheduler.removeFromAt(self.task.get("atid"))
				else:
					cronF=self.task.get("file","")
					if len(cronF)>0:
						self.scheduler.removeFromSystemCron(raw,cronF)
					else:
						self.scheduler.removeFromCron(raw)
			self.changes=False
			self.optionChanged=[]
			self.task={}
			self.parent.setCurrentStack(1)
	#def _delTask

	def _generateCronRegex(self,values):
		concat=[]
		last="-1"
		first="-1"
		for value in values:
			if value!="*":
				if int(value)-int(last)==1:
					if first=="-1":
						first=last
				else:
					if (first!="-1"):
						concat.append("{0}-{1}".format(first,last))
						if str(first) in concat:
							concat.remove(str(first))
						first="-1"
						last="-1"
			if first=="-1":
				concat.append(str(value))
			last=value
		if (first!="-1"):
			concat.append("{0}-{1}".format(first,last))
			if str(first) in concat:
				concat.remove(str(first))
		cronRegex=",".join(concat)
		return(cronRegex)
	#def _generateRanges

	def _readScreen(self,alias={}):
		processInfo={}
		processInfo["cmd"]=self.cmbCmd.currentText()
		if processInfo["cmd"] in alias.keys():
			processInfo["cmd"]=alias[processInfo["cmd"]]
		cmdName=processInfo["cmd"].split(" ")[0]
		if os.path.isfile(cmdName)==False and cmdName[0].isalnum():
			fullcmd=shutil.which(os.path.basename(cmdName))
			if fullcmd:
				processInfo["cmd"]=" ".join([fullcmd]+processInfo["cmd"].split(" ")[1:])
		processInfo["dow"]="*"
		processInfo["m"]=self.minutes.currentText()
		h=self.hours.currentText()
		date=self.calendar.selectedDate()
		dom=date.day()
		mon=date.month()
		if self.cmbRepeat.isEnabled():
			repeat=self.cmbRepeat.currentData()
			if repeat=="HOURLY":
				h="*"
				dom="*"
				mon="*"
			elif repeat=="DAILY":
				dom="*"
				mon="*"
			elif repeat=="MONTHLY":
				mon="*"
		processInfo["h"]=h
		processInfo["dom"]=dom
		processInfo["mon"]=mon
		return(processInfo)
	#def _readScreen

	def writeConfig(self):
		config=self.appconfig.getConfig("user")
		processInfo=self._readScreen(config.get("user",{}).get("alias",{}))
		cron=[]
		res=None
		if len(processInfo)>0:
			cmdName=processInfo["cmd"].split(" ")[0]
			if os.path.isfile(cmdName)==False and  cmdName[0].isalnum():
				if len(self.task.get("atid",""))>0:
					self.showMsg("{}".format(i18n.get("ATNOTMOD")))
				else:
					self.showMsg("{} {}".format(cmdName,i18n.get("NOTCMD")))
				return ({})
			if not processInfo["cmd"] in config.get("user",{}).get("alias",{}).keys():
				self._addCmdToHistory(processInfo["cmd"])
			cron.append(processInfo)
			if self.cmbType.currentIndex()<=1:
				cronF=""
				if self.cmbType.currentIndex()==1:
					cronF=os.path.join("/","etc","cron.d","taskscheduler")
				res=self.scheduler.cronFromJson(cron,self.task.get("raw",""),cronF)
			else:
				if not (self.scheduler.addAtJob(cron[0].get("m"),cron[0].get("h"),cron[0].get("dom"),cron[0].get("mon"),cron[0].get("cmd"))):
					self.showMsg("{}".format(cmdName,i18n.get("MALFORMED","ERROR")))
					return()
		self.updateScreen()
		self.parent.setCurrentStack(1)
	#def writeConfig

