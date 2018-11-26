#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
import json
import cairo
import os
import subprocess
import shutil
import threading
import platform
import subprocess
import sys
import time
#import commands
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib, PangoCairo, Pango
import time
from datetime import date
from taskscheduler.cronParser import cronParser

import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext


WIDGET_MARGIN=6
DBG=1

class DetailBox:
	
	def __init__(self,scheduler,scheduled_task_type=False):
		self.scheduled_task_type=scheduled_task_type
		self.scheduler_client=scheduler
		self.parser=cronParser()
		self.task={}
		self.task['serial']="0"
		self.task['type']="remote"
		self.btn_apply=Gtk.Button(stock=Gtk.STOCK_APPLY)
		try:
			self.flavour=subprocess.getoutput("lliurex-version -f")
		except:
			self.flavour="client"
		self.ldm_helper='/usr/sbin/sched-ldm.sh'

	def _debug(self,msg):
		if DBG:
			print("taskDetails: %s"%msg)
	#def _debug

	def set_mode(self,mode):
		pass

	def set_task_data(self,task):
		self.task['name']=''
		self.task['serial']=''
		self.task['data']=''
		self.task['cmd']=''
		self.task['type']=''
		self.task['spread']=''
		self.task.update(task)
		if 'kind' in task.keys():
			if type(task['kind'])==type(''):
				self.task['kind']=task['kind'].split(',')
			else:
				self.task['kind']=task['kind']
		else:
			self.task['kind']=''
		if 'data' in task.keys():
			self.task.update(task['data'])
			del self.task['data']

	def update_task_data(self,task):
		self.task.update(task)

	def _format_widget_for_grid(self,widget):
		#common
		widget.set_hexpand(False)
		widget.set_halign(Gtk.Align.CENTER)
		widget.set_valign(Gtk.Align.CENTER)
		if 'Gtk.Button' in str(type(widget)):
			pass
		elif 'Gtk.Entry' in str(type(widget)):
			widget.set_alignment(xalign=0.5)
			widget.set_max_length(2)
			widget.set_width_chars(2)
			widget.set_max_width_chars(3)
	#def _format_widget_for_grid

	def _load_interval_data(self,widget=None,handler=None):
#		if handler:
#			self.cmb_interval.handler_block(handler)
		total=999
#		position=self.cmb_interval.get_active()
#		self.cmb_interval.remove_all()
#		date=self.cmb_dates.get_active_text()
#		total=24
#		if date==_("minute(s)"):
#			total=120
#		elif date==_("day(s)"):
#			total=7
#		elif date==_("hour(s)"):
#			total=24
#		elif date==_("week(s)"):
#			total=4
#		elif date==_("month(s)"):
#			total=12
		self.spin_interval.set_range(1,total)

		#Set sensitive status
		self._changed_interval()
		#If user changes selection try to activate same value on new interval data or max
#		if position>=total:
#			position=total-1
#		elif position<0:
#			position=0
#		self.cmb_interval.set_active(position)
		if handler:
