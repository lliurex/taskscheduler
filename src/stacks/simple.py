#!/usr/bin/python3
import sys
import os,shutil
import subprocess
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QVBoxLayout,QTableWidget,QHeaderView,QVBoxLayout,QLineEdit,QComboBox,QCheckBox,QCalendarWidget
from PySide2 import QtGui
from PySide2.QtCore import Qt,QSize,Signal
from appconfig.appConfigStack import appConfigStack as confStack
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"DESCRIPTION":("Schedule task"),
	"DESCRIPTION_MENU":_("Add schedule for task"),
	"TOOLTIP":_("Add scheduled tasks"),
	"CMD":_("Task"),
	"USERCRON":_("User's cron"),
	"SYSCRON":_("System cron"),
	"REPEAT":_("Repeat"),
	"NOREPEAT":_("No repeat"),
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

class simple(confStack):
	def __init_stack__(self):
		self.dbg=True
		self._debug("detail Load")
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('appointment-new')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=2
		self.enabled=True
		self.level='user'
		self.scheduler=taskscheduler.TaskScheduler()
		self.task={}
	#def __init__
	
	def _load_screen(self):
		self.lay=QGridLayout()
		self.lay.addWidget(QLabel(i18n.get("CMD")),0,0,1,1,Qt.Alignment(0))
		self.cmbCmd=QComboBox()
		self.cmbCmd.setEditable(True)
		self.lay.addWidget(self.cmbCmd,0,1,1,3)
		self.lay.addWidget(QLabel(i18n.get("HOUR_SCHED")),2,0,1,1,Qt.AlignTop)
		self.hours=QComboBox()
		self.lay.addWidget(self.hours,3,0,1,1,Qt.AlignTop)
		self.lay.addWidget(QLabel(i18n.get("MINUTE_SCHED")),2,1,1,1,Qt.AlignTop)
		self.minutes=QComboBox()
		self.lay.addWidget(self.minutes,3,1,1,1,Qt.AlignTop)
		self.lay.addWidget(QLabel(i18n.get("REPEAT")),2,2,1,1,Qt.AlignTop)
		self.cmbRepeat=QComboBox()
		self.lay.addWidget(self.cmbRepeat,3,2,1,1,Qt.AlignTop)
		self.calendar=QCalendarWidget()
		self.lay.addWidget(self.calendar,2,3,3,2,Qt.AlignTop|Qt.AlignRight)
		self.cmbType=QComboBox()
		self.cmbType.addItem(i18n.get("USERCRON"))
		self.cmbType.addItem(i18n.get("SYSCRON"))
		self.lay.addWidget(self.cmbType,0,4,1,1,Qt.AlignRight)
		self.lay.setRowStretch(3,2)
		self.lay.setRowStretch(3,3)
		self.setLayout(self.lay)
		return(self)
	#def _load_screen

	def _drawRepeat(self):
		for i in ["NOREPEAT","HOURLY","DAILY","MONTHLY","YEARLY"]:
			text=i18n.get(i)
			self.cmbRepeat.addItem(text,userData=i)
	#def _drawHours

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
		config=self.getConfig("user")
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

	def _clearScreen(self):
		self.cmbCmd.clear()
		processWdg=[self.minutes,self.hours,self.cmbRepeat]
		for wdg in processWdg:
			wdg.clear()
		self._drawHours()
		self._drawMinutes()
		self._drawRepeat()
	#def _resetScreen

	def setParms(self,*args):
		self.task=args[0]
	#def setParms

	def _addCmdToHistory(self,cmd):
		self._debug(self.level)
		config=self.getConfig("user")
		userconf=config.get("user")
		usercmd=userconf.get("cmd",[])
		if cmd not in usercmd:
			usercmd.append(cmd)
			self.saveChanges("cmd",usercmd,level="user")
	#def _addCmdToHistory

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
		repeat=self.cmbRepeat.currentData()
		h=self.hours.currentText()
		if repeat=="HOURLY":
			h="*"
		processInfo["h"]=h
		date=self.calendar.selectedDate()
		dom=date.day()
		mon=date.month()
		if repeat=="DAILY":
			dom="*"
			mon="*"
		processInfo["dom"]=dom
		if repeat=="MONTHLY":
			mon="*"
		processInfo["mon"]=mon
		return(processInfo)
	#def _readScreen

	def writeConfig(self):
		config=self.getConfig("user")
		processInfo=self._readScreen(config.get("user",{}).get("alias",{}))
		if len(processInfo)>0:
			cmdName=processInfo["cmd"].split(" ")[0]
			if os.path.isfile(cmdName)==False and  cmdName[0].isalnum():
				self.showMsg("{} {}".format(cmdName,i18n.get("NOTCMD")))
				return ({})
			if not processInfo["cmd"] in config.get("user",{}).get("alias",{}).keys():
				self._addCmdToHistory(processInfo["cmd"])
			cronF=""
			if self.cmbType.currentIndex()==1:
				cronF=os.path.join("/","etc","cron.d","taskscheduler")
			self.scheduler.cronFromJson(processInfo,self.task.get("raw",""),cronF)
	#def writeConfig

