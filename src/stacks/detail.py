#!/usr/bin/python3
import sys
import os,shutil
import subprocess
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QHBoxLayout,QTableWidget,QHeaderView,QVBoxLayout,QLineEdit,QComboBox,QCheckBox,QScrollArea,QDialog,QSizePolicy
from PySide2 import QtGui
from PySide2.QtCore import Qt,QSize,Signal
from  appconfig import appConfig 
from QtExtraWidgets import QTableTouchWidget, QCheckableComboBox, QStackedWindowItem
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"MENU":_("Advance schedule"),
	"DESC":_("Advanced scheduling for expert users"),
	"TOOLTIP":_("Add scheduled tasks"),
	"CMD":_("Task"),
	"USERCRON":_("User's cron"),
	"SYSCRON":_("System cron"),
	"ATJOB":_("At job"),
	"ATNOTMOD":_("This at job can't be modified"),
	"MONTHLY":_("Monthly"),
	"DAILY":_("Daily"),
	"HOURLY":_("Hourly"),
	"MONTH_SCHED":_("Months"),
	"DAY_SCHED":_("Days"),
	"HOUR_SCHED":_("Hours"),
	"MINUTE_SCHED":_("Minute"),
	"DOW_SCHED":_("Select weekdays"),
	"DOW_SELECT":_("Weekdays"),
	"DELETE":_("Delete"),
	"CANCEL":_("Cancel"),
	"CONFIRM":_("Sure?"),
	"NOTCMD":_("not found"),
	"MALFORMED":_("Jobs can run only on fixed dates"),
	"LBLCMD":_("Write or select a command")
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

DAYS={"Monday":_("Monday"),
	"Tuesday":_("Tuesday"),
	"Wednesday":_("Wednesday"),
	"Thursday":_("Thursday"),
	"Friday":_("Friday"),
	"Saturday":_("Saturday"),
	"Sunday":_("Sunday")
	}