#			self.cmb_interval.handler_unblock(handler)
			self._parse_scheduled(True)
	#def _load_interval_data
	
	def _load_date_data(self):
		date=[_("minute(s)"),_("hour(s)"),_("day(s)"),_("week(s)"),_("month(s)")]
		for i in date:
			self.cmb_dates.append_text(i)
		self.cmb_dates.set_active(0)
	#def _load_date_data
	
	def _load_special_date_data(self):
		date=[_("Last month day"),_("First month day")]
		for i in date:
			self.cmb_special_dates.append_text(i)
		self.cmb_special_dates.set_active(0)
	#def _load_special_date_data

	def _load_date_time_data(self,date_type):
		inc=0
		jump=0
		time_units=0
		months={}
		if date_type=='hour':
			time_units=24
			widget=self.cmb_hours
		elif date_type=='minute':
			time_units=60
			jump=5
			widget=self.cmb_minutes
		elif date_type=='month':
			widget=self.cmb_months
			widget.append_text(_("All months"))
			inc=1
			time_units=12
			months={1:'January',2:'February',3:'March',4:'April',5:'May',6:'June',7:'July',8:'August',9:'September',10:'October',11:'November',12:'December'}
		elif date_type=='day':
			widget=self.cmb_days
			widget.append_text(_("All days"))
			inc=1
			time_units=31

		for i in range(time_units):
			if jump:
				if (not i%jump):
					widget.append_text(str(i+inc))
			else:
				if months:
					widget.append_text(months[(i+inc)])
				else:
					widget.append_text(str(i+inc))
		widget.set_active(0)
	#def _load_date_time_data

	def render_form(self,gtkGrid=None,**kwargs):
		if 'expert' in kwargs.keys():
			expert=kwargs['expert']
		else:
			expert=False
		if 'task_kind' in kwargs.keys():
			task_kind=kwargs['task_kind']
		else:
			task_kind=''
		if 'edit' in kwargs.keys():
			edit=kwargs['edit']
		else:
			edit=False
		if not gtkGrid:
			gtkGrid=Gtk.Grid()
		self.notebook=Gtk.Stack()
		self.chk_daily=Gtk.CheckButton(_("Select days"))
		self.chk_monday=Gtk.ToggleButton(_("Monday"))
		self.chk_tuesday=Gtk.ToggleButton(_("Tuesday"))
		self.chk_wednesday=Gtk.ToggleButton(_("Wednesday"))
		self.chk_thursday=Gtk.ToggleButton(_("Thursday"))
		self.chk_friday=Gtk.ToggleButton(_("Friday"))
		self.chk_saturday=Gtk.ToggleButton(_("Saturday"))
		self.chk_sunday=Gtk.ToggleButton(_("Sunday"))
		self.chk_daily=Gtk.CheckButton(_("Daily"))
		self.chk_hourly=Gtk.CheckButton(_("Hourly"))
		self.chk_weekly=Gtk.CheckButton(_("Weekly"))
		self.chk_interval=Gtk.CheckButton(_("Repeat"))
		self.cmb_interval=Gtk.ComboBoxText()
		self.spin_interval=Gtk.SpinButton()
		self.cmb_dates=Gtk.ComboBoxText()
		self.cmb_dates.set_hexpand(False)
		self.cmb_dates.set_vexpand(False)
		self.cmb_dates.set_valign(Gtk.Align.CENTER)
		self.cmb_dates.set_halign(Gtk.Align.CENTER)
		self.chk_special_dates=Gtk.CheckButton(_("Last month day"))
		self.day_box=Gtk.Box()
		self.day_box.set_homogeneous(True)
		self.cmb_days=Gtk.ComboBoxText()
		self.month_box=Gtk.Box()
		self.month_box.set_homogeneous(True)
		self.calendar=Gtk.Calendar()
		self.day_box.add(self.calendar)
		self.cmb_months=Gtk.ComboBoxText()
		self.hour_box=Gtk.Box(spacing=WIDGET_MARGIN)
		self.hour_box.set_homogeneous(False)
		self.cmb_hours=Gtk.ComboBoxText()
		####REM
		self.spin_hour=Gtk.SpinButton()
		self.spin_hour.set_range(0,23)
		self.spin_hour.set_increments(1,1)
		self.spin_hour.set_wrap(True)
		self.spin_hour.set_orientation(Gtk.Orientation.VERTICAL)
		self.spin_hour.set_valign(Gtk.Align.CENTER)
		self.spin_hour.set_halign(Gtk.Align.CENTER)
		self.spin_hour.set_vexpand(False)
		self.spin_min=Gtk.SpinButton()
		self.spin_min.set_range(0,59)
		self.spin_min.set_increments(1,1)
		self.spin_min.set_wrap(True)
		self.spin_min.set_orientation(Gtk.Orientation.VERTICAL)
		self.spin_min.set_valign(Gtk.Align.CENTER)
		self.spin_min.set_halign(Gtk.Align.CENTER)
		self.spin_min.set_vexpand(False)
		self.hour_box.add(self.spin_hour)
		self.hour_box.add(Gtk.Label(":"))
		self.minute_box=Gtk.Box()
		self.minute_box.add(self.spin_min)
		self.time_box=Gtk.Box(spacing=WIDGET_MARGIN)
		self.time_box.add(self.hour_box)
		self.time_box.add(self.minute_box)
		self.cmb_minutes=Gtk.ComboBoxText()

		self._load_interval_data()
		self._load_date_data()

		self.lbl_info=Gtk.Label("")
		self.lbl_info.set_line_wrap(True)
		self.lbl_info.set_max_width_chars(20)
		self.lbl_info.set_width_chars(20)
		self.lbl_info.set_opacity(0.6)
		gtkGrid.attach(self.lbl_info,0,0,7,1)
		self.lbl_info.set_margin_bottom(24)
		dow_frame=Gtk.Frame()
		dow_frame.set_shadow_type(Gtk.ShadowType.OUT)
		frame_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=WIDGET_MARGIN)
		dow_frame.add(frame_box)
		frame_box.set_margin_bottom(6)
		frame_box.set_margin_top(6)
		frame_box.set_margin_left(6)
		frame_box.set_margin_right(6)
		dow_box=Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		work_days_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		work_days_box.add(self.chk_monday)
		work_days_box.add(self.chk_tuesday)
		work_days_box.add(self.chk_wednesday)
		work_days_box.add(self.chk_thursday)
		work_days_box.add(self.chk_friday)
		work_days_box.set_focus_chain([self.chk_monday,self.chk_tuesday,self.chk_wednesday,self.chk_thursday,self.chk_friday])
		dow_box.add(work_days_box)
		weekend_days_box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		dow_box.add(weekend_days_box)
		weekend_days_box.add(self.chk_saturday)
		weekend_days_box.add(self.chk_sunday)
		weekend_days_box.set_focus_chain([self.chk_saturday,self.chk_sunday])
		dow_box.set_focus_chain([work_days_box,weekend_days_box])
