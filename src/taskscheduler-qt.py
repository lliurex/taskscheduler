#!/usr/bin/env python3
import sys
import os
from PySide2.QtWidgets import QApplication
from QtExtraWidgets import QStackedWindow
import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext
app=QApplication(["TaskScheduler"])
config=QStackedWindow()
abspath=os.path.dirname(__file__)
if os.path.islink(__file__)==True:
	abspath=os.path.join(os.path.dirname(__file__),os.path.dirname(os.readlink(__file__)))
config.addStacksFromFolder(os.path.join(abspath,"stacks"))
config.setBanner("/usr/share/taskscheduler/rsrc/taskscheduler_banner.png")
config.show()
config.setMinimumWidth(config.sizeHint().width()*1.8)
config.setMinimumHeight(config.sizeHint().width()*0.8)

#config=appConfig(NAME.lower(),{'app':app})
#config.setRsrcPath("/usr/share/{}/rsrc".format(NAME.lower()))
#config.setIcon(NAME.lower())
#config.setBackgroundImage("{}_bkg.svg".format(NAME.lower()))
#config.setConfig(confDirs={'system':os.path.join('/usr/share',NAME.lower()),'user':os.path.join(os.environ['HOME'],'.config/{}'.format(NAME.lower()))},confFile="{}.conf".format(NAME.lower()))
#config.Show()
#config.setMinimumWidth(config.sizeHint().width())

app.exec_()