class detail(QStackedWindowItem):
	def __init_stack__(self):
		self.dbg=True
		self._debug("detail Load")
		self.setProps(shortDesc=i18n.get("MENU"),
			longDesc=i18n.get("DESC"),
			icon="address-book-new",
			tooltip=i18n.get("TOOLTIP"),
			index=3,
			visible=True)
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('address-book-new')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=3
		self.enabled=True
		self.level='user'
		self.scheduler=taskscheduler.TaskScheduler()
		self.appconfig=appConfig.appConfig()
		self.appconfig.setConfig(confDirs={'system':os.path.join('/usr/share',"taskscheduler"),'user':os.path.join(os.environ['HOME'],'.config',"taskscheduler")},confFile="taskscheduler.conf")
		self.task={}
		self.currentTaskData={}
	#def __init__
	
	def __initScreen__(self):
		self.lay=QGridLayout()
		scr=QScrollArea()
		scr.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		scr.setWidgetResizable(True)
		scr.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Expanding))
		wdg=QWidget()
		wdg.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Expanding))
		lay=QGridLayout()
		wdg.setLayout(lay)
		lay.addWidget(QLabel(i18n.get("CMD")),0,1,1,1)
		self.cmbCmd=QComboBox()
		self.cmbCmd.setEditable(True)
		lay.addWidget(self.cmbCmd,0,0,1,2)
		self.hours=self._drawDateTimeWidget("HOUR_SCHED","HOURLY",0,24)
		self.hours.adjustSize()
		lay.addWidget(self.hours,1,0,1,1)
		self.minutes=self._drawMinutes()
		self.minutes.adjustSize()
		lay.addWidget(self.minutes,1,1,1,1)
		self.btnDelete=QPushButton(i18n.get("DELETE"))
		self.btnDelete.clicked.connect(self._delTask)
		lay.addWidget(self.btnDelete,1,1,1,1,Qt.AlignTop|Qt.AlignRight)
		self.cmbType=QComboBox()
		self.cmbType.addItem(i18n.get("USERCRON"))
		self.cmbType.addItem(i18n.get("SYSCRON"))
		self.cmbType.addItem(i18n.get("ATJOB"))
		lay.addWidget(self.cmbType,1,1,1,1,Qt.AlignTop|Qt.AlignRight)
		self.months=self._drawDateTimeWidget("MONTH_SCHED","MONTHLY",1,13)
		self.months.adjustSize()
		lay.addWidget(self.months,2,0,1,1)
		self.days=self._drawDateTimeWidget("DAY_SCHED","DAILY",1,32)
		self.days.adjustSize()
		lay.addWidget(self.days,2,1,1,1)
		lay.setRowStretch(0,1)
		scr.setWidget(wdg)
		self.lay.addWidget(scr,0,0,1,1)
		scr.setMinimumWidth(self.hours.width()*1.4)
		scr.adjustSize()
		self.setLayout(self.lay)
		self.btnAccept.clicked.connect(self.writeConfig)
		return(self)
	#def _load_screen

	def initScreen(self):
		self.task={}

	def updateScreen(self):
		self._clearScreen()
		if (self.task.get("cmd","")!=""):
			self.cmbCmd.addItem(self.task.get("cmd"))
			self.cmbCmd.setCurrentText(self.task.get("cmd"))
		else:
			cmds=self._loadCommands()
			self.cmbCmd.setPlaceholderText(i18n.get("LBLCMD"))
			for cmd in cmds:
				if len(cmd)>0:
					self.cmbCmd.addItem(cmd)
			self.cmbCmd.setCurrentIndex(-1)
		data=self.task.get("raw","")
		ldata=data.split(" ")
		if len(ldata)>1:
			self._loadDataFromTask(data)
		self.task={}
	#def _udpate_screen

	def _drawDateTimeWidget(self,desc,desc2,minRange,maxRange):
		wdg=QWidget()
		wdg.setObjectName("cell")
		wdg.setStyleSheet("#cell{border: 1px solid #AAAAAA;}")
		lay=QGridLayout()
		lay.addWidget(QLabel(i18n.get(desc)),0,0,1,2,Qt.AlignTop|Qt.AlignCenter)
		maxCols=int(maxRange/5)
		maxCols=int(maxCols) + bool(maxCols%1)
		col=0
		row=1
		for i in range(minRange,maxRange):
			text=(str(i))
			if desc2=="MONTHLY":
				text=MONTHS.get(i)
			btn=QPushButton(text)
			btn.setCheckable(True)
			btn.setMaximumWidth(64)
			lay.addWidget(btn,row,col,Qt.AlignTop|Qt.AlignCenter)
			col+=1
			if col>maxCols:
				col=0
				row+=1
		chk=QCheckBox(i18n.get(desc2))
		if desc2=="DAILY":
			cmbDay=QCheckableComboBox()
			cmbDay.setText(i18n.get("DOW_SCHED"))
			for key,item in DAYS.items():
				cmbDay.addItem(item)
			if col>=maxCols-2:
				row+=1
				col=0
			else:
				col+=1
			lay.addWidget(cmbDay,row,col,1,maxCols-col+1)
			#lay.addWidget(chk,row,5,1,1,Qt.AlignRight|Qt.AlignBottom)
		#else:
		#	lay.addWidget(chk,row,0,1,6,Qt.AlignRight)
		lay.setSpacing(0)
		lay.setContentsMargins(3,3,3,3)
		wdg.setLayout(lay)
		return(wdg)
	#def _drawDateTimeWidget

	def _drawMinutes(self):
		wdg=QWidget()
		lay=QGridLayout()
		lay.addWidget(QLabel(i18n.get("MINUTE_SCHED")),0,0)
		cmb=QComboBox()
		for i in range(0,60,5):
			cmb.addItem(str(i).zfill(2))
		lay.addWidget(cmb,1,0,Qt.AlignTop)
		wdg.setLayout(lay)
		return(wdg)

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

	def _loadDataFromTask(self,data):
		(m,h,mon,dom,dow)=["*","*","*","*","*"]
		if len(data)>3:
			(m,h,dom,mon,dow)=data.split(" ")[0:5]
		if h=="*":
			h="0-24"
		if dom=="*":
			dom="1-32"
		if mon=="*":
			mon="1-13"
		if dow=="*":
			dow="1-7"
		processData={self.minutes:{"m":m},self.hours:{"h":h},self.days:{"dom":dom,"dow":dow},self.months:{"mon":mon}}
		for wdg,dataset in processData.items():
			self._setWidgetData(wdg,dataset)
		for i in self.minutes.findChildren(QComboBox):
			if i.findText(m)<0:
				i.addItem(m)
			i.setCurrentText(m)
	#def _loadDataFromTask

	def _setWidgetData(self,wdg,dataset):
		for key,data in dataset.items():
			active=self.scheduler._processCronField(str(data),0,0)
			#for item in str(data).split(","):
			#	if ("-") in item:
			#		ranged=item.split("-")
			#		for d in range(int(ranged[0]),int(ranged[-1])+1):
			#			active.append(str(d))
			#	else:
			#		if item.isdigit():
			#			active.append(str(int(item)))
			#		else:
			#			active.append(item)
			for i in wdg.findChildren(QPushButton):
				if key=="dow":
					break
				text=i.text()
				if not text.isdigit():
					for month,desc in MONTHS.items():
						if desc==text:
							text=str(month)
							break
				if text in active:
					i.setDown(True)
					i.setChecked(True)
				else:
					i.setDown(False)
					i.setChecked(False)
			for i in wdg.findChildren(QComboBox):
				if not isinstance(i,QCheckableComboBox) and key=="dom":
					if active[0].isdigit():
						i.setCurrentText(active[0])
				elif key=="dow":
					if len(active)>0 and len(active)<7:
						i.setText("{}: {}".format(i18n.get("DOW_SELECT"),",".join(active)))
					else:
						i.setText(i18n.get("DOW_SCHED"))
					for idx in active:
						i.setState(int(idx),True)
	#def _setWidgetData

	def _reset_screen(self):
		self.task=self.currentTaskData
		self.updateScreen()
	#def _reset_screen

	def _clearScreen(self):
		self.cmbType.setVisible(False)
		if len(self.task)==0:
			self.btnDelete.setVisible(False)
			self.cmbType.setVisible(True)
			self.cmbCmd.setEnabled(True)
			self.cmbType.setEnabled(True)
		self.cmbCmd.clear()
		processWdg=[self.minutes,self.hours,self.days,self.months]
		for wdg in processWdg:
			for i in wdg.findChildren(QPushButton):
				i.setDown(False)
				i.setChecked(False)
			for i in wdg.findChildren(QComboBox):
				if isinstance(i,QCheckableComboBox):
					for idx in range(1,i.count()):
						i.setState(idx,False)
					i.setText(i18n.get("DOW_SCHED"))
				else:
					i.clear()
					for idx in range(0,60,5):
						i.addItem(str(idx).zfill(2))
					i.setCurrentText("00")
	#def _clearScreen

	def setParms(self,*args):
		self.task=args[0]
		self.currentTaskData=args[0]
		self.btnDelete.setVisible(True)
		self.cmbCmd.setEnabled(False)
		self.cmbType.setEnabled(False)
	#def setParms

	def _addCmdToHistory(self,cmd):
		self.refresh=True
		config=self.appconfig.getConfig("user")
		userconf=config.get("user")
		usercmd=userconf.get("cmd",[])
		if cmd not in usercmd and len(cmd)>0:
			usercmd.append(cmd)
			self.appconfig.saveChanges("cmd",usercmd,level="user")
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

	def _delTask(self):
		dlg=QDialog()
		lay=QGridLayout()
		dlg.setLayout(lay)
		lblQ=QLabel("{0} <strong>{1}</strong><br>{2}".format(i18n.get("DELETE"),self.currentTaskData.get("cmd"),i18n.get("CONFIRM")))
		lay.addWidget(lblQ,0,0,1,2)
		btn_ok=QPushButton(i18n.get("DELETE"))
		btn_ok.clicked.connect(dlg.accept)
		btn_cancel=QPushButton(i18n.get("CANCEL"))
		btn_cancel.clicked.connect(dlg.reject)

		lay.addWidget(btn_ok,1,0,1,1,Qt.AlignRight)
		lay.addWidget(btn_cancel,1,1,1,1,Qt.AlignLeft)
		if dlg.exec_():
			raw=self.currentTaskData.get("raw","")
			if len(raw)>0:
				if len(self.currentTaskData.get("atid",""))>0:
					self.scheduler.removeFromAt(self.currentTaskData.get("atid"))
				else:
					cronF=self.currentTaskData.get("file","")
					if len(cronF)>0:
						self.scheduler.removeFromSystemCron(raw,cronF)
					else:
						self.scheduler.removeFromCron(raw)
			self.changes=False
			self.optionChanged=[]
			self.currentTaskData={}
			self.parent.setCurrentStack(1)
	#def _delTask

	def _readWidgetData(self,key,wdg):
		values=[]
		allEnabled=True
		for i in wdg.findChildren(QPushButton):
			if i.isChecked()==True:
				data=i.text()
				if not data.isdigit():
					for dmon,mon in MONTHS.items():
						if mon==data:
							data=dmon
				values.append(str(data))
			else:
				allEnabled=False
		for i in wdg.findChildren(QComboBox):
			if isinstance(i,QCheckableComboBox):
				if key=="dow":
					values=[]
					items=i.getItems()
					for item in items:
						if item.checkState() == Qt.Checked:
							values.append(item.index().row())
						elif item.index().row()>0:
							allEnabled=False
			elif key=="m":
				allEnabled=False
				values.append(str(int(i.currentText())))
		return(values,allEnabled)
	#def _readWidgetData

	def _readScreen(self,alias={}):
		processWdg={"m":self.minutes,"h":self.hours,"dom":self.days,"mon":self.months,"dow":self.days}
		processInfo={"m":[],"h":[],"dom":[],"mon":[],"dow":[]}
		for key,wdg in processWdg.items():
			allEnabled=True
			values,allEnabled=self._readWidgetData(key,wdg)
			if allEnabled==True or len(values)==0:
				values=["*"]
			processInfo[key]=self._generateCronRegex(values)

		processInfo["cmd"]=self.cmbCmd.currentText()
		if processInfo["cmd"] in alias.keys():
			processInfo["cmd"]=alias[processInfo["cmd"]]
		cmdName=processInfo["cmd"].split(" ")[0]
		if os.path.isfile(cmdName)==False and cmdName[0].isalnum():
			fullcmd=shutil.which(os.path.basename(cmdName))
			if fullcmd:
				processInfo["cmd"]=" ".join([fullcmd]+processInfo["cmd"].split(" ")[1:])
		return(processInfo)
	#def _readScreen

	def writeConfig(self):
		config=self.appconfig.getConfig("user")
		cron=[]
		processInfo=self._readScreen(config.get("user",{}).get("alias",{}))
		cmdName=processInfo["cmd"].split(" ")[0]
		if os.path.isfile(cmdName)==False and cmdName[0].isalnum():
			fullcmd=shutil.which(os.path.basename(cmdName))
			if fullcmd:
				processInfo["cmd"]=" ".join([fullcmd]+processInfo["cmd"].split(" ")[1:])
				cmdName=processInfo["cmd"].split(" ")[0]
			if os.path.isfile(cmdName)==False and  cmdName[0].isalnum():
				if len(self.currentTaskData.get("atid",""))>0:
					self.showMsg("{}".format(i18n.get("ATNOTMOD")))
				else:
					self.showMsg("{} {}".format(cmdName,i18n.get("NOTCMD")))
				return ()
		if len(self.currentTaskData)>0:
			self.task=self.currentTaskData.copy()
		if len(processInfo["cmd"])<1:
			return
		if not processInfo["cmd"] in config.get("user",{}).get("alias",{}).keys():
			self._addCmdToHistory(processInfo["cmd"])
		cron.append(processInfo)
		cronF=""
		res=None
		if len(self.task.get("atid",""))>0 or self.cmbType.currentIndex()==2:
			if not (self.scheduler.addAtJob(cron[0].get("m"),cron[0].get("h"),cron[0].get("dom"),cron[0].get("mon"),cron[0].get("cmd"))):
				field="Error"
				a={"m":"MINUTE_SCHED","h":"HOUR_SCHED","dom":"DAY_SCHED","mon":"MONTH_SCHED"}
				for i in ["m","h","dom","mon"]:
					if str(cron[0].get(i)).isdigit()==False:
						field=i18n.get(a[i])
						break

				self.showMsg("{}: {}".format(field,i18n.get("MALFORMED")))
				return()
			elif len(self.task.get("atid",""))>0:
				self.scheduler.removeFromAt(self.task.get("atid"))
		else:
			if self.task.get("file","")!="":
				cronF=self.task["file"]
			elif self.cmbType.currentIndex()==1:
				cronF=os.path.join("/","etc","cron.d","taskscheduler")
			res=self.scheduler.cronFromJson(cron,self.task.get("raw",""),cronF)
		if res==True:
			self.currentTaskData=processInfo
			self.updateScreen()
			self.parent.setCurrentStack(0)
	#def writeConfig
