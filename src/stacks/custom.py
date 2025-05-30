#!/usr/bin/python3
import sys,os
import shutil
import subprocess
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QHBoxLayout,QTableWidget,QHeaderView,QVBoxLayout,QLineEdit,QTableWidgetItem,QComboBox
from PySide6 import QtGui
from PySide6.QtCore import Qt,QSize,Signal,QDate
from QtExtraWidgets import QTableTouchWidget, QStackedWindowItem
from appconfig import manager
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"MENU":_("Add commands"),
	"DESC":_("Add custom commands"),
	"TOOLTIP":_("Add custom commmands with aliases for later use"),
	"ALIAS":_("Command alias"),
	"ADD":_("Add"),
	"CMD":_("Full command"),
	"NOTCMD":_("no found")
	}

class custom(QStackedWindowItem):
	def __init_stack__(self):
		self.dbg=True
		self._debug("custom Load")
		self.appconfig=manager.manager(relativepath="taskscheduler",name="taskscheduler.json")
		#self.appconfig.setConfig(confDirs={'system':'/usr/share/taskscheduler','user':'{}/.config/taskscheduler'.format(os.environ['HOME'])},confFile="alias.conf")
		#self.appconfig.setLevel("user")
		self.scheduler=taskscheduler.TaskScheduler()
		self.setProps(shortDesc=i18n.get("MENU"),
			longDesc=i18n.get("DESC"),
			icon="document-edit",
			tooltip=i18n.get("TOOLTIP"),
			index=4,
			visible=True)
		self.enabled=True
		self.level='system'
		self.task={}
		self.btnAccept.clicked.connect(self.writeConfig)
	#def __init__
	
	def __initScreen__(self):
		self.lay=QGridLayout()
		self.inpAlias=QLineEdit()
		self.inpAlias.setPlaceholderText(i18n.get("ALIAS"))
		self.lay.addWidget(self.inpAlias,0,0,1,1,Qt.AlignLeft)
		self.cmbCmd=QComboBox()	
		self.cmbCmd.setEditable(True)
		self.cmbCmd.setPlaceholderText(i18n.get("CMD"))
		self.lay.addWidget(self.cmbCmd,0,1,1,1,Qt.Alignment(0))
		self.btnAdd=QPushButton(i18n.get("ADD"))
		self.btnAdd.clicked.connect(self._addAlias)
		self.lay.addWidget(self.btnAdd,0,2,1,1,Qt.Alignment(1))
		self.table=QTableWidget(1,2)
		self.table.setSelectionBehavior(QTableWidget.SelectRows)
		self.table.itemSelectionChanged.connect(self._loadRowData)
#		self.table.setShowGrid(False)
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().hide()
		self.lay.addWidget(self.table,1,0,1,3)
		self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
		self.setLayout(self.lay)
		self.btnAccept.clicked.connect(self.writeConfig)
	#def _load_screen

	def _loadRowData(self,*args):
		self.inpAlias.setText(self.table.item(self.table.currentRow(),0).text())
		self.cmbCmd.setCurrentText(self.table.item(self.table.currentRow(),1).text())
		print(args)

	def updateScreen(self):
		aliases=self._getAliases()
		commands=self._getHistory()
		self._resetScreen()
		for alias,cmd in aliases.items():
			self.table.setRowCount(self.table.rowCount()+1)
			self.table.setItem(self.table.rowCount()-1,0,QTableWidgetItem(alias))
			self.table.setItem(self.table.rowCount()-1,1,QTableWidgetItem(cmd))
		for cmd in commands:
			self.cmbCmd.addItem(cmd)
	#def _update_screen

	def _resetScreen(self):
		self.changes=False
		self.refresh=False
		self.inpAlias.setText("")
		self.cmbCmd.clear()
		self.table.clearContents()
		self.table.setRowCount(0)
	#def _resetScreen

	def _getAliases(self):
		config=self.appconfig.getConfig()
		commands=config.get("alias",{})
		return(commands)
	#def _getAliases

	def _addAlias(self):
		cmd=self.cmbCmd.currentText()
		cmdName=cmd.split(" ")[0]
		alias=self.inpAlias.text()
		if len(cmdName)==0 or len(alias)==0:
			return
		if os.path.isfile(cmdName)==False:
			fullcmd=shutil.which(os.path.basename(cmd.split(" ")[0]))
			if fullcmd:
				cmd=" ".join([fullcmd]+cmd.split(" ")[1:])
				cmdName=cmd.split(" ")[0]
		if os.path.isfile(cmdName)==False:
			self.showMsg("{} {}".format(cmdName,i18n.get("NOTCMD")))
			return
		f=self.table.findItems(alias,Qt.MatchExactly)
		if len(f)==0:
			self.table.setRowCount(self.table.rowCount()+1)
			self.table.setItem(self.table.rowCount()-1,0,QTableWidgetItem(alias))
			self.table.setItem(self.table.rowCount()-1,1,QTableWidgetItem(cmd))
		#if alias not in useralias.keys():
	#def _addAlias

	def _getHistory(self):
		self.refresh=True
		config=self.appconfig.getConfig()
		hst=config.get("cmd",[])
		hst.sort()
		return(hst)
	#def _getHistory

	def writeConfig(self):
		self._addAlias()
		useralias={"alias":{}}
		for row in range(0,self.table.rowCount()):
			alias=self.table.item(row,0).text()
			if alias in useralias or len(alias)<1:
				continue
			cmd=self.table.item(row,1).text()
			if len(cmd)<1:
				continue
			useralias["alias"].update({alias:cmd})
		self.appconfig.writeConfig(useralias)
		self.updateScreen()
	#def writeConfig
