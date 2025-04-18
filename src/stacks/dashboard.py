#!/usr/bin/python3
import sys
import os
import subprocess
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QTableWidget,QHeaderView,QAbstractScrollArea
from PySide6 import QtGui
from PySide6.QtCore import Qt,QSize,Signal
from QtExtraWidgets import QTableTouchWidget, QStackedWindowItem
from appconfig import manager
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"MENU":_("Dashboard"),
	"DESC":_("Take a look to next scheduled tasks"),
	"TOOLTIP":_("Show scheduled tasks ordered by next execution time"),
	"REST":_("Next in"),
	"USERCRON":_("User cron"),
	"NEWTASK":_("Schedule a new task"),
	"ATID":_("at job")
	}

MONTHS={1:_("January"),
	2:_("February"),
	3:_("March"),
	4:_("April"),
	5:_("May"),
	6:_("June"),
	7:_("July"),
	8:_("August"),
	9:_("September"),
	10:_("October"),
	11:_("November"),
	12:_("December")
	}

class taskButton(QPushButton):
	def __init__(self,task,alias=None,parent=None):
		QPushButton.__init__(self, parent)
		self.dbg=False
		self.task=task
		self.lay=QGridLayout()
		cmd=task.get("cmd","")
		if len(cmd)>50:
			cmd="{}...".format(cmd[0:50])
		if alias:
			for key,item in alias.items():
				#print("{} == {}".format(item,task.get("cmd")))
				if task.get('cmd').strip()==item.strip():
					cmd=key
					break
		text="\u200b".join(cmd)
		self.label=QLabel()
		self.label.setText("<strong>{0}</strong>".format(cmd))
		self.label.setToolTip(task.get("cmd"))
		self.label.setWordWrap(True)
		#self.label.adjustSize()
		self.lay.addWidget(self.label,0,0,2,2)#Qt.AlignLeft|Qt.AlignTop)
		self.lblDate=QLabel()
		self._setDate(task.get('next',"scheduled:Task new-Add").split(" ")[1])
		self.lblDate.setToolTip("d:{0} m:{1}".format(task.get("raw","* * * *").split()[2],task.get("raw","* * * *").split()[3]))
		self.lblDate.setWordWrap(True)
		self.lblDate.adjustSize()
		self.lay.addWidget(self.lblDate,2,0,1,1,Qt.AlignLeft)
		self.lblTime=QLabel()
		self._setTime(task.get('next',"scheduled:Task new-Add").split(" ")[0])
		#self.lblTime.setToolTip(self.lblTime.text())
		self.lblTime.setToolTip("m:{0} h:{1}".format(task.get("raw","* * * *").split()[0],task.get("raw","* * * *").split()[1]))
		self.lblTime.setWordWrap(True)
		self.lblTime.adjustSize()
		self.lay.addWidget(self.lblTime,2,1,1,1,Qt.AlignRight)
		self.lblFile=QLabel()
		self.lblFile.setAlignment(Qt.AlignLeft)
		self.lblFile.setText(i18n.get("USERCRON"))
		if len(task.get("file",""))>0:
			self.lblFile.setText(os.path.basename(task.get("file","")))
			self.lblFile.setToolTip(task.get("file"))
			icn=QtGui.QIcon.fromTheme( "folder-locked")
			self.setIcon(icn)
		elif len(task.get("atid",""))>0:
			self.lblFile.setText(i18n.get("ATID"))
			self.lblFile.setToolTip(task.get("file",""))
			icn=QtGui.QIcon.fromTheme( "clock")
			self.setIcon(icn)
		self.lblFile.adjustSize()
		self.lay.addWidget(self.lblFile,3,0,1,2,Qt.AlignBottom)
		self.lblRest=QLabel()
		self.lblRest.setAlignment(Qt.AlignCenter)
		self._setRest(task.get('rest',""))
		sched=self._formatTooltip(task.get("raw",i18n.get("NEWTASK")).split()[:5])
		self.lblRest.setToolTip("{}".format(sched))
		self.lblRest.adjustSize()
		self.lay.addWidget(self.lblRest,4,0,1,2,Qt.AlignCenter)
		self.setMinimumSize(self.sizeHint().width(),self._getHeight())
		self.setLayout(self.lay)
		blocked=["bellscheduler","lliurex"]
		for block in blocked:
			if block in self.lblFile.text().lower():
				self.setEnabled(False)
				break
		if task.get("raw","").startswith("@"):
			self.setEnabled(False)
		self.adjustSize()
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("Taskbutton {}".format(msg))
	#def _debug

	def _formatTooltip(self,textArray):
		tooltip=""
		labels=["m","h","dom","mon","dow"]
		sched=[]
		idx=0
		for text in textArray:
			lentext=len(text)
			if lentext>len(labels[idx]):
				labels[idx]=labels[idx].center(lentext)
			elif lentext<=len(labels[idx]):
				text=text.center(len(labels[idx])+idx)
			sched.append(text)
			idx+=1
		tooltip="{}\n{}".format("  ".join(labels),"  ".join(sched))
		return(tooltip)
	#def _formatTooltip

	def _getHeight(self):
		h=self.lblTime.geometry().height()+self.lblDate.geometry().height()+self.lblRest.geometry().height()+self.label.geometry().height()+self.lblFile.geometry().height()
		self._debug("******* SIZES for {} *****".format(self.label.text()))
		self._debug("Self: {}".format(self.size()))
		array=[self.lblTime,self.lblDate,self.lblRest,self.label,self.lblFile]
		geom=[]
		hint=[]
		h=0
		size=[]
		for i in array:
			geom.append(i.geometry())
			hint.append(i.sizeHint())
			size.append(i.size())
			h+=i.sizeHint().height()
		self._debug(geom)
		self._debug(hint)
		self._debug(size)
		self._debug("H: {}".format(h))
		return (h)
	#def _getHeight

	def _setTime(self,time):
		self.lblTime.setText(time)
	#def _setTime

	def _setDate(self,date):
		(month,day)=date.split("-")
		#self.lblDate.setText("{0}<br>{1}".format(MONTHS.get(int(month)),day))
		if month.isdigit():
			self.lblDate.setText("{1} {0}".format(MONTHS.get(int(month)),day))
		else:
			self.lblDate.setText("{1} {0}".format(month,day))
	#def _setDate

	def _setRest(self,rest):
		self.lblRest.setText("{0} {1}".format(i18n.get("REST"),rest[0:-3]))
	#set _setRest

	def getTask(self):
		return(self.task)
	#def getTask

