#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication
from QtExtraWidgets import QStackedWindow
import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext
app=QApplication(["TaskScheduler"])
mw=QStackedWindow()
mw.setIcon("taskscheduler")
abspath=os.path.dirname(__file__)
if os.path.islink(__file__)==True:
	abspath=os.path.join(os.path.dirname(__file__),os.path.dirname(os.readlink(__file__)))
mw.addStacksFromFolder(os.path.join(abspath,"stacks"))
mw.setBanner("/usr/share/taskscheduler/rsrc/taskscheduler_banner.png")
mw.show()
mw.resize(mw.sizeHint().width()*2.1,mw.sizeHint().width()*1.2)
app.exec()
