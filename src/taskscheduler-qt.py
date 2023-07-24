#!/usr/bin/env python3
import sys
import os
from PySide2.QtWidgets import QApplication
from appconfig.appConfigScreen import appConfigScreen as appConfig
NAME="TaskScheduler"
app=QApplication([NAME])
config=appConfig(NAME,{'app':app})
config.setRsrcPath("/usr/share/{}/rsrc".format(NAME.lower()))
config.setIcon(NAME.lower())
config.setBanner("{}_banner.png".format(NAME.lower()))
config.setBackgroundImage("{}_bkg.svg".format(NAME.lower()))
config.setConfig(confDirs={'system':os.path.join('/usr/share',NAME.lower()),'user':os.path.join(os.environ['HOME'],'.config/{}'.format(NAME.lower()))},confFile="{}.conf".format(NAME.lower()))
config.Show()

app.exec_()
