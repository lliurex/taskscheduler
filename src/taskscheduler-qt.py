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
#mw.setMinimumWidth(mw.sizeHint().width()*2.2)
#mw.setMinimumHeight(mw.sizeHint().width())
mw.resize(mw.sizeHint().width()*2.1,mw.sizeHint().width())

#mw=appmw(NAME.lower(),{'app':app})
#mw.setRsrcPath("/usr/share/{}/rsrc".format(NAME.lower()))
#mw.setIcon(NAME.lower())
#mw.setBackgroundImage("{}_bkg.svg".format(NAME.lower()))
#mw.setmw(confDirs={'system':os.path.join('/usr/share',NAME.lower()),'user':os.path.join(os.environ['HOME'],'.mw/{}'.format(NAME.lower()))},confFile="{}.conf".format(NAME.lower()))
#mw.Show()
#mw.setMinimumWidth(mw.sizeHint().width())

app.exec()
