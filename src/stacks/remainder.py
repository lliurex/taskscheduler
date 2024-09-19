#!/usr/bin/python3
import sys
import os
import subprocess
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QPushButton,QGridLayout,QHBoxLayout,QTableWidget,QHeaderView,QVBoxLayout,QLineEdit
from PySide2 import QtGui
from PySide2.QtCore import Qt,QSize,Signal
from QtExtraWidgets import QStackedWindowItem
import taskscheduler.taskscheduler as taskscheduler

import gettext
_ = gettext.gettext

i18n={"DESC":("Add remainder"),
	"MENU":_("Add remainder"),
	"TOOLTIP":_("One-shot notifications/alarms")
	}

class remainder(QStackedWindowItem):
	def __init_stack__(self):
		self.dbg=False
		self._debug("custom Load")
		self.scheduler=taskscheduler.TaskScheduler()
		self.setProps(shortDesc=i18n.get("MENU"),
			longDesc=i18n.get("DESC"),
			icon="dialog-password",
			tooltip=i18n.get("TOOLTIP"),
			index=3,
			visible=True)
		self.description=i18n.get("DESCRIPTION")
		self.menu_description=i18n.get("DESCRIPTION_MENU")
		self.icon=('dialog-password')
		self.tooltip=i18n.get("TOOLTIP")
		self.index=3
		self.enabled=False
		self.level='system'
		self.task={}
	#def __init__
	
	def __initScreen__(self):
		self.lay=QVBoxLayout()
		self.table=QTableWidget(1,2)
		self.table.setShowGrid(False)
		self.table.verticalHeader().hide()
		self.table.horizontalHeader().hide()
		self.lay.addWidget(self.table)
		self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
		self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
		self.setLayout(self.lay)
	#def _load_screen

	def updateScreen(self):
		commands=self._getCustomCommands()
		pass
	#def _update_screen

	def _getCustomCommands(self):
		commands={}
		return(commands)