class dashboard(QStackedWindowItem):
	def __init_stack__(self):
		self.dbg=True
		self._debug("dashboard Load")
		self.appconfig=manager.manager(relativepath="taskscheduler",name="taskscheduler.json")
		#self.appconfig.setConfig(confDirs={'system':'/usr/share/taskscheduler','user':'{}/.config/taskscheduler'.format(os.environ['HOME'])},confFile="alias.conf")
		#self.appconfig.setLevel("user")
		self.scheduler=taskscheduler.TaskScheduler()
		self.setProps(shortDesc=i18n.get("MENU"),
			longDesc=i18n.get("DESC"),
			icon="x-office-calendar",
			tooltip=i18n.get("TOOLTIP"),
			index=1,
			visible=True)
		self.enabled=True
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('x-office-calendar')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=1
		self.enabled=True
		self.level='system'
		self.hideControlButtons()
	#def __init__
	
	def __initScreen__(self):
		self.lay=QGridLayout()
		self.table=QTableTouchWidget()
		self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.table.setShowGrid(False)
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().hide()
		self.lay.addWidget(self.table,0,0,1,1)
		self.setLayout(self.lay)
	#def _load_screen

	def updateScreen(self):
		maxH=[]
		cron=self.scheduler.getUserCron()
		#crond=self.scheduler.getSystemCron()
		syscron=self.scheduler.getSystemCron()
		for epoch,data in syscron.items():
			while epoch in cron.keys():
				epoch+=1
			cron[epoch]=data
		atjobs=self.scheduler.getAt()
		for epoch,data in atjobs.items():
			while epoch in cron.keys():
				epoch+=1
			cron[epoch]=data

		config=self.appconfig.getConfig()
		alias=config.get("alias")
		self.table.setRowCount(0)
		self.table.setRowCount(1)
		self.table.setColumnCount(0)
		self.table.setColumnCount(4)
		self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
		self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
		self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
		self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.Stretch)
		row=0
		col=0
		btnTask=None
		cronSorted=dict(sorted(cron.items()))
		for rest,line in cronSorted.items():
			btnTask=taskButton(line,alias)
			btnTask.clicked.connect(self._gotoTask)
			self.table.setCellWidget(row,col,btnTask)
			col+=1
			if col>=4:
				col=0
				row+=1
				self.table.setRowCount(row+1)
			maxH.append(btnTask._getHeight())
		if col+row==0:
			btnTask=QPushButton("+")
			self.table.setCellWidget(row,col,btnTask)
			btnTask.setStyleSheet("font-size: 2em;font: bold; margin:6px;padding:6px;")
			btnTask.setMaximumWidth(128)
			btnTask.setMinimumHeight(btnTask.width()*2)
			btnTask.clicked.connect(self._gotoTask)
			self.table.resizeRowsToContents()
			self.table.resizeColumnsToContents()
		if len(maxH)>=1:
			idx=-1
			maxH.sort()
			for i in range(0,self.table.rowCount()):
				self.table.setRowHeight(i,maxH[idx])
	#def _udpate_screen

	def _gotoTask(self):
		wdg=self.table.cellWidget(self.table.currentRow(),self.table.currentColumn())
		if isinstance(wdg,taskButton):
			task=wdg.getTask()
			if len(task.get("atid",""))>0:
			#self.stack.gotoStack(idx=3,parms=wdg.getTask())
				self.parent.setCurrentStack(2,parms=task)
			else:
				self.parent.setCurrentStack(3,parms=task)
	#def _gotoTask

