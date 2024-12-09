import os
from PySide2.QtWidgets import QPushButton,QGridLayout,QComboBox,QWidget,QFileDialog,QInputDialog
from PySide2 import QtGui
from PySide2.QtCore import Qt,QDate
import gettext
_ = gettext.gettext

i18n={"BTN_ARGS":_("Set arguments"),
	"BTN_FILE":_("Select script"),
	"SELECT_FILE":_("Write or select a command")
	}

class QCmdSelector(QWidget):
	def __init__(self,parent=None,**kwargs):
		QWidget.__init__(self, parent)
		self.lay=QGridLayout()
		self.setLayout(self.lay)
		self.cmbCmd=QComboBox()
		self.cmbCmd.setEditable(True)
		self.cmbCmd.currentTextChanged.connect(self._refreshCmd)
		self.cmbCmd.lineEdit().setPlaceholderText(i18n.get("SELECT_FILE"))
		self.lay.addWidget(self.cmbCmd,0,2,1,2)
		self.btnFile=QPushButton(i18n.get("BTN_FILE"))
		self.btnFile.clicked.connect(self._setFile)
		self.lay.addWidget(self.btnFile,0,0,1,1)
		self.btnArgs=QPushButton(i18n.get("BTN_ARGS"))
		self.lay.addWidget(self.btnArgs,0,1,1,1)
		self.btnArgs.clicked.connect(self._setArgs)
		self.btnArgs.setEnabled(False)
	#def __init__

	def _setFile(self):
		self.btnArgs.setEnabled(False)
		dlg=QFileDialog()
		if dlg.exec():
			fnames=dlg.selectedFiles()
			if len(fnames)>0:
				self._btnFileText(fnames[0])
	#def _setFile

	def _btnFileText(self,text):
		cmdTxt=text.split("/")
		if len(cmdTxt)==0:
			return
		btnText=text
		if len(cmdTxt)>2:
			btnText="/{}/.../{}".format(text.split("/")[1],os.path.basename(text))
		self.btnFile.setText(btnText)
		self.btnFile.setToolTip(text)
		self.btnArgs.setEnabled(True)
		currentCmd=self.cmbCmd.currentText().split()
		currentCmd.append("")
		if text!=currentCmd[0]:
			argsText=""
			if self.btnArgs.text()!=i18n.get("BTN_ARGS"):
				argsText=self.btnArgs.text()
			self.cmbCmd.setEditText("{} {}".format(text,argsText))
		if len(currentCmd)==2:
			self.btnArgs.setText(i18n.get("BTN_ARGS"))
	#def _btnFileText

	def _btnArgsText(self,text):
		self.btnArgs.setText(text)
		self.btnArgs.setToolTip(text)
		currentArgs=self.cmbCmd.currentText().split()
		currentArgs.append("")
		if text!=" ".join(currentArgs):
			self.cmbCmd.setEditText("{} {}".format(self.btnFile.toolTip(),text))
	#def _btnFileText

	def _setArgs(self):
		dlg=QInputDialog()
		if dlg.exec():
			content=dlg.textValue()
			if len(content)>0:
				self._btnArgsText(content)
	#def _setArgs
		
	def clear(self):
		self.cmbCmd.clear()
	#def clear

	def addItem(self,*args,**kwargs):
		self.cmbCmd.addItem(*args)
	#def addItem

	def setCurrentIndex(self,*args,**kwargs):
		self.cmbCmd.setCurrentIndex(*args)
		if args[0]<0:
			self.btnFile.setText(i18n.get("BTN_FILE"))
			self.btnArgs.setText(i18n.get("BTN_ARGS"))
	#def setCurrentIndex

	def currentIndex(self,*args,**kwargs):
		return(self.cmbCmd.currentIndex())
	#def currentIndex

	def setCurrentText(self,*args,**kwargs):
		self.cmbCmd.setCurrentText(*args)
		if args[0]==None:
			self.btnFile.setText(i18n.get("BTN_FILE"))
			self.btnArgs.setText(i18n.get("BTN_ARGS"))
	#def setCurrentText

	def currentText(self,*args,**kwargs):
		return(self.cmbCmd.currentText())
	#def currentText

	def setPlaceholderText(self,*args,**kwargs):
		self.cmbCmd.lineEdit().setPlaceholderText(*args)
	#def setPlaceholderText

	def _refreshCmd(self,*args,**kwargs):
		text=self.cmbCmd.currentText()
		cmdArgs=text.split()
		if len(cmdArgs)>0:
			self._btnFileText(cmdArgs[0])
			if len(cmdArgs)>1:
				self._btnArgsText(" ".join(cmdArgs[1:]))
	#def _refreshCmd

	def readMode(self):
		self.btnFile.setVisible(False)
		self.btnArgs.setVisible(False)
	#def readMode

	def editMode(self):
		self.btnFile.setVisible(True)
		self.btnArgs.setVisible(True)
	#def editMode
#class cmdSelector

