#!/usr/bin/python3
import sys
import os
import subprocess
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QTableWidget,QHeaderView,QAbstractScrollArea
from PySide2 import QtGui
from PySide2.QtCore import Qt,QSize,Signal
from appconfig.appConfigStack import appConfigStack as confStack
import appconfig.appconfigControls as appconfigControls
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"DESCRIPTION":_("Dashboard"),
	"DESCRIPTION_MENU":_("Take a look to next scheduled tasks"),
	"TOOLTIP":_("Show scheduled tasks ordered by next execution time"),
	"REST":_("Next in"),
	"USERCRON":_("User cron")
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
		cmd=task.get("cmd","")[0:40]
		if alias:
			for key,item in alias.items():
				if task.get('cmd').strip()==item.strip():
					cmd=key
					break
		text="\u200b".join(cmd)
		self.label=QLabel()
		self.label.setText("<strong>{0}</strong>".format(cmd))
		self.label.setToolTip(task.get("cmd"))
		self.label.setWordWrap(True)
		self.label.adjustSize()
		self.lay.addWidget(self.label,0,0,2,2,Qt.AlignLeft|Qt.AlignTop)
		self.lblDate=QLabel()
		self._setDate(task.get('next').split(" ")[1])
		self.lblDate.setToolTip("d:{0} m:{1}".format(task.get("raw","* * * *").split()[2],task.get("raw","* * * *").split()[3]))
		self.lblDate.setWordWrap(True)
		self.lblDate.adjustSize()
		self.lay.addWidget(self.lblDate,2,0,1,1,Qt.AlignLeft)
		self.lblTime=QLabel()
		self._setTime(task.get('next').split(" ")[0])
		#self.lblTime.setToolTip(self.lblTime.text())
		self.lblTime.setToolTip("m:{0} h:{1}".format(task.get("raw","* * * *").split()[0],task.get("raw","* * * *").split()[1]))
		self.lblTime.setWordWrap(True)
		self.lblTime.adjustSize()
		self.lay.addWidget(self.lblTime,2,1,1,1,Qt.AlignRight)
		self.lblFile=QLabel()
		self.lblFile.setAlignment(Qt.AlignLeft)
		self.lblFile.setText(i18n.get("USERCRON"))
		if len(task.get("file",""))>0:
			self.lblFile.setText(os.path.basename(task.get("file")))
			self.lblFile.setToolTip(task.get("file"))
			icn=QtGui.QIcon.fromTheme("package-available-locked")
			self.setIcon(icn)
		self.lblFile.adjustSize()
		self.lay.addWidget(self.lblFile,3,0,1,2,Qt.AlignBottom)
		self.lblRest=QLabel()
		self.lblRest.setAlignment(Qt.AlignCenter)
		self._setRest(task.get('rest'))
		sched=self._formatTooltip(task.get("raw").split()[:5])
		self.lblRest.setToolTip("{}".format(sched))
		self.lblRest.adjustSize()
		self.lay.addWidget(self.lblRest,4,0,1,2,Qt.AlignCenter)
		self.setMinimumSize(self.sizeHint().width(),self._getHeight())
		self.adjustSize()
		self.setLayout(self.lay)
	#def __init__

	def _debug(self,msg):
		if self.dbg==True:
			print("Taskbutton {}".format(msg))

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

	def _setTime(self,time):
		self.lblTime.setText(time)
	#def _setTime

	def _setDate(self,date):
		(month,day)=date.split("-")
		#self.lblDate.setText("{0}<br>{1}".format(MONTHS.get(int(month)),day))
		self.lblDate.setText("{1} {0}".format(MONTHS.get(int(month)),day))
	#def _setDate

	def _setRest(self,rest):
		self.lblRest.setText("{0} {1}".format(i18n.get("REST"),rest[0:-3]))
	#set _setRest

	def getTask(self):
		return(self.task)

class dashboard(confStack):
	def __init_stack__(self):
		self.dbg=False
		self._debug("dashboard Load")
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('x-office-calendar')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=1
		self.enabled=True
		self.level='system'
		self.hideControlButtons()
		self.scheduler=taskscheduler.TaskScheduler()
	#def __init__
	
	def _load_screen(self):
		self.lay=QGridLayout()
		self.table=appconfigControls.QTableTouchWidget()
		self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.table.setShowGrid(False)
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().hide()
		self.lay.addWidget(self.table,0,0,1,1)
		self.setLayout(self.lay)
		return(self)
	#def _load_screen

	def updateScreen(self):
		maxH=[]
		cron=self.scheduler.getUserCron()
		#crond=self.scheduler.getSystemCron()
		cron.update(self.scheduler.getSystemCron())
		config=self.getConfig("user").get("user",{})
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

#		self.table.resizeColumnsToContents()
		if len(maxH)>=1:
			idx=-1
			maxH.sort()
			for i in range(0,self.table.rowCount()):
				self.table.setRowHeight(i,maxH[idx])
	#def _udpate_screen

	def _gotoTask(self):
		wdg=self.table.cellWidget(self.table.currentRow(),self.table.currentColumn())
		self.stack.gotoStack(idx=3,parms=wdg.getTask())
	#def _gotoTask