#REM NOTEBOOK
		self.notebook_sw=Gtk.StackSwitcher()
		self.notebook.add_titled(dow_box,_("By day"),_("By day"))
		self.notebook.add_titled(self.day_box,_("By date"),_("By date"))
		self.notebook_sw.set_stack(self.notebook)
		self.notebook_sw.set_margin_bottom(6)
#REM
		self.interval_box=Gtk.Box()
		minBoxPos=Gtk.PositionType.BOTTOM
		labelCol=1
		dowCol=0
		gtkGrid.set_column_spacing(WIDGET_MARGIN*5)
		self.time_box.set_valign(Gtk.Align.CENTER)
		self.time_box.set_halign(Gtk.Align.CENTER)
		self.time_box.set_margin_bottom(WIDGET_MARGIN)
		label=Gtk.Label(_("Each"))
		label.set_margin_right(WIDGET_MARGIN)
		#		self.interval_box.add(Gtk.Label(_("Each")))
		self.interval_box.add(label)
		self.spin_interval=Gtk.SpinButton()
		self.spin_interval.set_range(0,999)
		self.spin_interval.set_increments(1,1)
		self.spin_interval.set_wrap(True)
		self.spin_interval.set_orientation(Gtk.Orientation.VERTICAL)
		self.spin_interval.set_valign(Gtk.Align.CENTER)
		self.spin_interval.set_halign(Gtk.Align.CENTER)
		self.spin_interval.set_vexpand(False)
		self.interval_box.add(self.spin_interval)
		self.interval_box.add(self.cmb_dates)
		lbl_hour=Gtk.Label(_("Time"))

		if edit:
			self.btn_apply.set_halign(Gtk.Align.END)
			self.btn_apply.set_valign(Gtk.Align.END)
			gtkGrid.attach(self.btn_apply,6,7,2,1)
		self.chk_spread=Gtk.CheckButton(_("Send task to clients"))
		gtkGrid.attach(self.chk_spread,0,7,1,1)
		self.chk_node=Gtk.CheckButton()
		self.chk_node.set_margin_top(12)
		self.chk_node.set_halign(Gtk.Align.START)
		self.chk_node.set_valign(Gtk.Align.START)
		self.chk_node.set_label("Advanced")
		self.chk_node.set_active(self.scheduled_task_type)

		gtkGrid.attach(self.notebook_sw,3,1,1,1)
		gtkGrid.attach(self.notebook,3,2,1,7)
		dow_frame.set_visible(False)
		dow_frame.set_no_show_all(True)
		#Grid attach by task kind
		if 'daily' in task_kind or expert:
			self.chk_daily.set_active(True)

		gtkGrid.attach(lbl_hour,0,1,1,1)
		gtkGrid.attach_next_to(self.time_box,lbl_hour,Gtk.PositionType.BOTTOM,1,3)
		gtkGrid.attach(self.chk_interval,4,1,2,1)
		gtkGrid.attach_next_to(self.interval_box,self.chk_interval,Gtk.PositionType.BOTTOM,1,1)
		self.lbl_disclaim=Gtk.Label("")
		self.lbl_disclaim.set_line_wrap(True)
		self.lbl_disclaim.set_max_width_chars(25)
		self.lbl_disclaim.set_width_chars(25)
		self.lbl_disclaim.set_lines(-1)
		self.lbl_disclaim.set_opacity(0.6)
		gtkGrid.attach_next_to(self.lbl_disclaim,self.interval_box,Gtk.PositionType.BOTTOM,1,3)
		self.interval_box.set_sensitive(False)
		if 'repeat' in task_kind or expert:
			self.interval_box.set_sensitive(True)
			self.lbl_disclaim.set_text(_("Tasks will take day 1 of month 1 at 00:00 as reference date/time"))

		#Tab order chain
		widget_array=[dow_frame,self.hour_box,self.minute_box,self.month_box,self.day_box,self.chk_interval,\
						self.interval_box,self.chk_special_dates]
		if edit:
			widget_array.append(self.btn_apply)

		gtkGrid.set_focus_chain(widget_array)
		#Add data to combos
		self._load_date_time_data('minute')
		self._load_date_time_data('hour')
		self._load_date_time_data('day')
		self._load_date_time_data('month')
		#handled signals
		interval_handler=self.cmb_interval.connect("changed",self._parse_scheduled)
		#Signals
		self.chk_daily.connect("toggled",self._set_daily_visibility,dow_frame)
		self.chk_interval.connect("toggled",self._set_visibility,self.interval_box)
		self.chk_monday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_tuesday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_wednesday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_thursday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_friday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_saturday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_sunday.connect("toggled",self._enable_fixed_dates,interval_handler)
		self.chk_interval.connect("toggled",self._chk_interval_status)
		self.chk_special_dates.connect("toggled",self._chk_special_dates_status)
		self.cmb_dates.connect("changed",self._load_interval_data,interval_handler)
		self.cmb_handler={}
		self.cmb_handler[self.cmb_months]=self.cmb_months.connect("changed",self._parse_scheduled)
		self.cmb_handler[self.cmb_days]=self.cmb_days.connect("changed",self._parse_scheduled)
		self.cmb_handler[self.spin_hour]=self.spin_hour.connect("changed",self._parse_scheduled)
		self.cmb_handler[self.spin_min]=self.spin_min.connect("changed",self._parse_scheduled)
		gtkGrid.connect("event",self._parse_scheduled)
		self.chk_node.connect("toggled",self._enable_scheduled_task_type,gtkGrid,edit)

		#Initial control status
		self.interval_box.set_sensitive(False)
		#signals
		gtkGrid.set_valign(Gtk.Align.CENTER)
		gtkGrid.set_halign(Gtk.Align.CENTER)
		self.gtkgrid=gtkGrid
		return (gtkGrid)
	#def render_form

	def _set_daily_visibility(self,widget_event,widget,*args):
		self._set_visibility(widget_event,widget,*args)
		if widget_event.get_active()==False:
			widgets=[self.chk_monday,
				self.chk_tuesday,
				self.chk_wednesday,
				self.chk_thursday,
				self.chk_friday,
				self.chk_saturday,
				self.chk_sunday]
			for widget in widgets:
				widget.set_active(False)

	def _set_visibility(self,widget_event,widget,*args):
		status=widget_event.get_active()
		widget.set_sensitive(status)
		widget.show_all()

	def _enable_scheduled_task_type(self,widget,gtkgrid,edit):
		expert=self.chk_node.get_active()
		for grid_widget in gtkgrid.get_children():
			gtkgrid.remove(grid_widget)
		parent=gtkgrid.get_parent()
		parent.remove(gtkgrid)
		gtkgrid=self.render_form(gtkgrid,edit=edit,expert=expert)
		parent.add(gtkgrid)
		parent.show_all()

	def _render_form(self,task_kind,edit):
		for grid_widget in self.gtkgrid.get_children():
			self.gtkgrid.remove(grid_widget)
		parent=self.gtkgrid.get_parent()
		parent.remove(self.gtkgrid)
		gtkgrid=self.render_form(self.gtkgrid,task_kind=task_kind,edit=edit)
		parent.add(gtkgrid)
		parent.show_all()

	def load_task_details(self,*args,**kwargs):
		if 'edit' in kwargs.keys():
			edit=True
		else:
			edit=False
		self._render_form(self.task['kind'],edit=edit)
		for widget,handler in self.cmb_handler.items():
			widget.handler_block(handler)
		self.lbl_info.set_text('')
		if self.task['m'].isdigit():
			self.spin_min.set_value(int(self.task['m']))
		else:
			self.spin_min.set_value(0)
			self._parse_date_details(self.task['m'],None,'min')

		if self.task['h'].isdigit():
			self.spin_hour.set_value(int(self.task['h']))
		else:
			self.spin_hour.set_value(0)
			self._parse_date_details(self.task['h'],None,'hour')

		self._parse_date_details(self.task['dom'],self.cmb_days,'dom')
		self._parse_date_details(self.task['mon'],self.cmb_months,'mon')
		#Load calendar
		if self.task['dom'].isdigit() and self.task['mon'].isdigit():
				self.notebook.set_visible_child_name(_("By date"))
				self.calendar.select_month(int(self.task['mon'])-1,date.today().year)
				self.calendar.select_day(int(self.task['dom']))
		widget_dict={'0':self.chk_sunday,'1':self.chk_monday,'2':self.chk_tuesday,\
					'3':self.chk_wednesday,'4':self.chk_thursday,'5':self.chk_friday,\
					'6':self.chk_saturday,'7':self.chk_sunday}
		if self.task['dow']=='*' and self.task['dom']=='*':
			self.task['dow']="1,2,3,4,5,6,7"
		self._parse_date_details(self.task['dow'],None,'dow',widget_dict)
		if 'spread' in self.task.keys():
			if self.task['spread']==True:
				self.chk_spread.set_active(True)
		if 'lmd' in self.task.keys():
			self.chk_special_dates.set_active(True)
		for widget,handler in self.cmb_handler.items():
			widget.handler_unblock(handler)
	#def load_task_details

	def _parse_date_details(self,date,widget=None,date_type=None,widget_dict=None):
		if date.isdigit() and widget:
			widget.set_active(int(date))
		elif '/' in date:
			pos=date.split('/')
			self.chk_interval.set_active(True)
			self.cmb_interval.set_active(int(pos[1])-1)
			self.spin_interval.set_value(int(pos[1]))
			if date_type=='hour' or date_type=='min':
				self.spin_hour.set_value(0)
				self.hour_box.set_sensitive(False)
				self.minute_box.set_sensitive(False)
			elif date_type=='dom':
				self.cmb_dates.set_active(1)
				self.hour_box.set_sensitive(True)
				self.minute_box.set_sensitive(True)
			elif date_type=='mon':
				self.cmb_interval.set_active(int(pos[1])-1)
				self.cmb_dates.set_active(3)
				self.month_box.set_sensitive(False)
				self.hour_box.set_sensitive(True)
				self.minute_box.set_sensitive(True)
		elif widget_dict:
			array_date=[]
			if ',' in date:
				array_date=date.split(',')
			else:
				array_date.append(date)

			for selected_date in array_date:
				if selected_date.isdigit():
					widget_dict[selected_date].set_active(True)
	#def _parse_date_details

	def clear_screen(self):
		widgets=[self.chk_monday,self.chk_tuesday,self.chk_wednesday,self.chk_thursday,\
				self.chk_friday,self.chk_saturday,self.chk_sunday]
		for widget in widgets:
			widget.set_active(False)
		self.spin_hour.set_value(0)
		self.spin_min.set_value(0)
		self.cmb_days.set_active(0)
		self.cmb_months.set_active(0)
		self.cmb_interval.set_active(0)
		self.cmb_dates.set_active(0)
		self.chk_special_dates.set_active(False)
		self.chk_interval.set_active(False)
	#def clear_screen
	
	def _set_sensitive_widget(self,widget_dic):
		for widget,status in widget_dic.items():
			widget.set_sensitive(status)
	#def _set_sensitive_widget
	
	def _changed_interval(self):
		if self.chk_interval.get_active():
			interval=self.cmb_dates.get_active_text()
			if interval==_('hour(s)') or interval==_('minute(s)'):
				self._set_sensitive_widget({self.hour_box:False,self.minute_box:False})
				self._set_days_sensitive(True)
			elif interval==_('day(s)') or interval==_('week(s)'):
				self._set_sensitive_widget({self.month_box:True,self.hour_box:True,self.minute_box:True})
				self._set_days_sensitive(False)
			elif interval==_('month(s)'):
				self._set_sensitive_widget({self.hour_box:True,self.minute_box:True})
				self._set_days_sensitive(True)
		self._chk_special_dates_status()
	#def _changed_interval


	def _chk_interval_status(self,widget):
		if self.chk_interval.get_active():
			self._set_sensitive_widget({self.interval_box:True,\
				self.hour_box:False,self.minute_box:False,self.month_box:True})
			self._changed_interval()
			if not self.spin_interval.get_value_as_int():
				self.spin_interval.set_value(1)
			self.lbl_disclaim.set_text("Tasks will take day 1 of month 1 at 00:00 as reference date/time")

		else:
			self._set_sensitive_widget({self.interval_box:False,\
				self.hour_box:True,self.minute_box:True,self.month_box:True})
			self.lbl_disclaim.set_text("")
		self._chk_special_dates_status()
	#def _chk_interval_status
			
	def _chk_special_dates_status(self,widget=None):
		return
		if self.chk_special_dates.get_active():
			self._set_sensitive_widget({self.hour_box:True,self.minute_box:True,self.month_box:True,self.day_box:False})
			self._set_days_sensitive(False)
		else:
			self._set_sensitive_widget({self.day_box:not self._get_days_active()})
			self._set_days_sensitive(True)
	#def _chk_special_dates_status

	def _get_days_active(self):
		sw_active=False
		widgets=[self.chk_monday,
				self.chk_tuesday,
				self.chk_wednesday,
				self.chk_thursday,
				self.chk_friday,
				self.chk_saturday,
				self.chk_sunday]
		for widget in widgets:
			if widget.get_active():
				sw_active=True
				break
		return sw_active
	#def _get_days_active

	def _enable_fixed_dates(self,widget,handler=None):
		sw_enable=True
		sw_enable=self._get_days_active()
		if sw_enable:
			if self.chk_interval.get_active():
				self._load_interval_data(True,handler)
			else:
				self.month_box.set_sensitive(True)
		else:
			if self.chk_interval.get_active():
				self._load_interval_data(True,handler)
			else:
				self.month_box.set_sensitive(True)
	#def _enable_fixed_dates

	def _set_days_sensitive(self,state):
		if self.chk_special_dates.get_active():
			state=False
		widgets=[self.chk_monday,
				self.chk_tuesday,
				self.chk_wednesday,
				self.chk_thursday,
				self.chk_friday,
				self.chk_saturday,
				self.chk_sunday]
		for widget in widgets:
			widget.set_sensitive(state)
	#def _set_days_sensitive

	def _parse_screen(self):
		details={}
		dow=''
		#Init date data
		for i in ["h","m","mon","dom"]:
			details[i]="*"
		#load data
		if self.spin_hour.is_sensitive():
			details["h"]=str(self.spin_hour.get_value_as_int())
		if self.spin_min.is_sensitive():
			details["m"]=str(self.spin_min.get_value_as_int())
		else:
			details['m']="0"
		if self.notebook.get_visible_child_name()==_("By date"):
			details['dow']='*'
			date=self.calendar.get_date()
			details["mon"]=str(date.month+1)
			details["dom"]=str(date.day)
		else:
			widgets=[self.chk_monday,self.chk_tuesday,	self.chk_wednesday,	self.chk_thursday,\
				self.chk_friday,self.chk_saturday,self.chk_sunday]
			cont=1
			for widget in widgets:
				if widget.get_active() and widget.get_sensitive():
					dow+=str(cont)+','
				cont+=1
			if dow!='':
				dow=dow.rstrip(',')
			else:
				dow='*'
			details['dow']=dow

		if self.cmb_dates.is_sensitive():
			if self.cmb_dates.get_active_text()==_('minute(s)'):
				details['m']="0/"+str(self.spin_interval.get_value_as_int())
			if self.cmb_dates.get_active_text()==_('hour(s)'):
				details['h']="0/"+str(self.spin_interval.get_value_as_int())
			if self.cmb_dates.get_active_text()==_('day(s)'):
				details['dom']="1/"+str(self.spin_interval.get_value_as_int())
			if self.cmb_dates.get_active_text()==_('week(s)'):
				week=self.spin_interval.get_value_as_int()*7
				details['dom']="1/"+str(week)
			if self.cmb_dates.get_active_text()==_('month(s)'):
				details['mon']="1/"+str(self.spin_interval.get_value_as_int())
		details['hidden']=0
		if self.chk_special_dates.get_active():
			details['lmd']=1
			details['dom']='*'
			details['dow']='*'

		if self.chk_spread.get_active():
			details['spread']=True
		else:
			details['spread']=False

		return details
	#def _parse_screen

	def _parse_scheduled(self,container=None,widget=None):
		details=self._parse_screen()
		self.lbl_info.set_text(self.parser.parse_taskData(details))
	#def _parse_scheduled

	def update_task_details(self,widget=None):
		if self.task['name'] and self.task['serial']:
			task_data=self.get_task_details()
			return self.scheduler_client.write_tasks(task_data,self.task['type'])
	#def update_task_details

	def get_task_details(self,*args):
		details=self._parse_screen()
		details['cmd']=self.scheduler_client.get_task_command(self.task['cmd'])
		#Search for a "last day month" cmd
		if 'lmd' in details.keys():
			details['cmd']=self.ldm_helper+' '+details['cmd']
		task={}
		task[self.task['name']]={self.task['serial']:details}
		self._debug("Saving %s"%task)
		return task
	#def get_task_details
