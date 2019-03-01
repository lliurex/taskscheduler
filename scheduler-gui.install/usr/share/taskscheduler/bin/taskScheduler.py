#! /usr/bin/python3
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
from math import sqrt
import webbrowser
#import commands
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib, PangoCairo, Pango
from taskscheduler.taskscheduler import TaskScheduler as scheduler
from taskscheduler.cronParser import cronParser
from detailDateBox import DetailBox as detailDateBox 
from edupals.ui.n4dgtklogin import *
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext

WIDTH=800
HEIGHT=600
BASE_DIR="/usr/share/taskscheduler/"
#BASE_DIR="../share/taskscheduler/"
REMOVE_ICON=BASE_DIR+"rsrc/trash.svg"
EDIT_ICON=BASE_DIR+"rsrc/edit.svg"
LOGIN_IMG=BASE_DIR+"rsrc/scheduler.svg"
BANNER_IMG=BASE_DIR+"rsrc/taskScheduler-banner.png"
NO_EDIT_ICON=BASE_DIR+"rsrc/no_edit.png"
LOCK_PATH="/var/run/taskScheduler.lock"
MARGIN=6

class TaskScheduler:
	def __init__(self):
		self.dbg=False
		self.last_task_type='remote'
		self.ldm_helper='/usr/sbin/sched-ldm.sh'
		self.conf_dir="/etc/scheduler/conf.d"
		self.conf_dir="%s/.config/taskscheduler/"%(os.environ["HOME"])
		self.conf_file="%s/scheduler.conf"%(self.conf_dir)
		self.file_cmd_descriptions="%s/commands.json"%self.conf_dir
		self.i18n={}
		self.i18n={}
		self.command_description={}
		self.description_command={}
		self.scheduler=scheduler()
		self.cronparser=cronParser()
		self.tasks_per_row=3
		self.config={}
		self._parse_config()
		self.autorefresh=False
		#Install signal handler
		GLib.idle_add(self.install_handler,signal.SIGUSR1,priority=GLib.PRIORITY_HIGH)
	#def __init__		
		
	def install_handler(self,sig):
		GLib.unix_signal_add(GLib.PRIORITY_HIGH,sig,self.sig_refresh_grid_tasks,None)
	#def install_handler

	def _debug(self,msg):
		if self.dbg:
			print("taskScheduler: %s"%msg)
	#def _debug

	def _quit(self,*args):
		Gtk.main_quit()
	#def _quit

	def _parse_config(self):
		self.config=self.scheduler.read_config()
	#def _parse_config

	def _write_config(self,task,key,value):
		self.scheduler.write_config(task,key,value)
		self._parse_config()
	#def _write_config

	def start_gui(self):
		def keypress(widget,event):
			blacklist=['login','tasks']
			if event.keyval==65307 and self.stack.get_visible_child_name() not in blacklist:
				self._set_visible_stack(None,"tasks",Gtk.StackTransitionType.CROSSFADE,1)

		mw=Gtk.Window()
		mw.set_title("TaskScheduler")
		mw.connect("destroy",self._quit)
		mw.connect("key_press_event",keypress)
		mw.set_resizable(False)
		mw.set_size_request(WIDTH,HEIGHT)
		self.stack=Gtk.Stack()
		self.stack.set_transition_duration(1000)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.add_titled(self._render_login(), "login", "login")
		vbox_tasks=Gtk.Grid()
		vbox_tasks.set_hexpand(True)
		pb=GdkPixbuf.Pixbuf.new_from_file("%s"%BANNER_IMG)
		img_banner=Gtk.Image.new_from_pixbuf(pb)
		img_banner.props.halign=Gtk.Align.CENTER
		img_banner.set_margin_top(MARGIN*2)
		vbox_tasks.attach(img_banner,0,0,1,1)
		vbox_tasks.attach(self._render_toolbar(),0,1,1,1)
		vbox_tasks.attach(self._render_tasks(),0,2,1,1)
		self.stack.add_titled(vbox_tasks, "tasks", "tasks")
		self.stack.add_titled(self._render_new_command(), "ccmds", "ccmds")
		self.stack.add_titled(self._render_config(), "config", "config")
		self.stack.set_visible_child_name("login")
		mw.add(self.stack)
		self.set_css_info()
		mw.show_all()
		Gtk.main()
	#def start_gui

	def _set_visible_stack(self,widget,stack,transition=None,duration=None):
		if transition:
			self.stack.set_transition_type(transition)
		if duration:
			self.stack.set_transition_duration(duration)
		#clear stack 
		if stack!='tasks':
			for stack_child in self.stack.get_child_by_name(stack).get_children():
				if type(stack_child)==type(Gtk.Grid()):
					for grid_child in stack_child.get_children():
						if type(grid_child)==type(Gtk.ComboBoxText()):
							for cmb_child in grid_child.get_children():
								cmb_child.set_text("")
								cmb_child.set_placeholder_text(_("Insert text or choose one"))
						elif type(grid_child)==type(Gtk.Box()) or type(grid_child)==type(Gtk.VBox()):
								for box_child in grid_child.get_children():
									if type(box_child)==type(Gtk.Entry()):
										box_child.set_text("")
										box_child.set_placeholder_text(_("Insert text"))
									if type(box_child)==type(Gtk.ComboBoxText()):
										for cmb_child in box_child.get_children():
											cmb_child.set_text("")
											cmb_child.set_placeholder_text(_("Insert text or choose one"))

		self.stack.set_visible_child_name(stack)

		#default values
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_transition_duration(1000)
	#def _set_visible_stack

	def _entry_field(self,label,cmb=False):
		box=Gtk.VBox(True,True)
		box.set_name("WHITE_BACKGROUND")
		lbl=Gtk.Label()
		lbl.set_name("ENTRY_LABEL")
		lbl.set_halign(Gtk.Align.START)
		lbl.set_markup("%s"%_(label))
		box.add(lbl)
		if cmb:
			inp=Gtk.ComboBoxText.new_with_entry()
		else:
			inp=Gtk.Entry()
		inp.set_name("GtkEntry")
		box.add(inp)
		return (box,inp)
	#def _entry_field

	def _render_login(self):
		login=N4dGtkLogin()
		login.set_allowed_groups(['adm','teachers'])
		desc=_("Welcome to the Task Scheduler for Lliurex.\nFrom here you can:\n<sub>* Schedule tasks in the local pc\n* Distribute tasks among all the pcs in the network\n*Show scheduled tasks</sub>")
		login.set_info_text("<span foreground='black'>Task Scheduler</span>",_("Task Scheduler"),"<span foreground='black'>"+desc+"</span>\n")
		login.set_info_background(image=LOGIN_IMG,cover=False)
		login.after_validation_goto(self._signin)
		login.hide_server_entry()
		login.show_all()
		return(login)
	#def _render_login

	def _signin(self,user=None,pwd=None,server=None,data=None):
		self.scheduler.set_credentials(user,pwd,server)
		self._load_tasks()
		self._refresh_grid_tasks()
		self.stack.set_visible_child_name("tasks")
	#def _signin

	def _render_toolbar(self):
		def _show_prefs(widget):
			men_prefs.show_all()
			men_prefs.popup_at_widget(widget,Gdk.Gravity.SOUTH,Gdk.Gravity.NORTH,None)

		def _show_help(widget):
			men_help.show_all()
			men_help.popup_at_widget(widget,Gdk.Gravity.SOUTH,Gdk.Gravity.NORTH,None)

		def _refresh_tasks(*args):
			th=threading.Thread(target=self._refresh_grid_tasks,args=[])
			th.start()
		toolbar=Gtk.Toolbar()
		#Menu prefs
		men_prefs=Gtk.Menu()
		mei_ant=Gtk.MenuItem(_("Add new task"))
		mei_ant.connect("activate",self._add_task,toolbar)
		mei_acc=Gtk.MenuItem(_("Add custom command"))
		mei_acc.connect("activate",self._set_visible_stack,"ccmds",Gtk.StackTransitionType.CROSSFADE,1)
		mei_mcc=Gtk.MenuItem(_("Manage custom commands"))
		mei_mtg=Gtk.MenuItem(_("Manage task groups"))
		mei_mtg.connect("activate",self._set_visible_stack,"config",Gtk.StackTransitionType.CROSSFADE,1)
		mei_rtl=Gtk.MenuItem(_("Refresh tasks list"))
		mei_rtl.connect("activate",_refresh_tasks)
		men_prefs.append(mei_ant)
		men_prefs.append(mei_acc)
		men_prefs.append(mei_mtg)
		men_prefs.append(mei_rtl)

		#Menu help
		men_help=Gtk.Menu()
		mei_hlp=Gtk.MenuItem(_("Help"))
		mei_hlp.connect("activate",self._help)
		mei_abo=Gtk.MenuItem(_("About taskscheduler"))
		mei_abo.connect("activate",self._about)
		men_help.append(mei_hlp)
		men_help.append(mei_abo)

		toolbar.set_vexpand(False)
		btn_add=Gtk.Button()
		tlb_add=Gtk.ToolButton(btn_add)
		tlb_add.connect("clicked",self._add_task)
		tlb_add.set_icon_name("list-add")
		tlb_add.set_tooltip_text(_("Add new task"))
		toolbar.insert(tlb_add,0)
		btn_refresh=Gtk.Button()
		tlb_refresh=Gtk.ToolButton(btn_refresh)
		tlb_refresh.connect("clicked",_refresh_tasks)
		tlb_refresh.set_icon_name("view-refresh")
		tlb_refresh.set_tooltip_text(_("Reload tasks"))
		toolbar.insert(tlb_refresh,1)
		btn_config=Gtk.Button()
		tlb_config=Gtk.ToolButton(btn_config)
		tlb_config.connect("clicked",_show_prefs)
		tlb_config.set_icon_name("preferences-other")
		tlb_config.set_tooltip_text(_("Open preferences menu"))
		toolbar.insert(tlb_config,2)
		btn_help=Gtk.Button()
		tlb_help=Gtk.ToolButton(btn_help)
		tlb_help.set_tooltip_text(_("Open help menu"))
		tlb_help.connect("clicked",_show_help)
		tlb_help.set_icon_name("help-contents")
		toolbar.insert(tlb_help,-1)
		toolbar.set_margin_bottom(0)
		return(toolbar)
	#def _render_toolbar

	def _render_config(self,*args):
		def _begin_config(*args):
			task=cmb_tasks.get_active_text()
			task=self._get_translation_for_desc(task)
			clr=clr_color.get_rgba().to_string()
			self._write_config(task,'background',clr)
			#Get clr brightness (if is too dark the text will be white)
			#Extract red green and blue from clr
			clr_array=clr.split(',')
			red=int(clr_array[0].replace('rgb(',''))
			green=int(clr_array[2].replace(')',''))
			blue=int(clr_array[1])
			#Values extracted from different web sources and try-catch...
			red=red*red* 0.241
			green=green*green* 0.491
			blue=blue*blue* 0.384
			bright=sqrt(red+green+blue)
			if bright<134: #134 is a good value to distingish between dark and bright
				self._write_config(task,'color','white')
			else:
				self._write_config(task,'color','black')
			th=threading.Thread(target=self._refresh_grid_tasks,args=[])
			th.start()
			self._set_visible_stack(None,"tasks",Gtk.StackTransitionType.CROSSFADE,1)
		def _load_cmb(*args):
			(tasks,names)=self._load_tasks()
			cmb_tasks.remove_all()
			for task in names:
				cmb_tasks.append_text(_(task))
			cmb_tasks.set_active(0)
		grid=Gtk.Box(True,True)
		grid.set_name("MAIN_COMMANDS_GRID")
		grid_cnf=Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
		grid_cnf.set_hexpand(False)
		grid_cnf.set_vexpand(False)
		grid_cnf.set_halign(Gtk.Align.CENTER)
		grid_cnf.set_valign(Gtk.Align.CENTER)
		grid_cnf.set_name("COMMANDS_GRID")
		lbl_tasks=Gtk.Label(_("Task group"))
		lbl_tasks.set_name("ENTRY_LABEL")
		lbl_tasks.set_halign(Gtk.Align.START)
		cmb_tasks=Gtk.ComboBoxText.new()
		cmb_tasks.set_name("GtkCombo")
		grid_cnf.add(lbl_tasks)
		grid_cnf.add(cmb_tasks)
		lbl_color=Gtk.Label(_("Pick color for group"))
		lbl_color.set_name("ENTRY_LABEL")
		clr_color=Gtk.ColorChooserWidget()
		for c in clr_color.get_children():
			for h in c.get_children():
				if "Box" in str(h):
					h.set_visible(False)
				try:
					h.get_children()
				except:
					h.set_visible(False)

		grid_cnf.add(lbl_color)
		grid_cnf.add(clr_color)
		box_btn=Gtk.Box()
		box_btn.set_margin_top(MARGIN)
		box_btn.set_halign(Gtk.Align.END)
		btn_ok=Gtk.Button.new_from_icon_name("gtk-apply",Gtk.IconSize.BUTTON)
		btn_ok.connect("clicked",_begin_config)
		btn_ok.set_tooltip_text(_("Add command"))
		btn_cancel=Gtk.Button.new_from_icon_name("gtk-close",Gtk.IconSize.BUTTON)
		btn_cancel.connect("clicked",self._set_visible_stack,"tasks",Gtk.StackTransitionType.CROSSFADE,1)
		btn_cancel.set_tooltip_text(_("Cancel"))

		box_btn.add(btn_cancel)
		box_btn.add(btn_ok)
		grid_cnf.add(box_btn)
		grid.add(grid_cnf)
		grid.connect("map",_load_cmb)
		return(grid)
	#def _render_config

	def _render_new_command(self,*args):
		def _begin_add_new_command(*args):
			task=cmb_tasks.get_active_text()
			task=self._get_translation_for_desc(task)
			if task not in names:
				cmb_tasks.append_text(task)
			cmd=inp_cmd.get_active_text()
			cmd=self._get_translation_for_desc(cmd)
			cmd=self._get_description_for_cmd(cmd)
			desc=inp_desc.get_text()
			if desc=='':
				desc=inp_cmd.get_active_text()
			if cmd and task:
				if rvl_parm.get_reveal_child():
					parm=inp_parm.get_text()
					cmd="%s %s"%(cmd,parm)
					if desc==inp_cmd.get_active_text():
						desc="%s %s"%(desc,parm)
				if "kdialog" in cmd:
					cmd="%s 5000"%cmd
				if self.scheduler.add_command(task,cmd,desc):
					self._set_visible_stack(None,"tasks",Gtk.StackTransitionType.CROSSFADE,100)

		def _display_needed_parms(*args):
			command=inp_cmd.get_active_text()
			command=self._get_translation_for_desc(command)
			rvl_parm.set_reveal_child(False)
			if command in commands.keys():
				if 'parms' in commands[command].keys():
					parm=commands[command]['parms']
					inp_parm.set_placeholder_text(_(parm))
					rvl_parm.set_reveal_child(True)

		grid=Gtk.VBox()
		grid.set_name("MAIN_COMMANDS_GRID")
		grid_cmd=Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
		grid_cmd.set_row_homogeneous(True)
		grid_cmd.set_hexpand(True)
		grid_cmd.set_vexpand(False)
		grid_cmd.set_halign(Gtk.Align.CENTER)
		grid_cmd.set_valign(Gtk.Align.CENTER)
		grid_cmd.set_name("COMMANDS_GRID")
		(boxtask,cmb_tasks)=self._entry_field(_("Task Group"),cmb=True)
		(tasks,names)=self._load_tasks()
		for task in names:
			cmb_tasks.append_text(_(task))

		(boxcmd,inp_cmd)=self._entry_field(_("Insert command"),cmb=True)
		commands=self.scheduler.get_commands()
		for command,data in commands.items(): 
			self._add_translation_for_desc(command)
			self._add_description_for_cmd(command,data['cmd'])
			inp_cmd.append_text(_(command))
		inp_cmd.connect("changed",_display_needed_parms)
		(boxdesc,inp_desc)=self._entry_field(_("Insert description (optional)"))

		rvl_parm=Gtk.Revealer()
		(boxparm,inp_parm)=self._entry_field(_("Parameters"))
		rvl_parm.add(boxparm)
		grid_cmd.attach(boxtask,0,0,1,1)
		grid_cmd.attach(boxcmd,0,1,1,1)
		grid_cmd.attach(rvl_parm,0,2,1,1)
		grid_cmd.attach(boxdesc,0,3,1,1)
		grid.add(grid_cmd)

		box_btn=Gtk.Box()
		box_btn.set_margin_top(MARGIN)
		box_btn.set_halign(Gtk.Align.END)
		btn_ok=Gtk.Button.new_from_icon_name("gtk-apply",Gtk.IconSize.BUTTON)
		btn_ok.connect("clicked",_begin_add_new_command)
		btn_ok.set_tooltip_text(_("Add command"))
		btn_cancel=Gtk.Button.new_from_icon_name("gtk-close",Gtk.IconSize.BUTTON)
		btn_cancel.connect("clicked",self._set_visible_stack,"tasks",Gtk.StackTransitionType.CROSSFADE,1)
		btn_cancel.set_tooltip_text(_("Cancel"))
		box_btn.add(btn_cancel)
		box_btn.add(btn_ok)
		box_btn.set_hexpand(False)
		box_btn.set_vexpand(False)
		box_btn.set_valign(Gtk.Align.CENTER)
		box_btn.set_halign(Gtk.Align.END)
		grid_cmd.add(box_btn)
		return(grid)
	#def _render_new_command

	def _render_tasks(self):
		hbox=Gtk.Box()
		scrollbox=Gtk.ScrolledWindow()
		scrollbox.set_min_content_height(500)
		scrollbox.set_min_content_width(800)
		scrollbox.add(self._render_tasks_grid())
		hbox.add(scrollbox)
		return(hbox)
	#def _render_tasks

	def _render_tasks_grid(self):
		grid_tasks=Gtk.Grid()
		grid_tasks.set_name("TASK_GRID")
		grid_tasks.set_vexpand(False)
		grid_tasks.set_hexpand(True)
		grid_tasks.set_valign(Gtk.Align.START)
		grid_tasks.set_halign(Gtk.Align.START)
		grid_tasks.set_row_spacing(MARGIN/3)
		grid_tasks.set_column_spacing(MARGIN/3)
#		grid_tasks.set_margin_left(MARGIN/2)
#		grid_tasks.set_margin_right(MARGIN/2)
#		grid_tasks.set_margin_top(MARGIN)
		grid_tasks.set_column_homogeneous(True)
		tasks={}
		col=0
		row=0
		#Local Tasks
		tasks.update({'local':self.scheduler.get_scheduled_tasks()})
		if self.stack.get_visible_child_name!='login':
			for task_type in tasks.keys():
				for task_group,info in tasks[task_type].items():
					(group,index)=task_group.split('||')
					btn_task=Gtk.Button()
					self._add_translation_for_desc(group)
					self._render_task_description(btn_task,task_type,group,index,info)
					if not col%self.tasks_per_row and col>0:
						col=0
						row+=1
					grid_tasks.attach(btn_task,col,row,1,1)
					col+=1
		return(grid_tasks)
	#def _render_tasks_grid

	def _render_task_description(self,btn_task,task_type,group,index,info):
		for children in btn_task.get_children():
			children.destroy()
		parsed_calendar=self.cronparser.parse_taskData(info)
		vbox_task=Gtk.VBox(spacing=MARGIN)
		vbox_task.set_margin_bottom(MARGIN)
		btn_task.set_name("TASK_BOX")
		btn_task.set_size_request(260,100)
		hbox_task=Gtk.HBox()
		txt_client=''
		if 'spread' in info.keys():
			if info['spread']:
				pb=GdkPixbuf.Pixbuf.new_from_file("%s/rsrc/dist_task.png"%BASE_DIR)
				img_banner=Gtk.Image.new_from_pixbuf(pb)
				img_banner.props.halign=Gtk.Align.START
				img_banner.set_margin_left(MARGIN)
				hbox_task.add(img_banner)
				txt_client=_("\nClient task")
		hour_box=Gtk.VBox(False,False)
		hour_box.set_name("HOUR_BOX")
		date_box=Gtk.VBox(False,False,spacing=MARGIN)
		date_box.set_margin_bottom(MARGIN)
		date_box.set_valign(Gtk.Align.END)
		date_box.set_halign(Gtk.Align.END)
		dow_box=Gtk.VBox(False,False,spacing=MARGIN)
		dow_box.set_valign(Gtk.Align.CENTER)
		eta='--'
		if 'val' in info.keys():
			if int(info['val'])<3600:
				eta="%s m."%int(info['val']/60)
			elif int(info['val'])<86400: 
				eta="%s h."%int(info['val']/3600)
			else:
				eta="%s d."%int(info['val']/86400)

		#Header
		self._debug("Search for %s"%info['cmd'])
		cmd=self._get_cmd_for_description(info['cmd'])
		lbl_task=Gtk.Label(False,False)
		lbl_task.set_ellipsize(Pango.EllipsizeMode.END)
		lbl_task.set_max_width_chars(25)
		lbl_task.set_markup("<span><big>%s</big></span>"%(_(cmd)))
		lbl_task.set_valign(Gtk.Align.START)
		lbl_group=Gtk.Label()
		lbl_group.set_markup('<span>%s</span>'%(_(group)))
		lbl_group.set_name("TASK_BOX_HEADER")
		if group in self.config.keys():
			style_context=lbl_group.get_style_context()
			style_provider=Gtk.CssProvider()
			cell_background=''
			if 'background' in self.config[group].keys():
				background=self.config[group]['background']
				css_val = "background:%s;"%background
				cell_background=background.replace('rgb','rgba')
				cell_background=cell_background.replace(')',',0.2)')
				css_cell = "background:%s;"%cell_background
			if 'color' in self.config[group].keys():
				color=self.config[group]['color']
				css_val += "color:%s;"%color
			css="*{%s}"%css_val
			css_style=eval('b"""'+css+'"""')
			style_provider.load_from_data(css_style)
			style_context.add_provider(style_provider,Gtk.STYLE_PROVIDER_PRIORITY_USER)
			if cell_background:
				style_context=btn_task.get_style_context()
				style_provider=Gtk.CssProvider()
				css="*{%s}"%css_cell
				css_style=eval('b"""'+css+'"""')
				style_provider.load_from_data(css_style)
				style_context.add_provider(style_provider,Gtk.STYLE_PROVIDER_PRIORITY_USER)
		lbl_group.set_valign(Gtk.Align.START)
		lbl_group.set_hexpand(True)
		lbl_group.set_margin_left(0)
		lbl_group.set_margin_top(0)
		lbl_group.set_margin_right(0)
		vbox_task.add(lbl_group)
		vbox_task.add(lbl_task)
		#Date Time
		(f_time,repeat_time)=self._format_time(info['h'],info['m'])
		lbl_time=Gtk.Label()
		hour_box.add(lbl_time)
		dow="%s"%(info['dow'])
		days_array=[_('Mo'),_('Tu'),_('We'),_('Th'),_('Fr'),_('Sa'),_('Su')]
		month_array=[_('Jan'),_('Feb'),_('Mar'),_('Apr'),_('May'),_('Jun'),_('Jul'),_('Aug'),_('Sep'),_('Oct'),_('Nov'),_('Dec')]
		if (dow!='*'):
			(month,day,f_date,repeat_date)=self._format_date(info['mon'],info['dom'])
			try:
				dow=int(dow)-1
				days_array[dow]='<b>%s</b>'%days_array[dow]
			except:
				if ',' in dow:
					dow_array=dow.split(',')
					for dow_str in dow_array:
						dow_int=int(dow_str)-1
						if dow_int<=len(days_array):
							days_array[dow_int]='<b>%s</b>'%days_array[dow_int]
			d_date=' '.join(days_array)
			lbl_dow=Gtk.Label()
			lbl_dow.set_markup(d_date)
			dow_box.add(lbl_dow)
			dow_box.set_name("DOW_BOX")
			if repeat_time:
				f_time=_('<span font="12px"><sup>Each </sup></span>%s')%f_time
			lbl_time.set_markup(f_time)
			add_date=True
			lbl_date=Gtk.Label()
			if repeat_date:
				if (month.replace(' ','')!='*' or day!='*'):
					f_date=_('<span font="12px">Each\n</span>%s')%f_date
					lbl_date.set_markup(f_date)
					date_box.add(lbl_date)
				else:
					hour_box.set_halign(Gtk.Align.CENTER)
					add_date=False
			else:
				lbl_mon.set_name("DATE_BOX_HEADER")
				lbl_day=Gtk.Label(day)
				date_box.add(lbl_mon)
				date_box.add(lbl_day)
			hbox_task.add(hour_box)
			if add_date:
				date_box.set_name("DATE_BOX")
				hbox_task.add(date_box)
			vbox_task.add(hbox_task)
			vbox_task.add(dow_box)
		else:
			(month,day,f_date,repeat_date)=self._format_date(info['mon'],info['dom'])
			if month.isdigit():
				lbl_mon=Gtk.Label(month_array[int(month)-1])
			else:
				lbl_mon=Gtk.Label(month)
			lbl_mon.set_name("DATE_BOX_HEADER")
			lbl_day=Gtk.Label(day)
			lbl_date=Gtk.Label()
			date_box.set_name("DATE_BOX")
			hour_box.set_halign(Gtk.Align.CENTER)
			hour_box.set_valign(Gtk.Align.CENTER)
			if repeat_time:
				hour_box.set_halign(Gtk.Align.CENTER)
				if (month.replace(' ','')!='*' or day!='*'):
					f_time=_('<span font="12px">Each\n</span>%s')%f_time
				else:
					hour_box.set_halign(Gtk.Align.CENTER)
					f_time=_('<span font="12px"><sup>Each </sup></span>%s')%f_time
			lbl_time.set_markup(f_time)
			add_date=True
			if repeat_date:
				if (month.replace(' ','')!='*' or day!='*'):
					f_date=_('<span font="12px">Each\n</span>%s')%f_date
					lbl_date.set_markup(f_date)
					date_box.add(lbl_date)
				else:
					hour_box.set_halign(Gtk.Align.CENTER)
					add_date=False
			else:
				lbl_mon.set_name("DATE_BOX_HEADER")
				lbl_day=Gtk.Label(day)
				date_box.set_name("DATE_BOX")
				date_box.set_halign(Gtk.Align.CENTER)
				date_box.add(lbl_mon)
				date_box.add(lbl_day)
			hbox_task.add(hour_box)
			if add_date:
				hbox_task.add(date_box)
			vbox_task.add(hbox_task)
		hbox_btn=Gtk.Box()
		btn_task.add(vbox_task)
		txt_edit=''
		if 'protected' in info.keys() and info['protected']==True:
				style_context=btn_task.get_style_context()
				style_provider=Gtk.CssProvider()
				css_cell = 'background-image:url("%s");background-repeat:no-repeat;background-position:50% 50% 90% 10%;background-size: 45% 50%'%NO_EDIT_ICON
				css="*{%s}"%css_cell
				css_style=eval('b"""'+css+'"""')
				style_provider.load_from_data(css_style)
				style_context.add_provider(style_provider,Gtk.STYLE_PROVIDER_PRIORITY_USER)
				if txt_client:
					txt_edit=_(" - No editable")
				else:
					txt_edit=_("\nNo editable")
		else:
			btn_task.connect("clicked",self._edit_task,task_type,group,index,info)
		vbox_task.set_tooltip_text(_("%s\n%s\nLaunch in: %s%s%s")%(_(cmd),parsed_calendar,eta,txt_client,txt_edit))
		return(vbox_task)
	#def _render_task_description

	def _format_time(self,h,m):
		(repeat,repeat_hour,repeat_min)=(False,False,False)
		f_time=''
		h=self._format_time_unit(h)
		m=self._format_time_unit(m)
		repeat=False
		if ('*' in h or '*' in m):
			if h=='*':
				h="1"
				repeat_hour=True
			else:
				m='1'
				repeat_min=True
				repeat_hour=False
		if ('/' in h or '/' in m):
			if '/' in h:
				h=h.split('/')[-1]
				repeat_hour=True
			else:
				m=m.split('/')[-1]
				repeat_min=True
				repeat_hour=False
		if repeat_hour:
			repeat=True
			if m!='00':
				f_time=(_('%s<span font="10px">h. </span><span font="12px"><sup>at</sup> </span>%s<span font="10px">m.</span>'%(h,m)))
			else:
				f_time=(_('%s<span font="10px">h.</span>'%(h)))
		elif repeat_min:
			repeat=True
			f_time=(_('%s<span font="10px">m.</span>'%(m)))
		else:
			f_time="%s:%s"%(h,m)
		return(f_time,repeat)
	#def _format_time

	def _format_date(self,mon,dom):
		(repeat,repeat_mon,repeat_dom)=(False,False,False)
		f_date=''
		mon=self._format_time_unit(mon)
		dom=self._format_time_unit(dom)
		repeat=False
		if ('*' in dom or '*' in mon):
			if mon=='*':
				repeat_mon=True
			else:
				repeat_dom=True
				repeat_mon=False
		if ('/' in mon or '/' in dom):
			if '/' in mon:
				mon=mon.split('/')[-1]
				repeat_mon=True
			else:
				dom=dom.split('/')[-1]
				repeat_dom=True
				repeat_mon=False
		if repeat_mon:
			repeat=True
			f_date=(_('%s<span font="10px">M.</span>'%(mon)))
		elif repeat_dom:
			repeat=True
			f_date=(_('%s<span font="10px">d.</span>'%(dom)))
		else:
			f_date="%s/%s"%(mon,dom)
		return(mon,dom,f_date,repeat)
	#def _format_date

	def _format_time_unit(self,unit):
		if ('*' not in unit and '/' not in unit):
			if int(unit)<10:
				unit="0%s"%unit
		return unit
	#def _format_time_unit

	def _edit_task(self,widget,task_type,group,index,info):
		def _popdown(*args):
			pop.popdown()

		task={}
		task['type']=task_type
		task['name']=group
		task['serial']=index
		task.update({'data':info})
		if task_type:
			pop=Gtk.Popover.new(widget)
			pop.set_modal(True)
			pop.set_position(Gtk.PositionType.RIGHT)
			vbox=Gtk.Grid()
			add_task_grid=detailDateBox(self.scheduler)
			task_grid=add_task_grid.render_form()
			vbox.attach(task_grid,0,1,4,1)
			add_task_grid.set_task_data(task)
			add_task_grid.load_task_details()
			box_btn=Gtk.Grid()
			btn_del=Gtk.Button.new_from_icon_name("edit-delete",Gtk.IconSize.BUTTON)
			btn_del.connect("clicked",self._delete_task,pop,widget,add_task_grid,task)
			btn_del.set_margin_right(MARGIN*2)
			btn_del.set_tooltip_text(_("Delete task"))
			btn_ok=Gtk.Button.new_from_icon_name("gtk-apply",Gtk.IconSize.BUTTON)
			btn_ok.set_tooltip_text(_("Save task"))
			btn_ok.connect("clicked",self._save_task,pop,widget,add_task_grid)
			btn_cancel=Gtk.Button.new_from_icon_name("gtk-close",Gtk.IconSize.BUTTON)
			btn_cancel.set_tooltip_text(_("Cancel"))
			btn_cancel.connect("clicked",_popdown)
			box_btn.add(btn_del)
			box_btn.add(btn_cancel)
			box_btn.add(btn_ok)
			box_btn.set_halign(Gtk.Align.END)
			task_grid.attach_next_to(box_btn,add_task_grid.chk_spread,Gtk.PositionType.RIGHT,4,1)
			vbox.show_all()
			pop.add(vbox)
			pop.popup()
	#def _edit_task(self,widget,task_type,group,index,info):

	def _add_task(self,*args):
		def _load_task_cmds(widget):
			actions=[]
			cmb_commands.remove_all()
			task_name=widget.get_active_text()
			if task_name:
				i18n_name=self._get_translation_for_desc(task_name)
				for action in tasks[i18n_name].keys():
					if action not in actions:
						self._add_translation_for_desc(action)
						actions.append(action)
						cmb_commands.append_text(_(action))
			cmb_commands.set_active(0)

		def _popdown(*args):
			pop.popdown()

		def _begin_add(*args):
			tasks=cmb_tasks.get_active_text()
			commands=cmb_commands.get_active_text()
			self._save_task(None,pop,None,add_task_grid,tasks,commands)
		attach=args[0]
		if len(args)>1:
			attach=args[1]
		pop=Gtk.Popover.new(attach)
		pop.set_modal(True)
		pop.set_position(Gtk.PositionType.RIGHT)
		vbox=Gtk.Grid()
		vbox.set_column_homogeneous(False)
		vbox.set_margin_top(MARGIN)
		vbox.set_margin_right(MARGIN)
		add_task_grid=detailDateBox(self.scheduler)
		vbox.attach(Gtk.Label(_("Task group")),0,0,1,1)
		cmb_tasks=Gtk.ComboBoxText()
		(tasks,names)=self._load_tasks()
		for task in names:
			cmb_tasks.append_text(_(task))
		cmb_commands=Gtk.ComboBoxText()
		cmb_tasks.connect('changed',_load_task_cmds)
		cmb_tasks.set_active(0)

		vbox.attach(cmb_tasks,1,0,1,1)
		vbox.attach(Gtk.Label(_("Command")),2,0,1,1)
		vbox.attach(cmb_commands,3,0,1,1)
		task_grid=add_task_grid.render_form()
		box_btn=Gtk.Grid()
		btn_ok=Gtk.Button.new_from_icon_name("gtk-apply",Gtk.IconSize.BUTTON)
		btn_ok.set_tooltip_text(_("Add task"))
		btn_ok.connect("clicked",_begin_add)
		btn_cancel=Gtk.Button.new_from_icon_name("gtk-close",Gtk.IconSize.BUTTON)
		btn_cancel.set_tooltip_text(_("Cancel"))
		btn_cancel.connect("clicked",_popdown)
		box_btn.add(btn_cancel)
		box_btn.add(btn_ok)
		box_btn.set_halign(Gtk.Align.END)
		task_grid.attach_next_to(box_btn,add_task_grid.chk_spread,Gtk.PositionType.RIGHT,4,1)
		vbox.attach(task_grid,0,1,5,1)
		vbox.show_all()
		pop.add(vbox)
		pop.popup()
	#def _add_task

	def _delete_task(self,widget,pop,button,add_task_grid,task):
		task.update(task['data'])
		if self.scheduler.remove_task(task):
			pop.popdown()
			th=threading.Thread(target=self._refresh_grid_tasks,args=[])
			th.start()
	#def _delete_task

	def _refresh_grid_tasks(self,*args):
		(gtkgrid,hbox)=self._get_tasks_grid()
		for i in range(10,0,-1):
			gtkgrid.set_opacity(i/10)
			time.sleep(0.1)
		GLib.timeout_add(1,self._refresh_grid_task_data,gtkgrid,hbox)
		for i in range(11):
			gtkgrid.set_opacity(i/10)
			time.sleep(0.1)
	#def _refresh_grid_tasks

	def _refresh_grid_task_data(self,gtkgrid,hbox):
		gtkgrid.destroy()
		grid=self._render_tasks_grid()
		grid.show_all()
		hbox.add(grid)
		return(False)
	#def _refresh_grid_task_data

	def _save_task(self,widget,pop,button,add_task_grid,tasks=None,commands=None):
		if tasks and commands:
			task={}
			task['name']=self._get_translation_for_desc(tasks)
			task['serial']=""
			task['cmd']=self._get_translation_for_desc(commands)
			task.update({'data':add_task_grid._parse_screen()})
			add_task_grid.set_task_data(task)
		task=add_task_grid.get_task_details()
		#Replace cmd description by cmd
		for g_name in task.keys():
			for i_task in task[g_name].keys():
				task[g_name][i_task]['cmd']=self._get_description_for_cmd(task[g_name][i_task]['cmd'])
		self._debug("Writing task info...%s"%task)
		self.autorefresh=False
		(status,msg)=self.scheduler.write_tasks(task)
		if status:
			self._debug("OK - %s - %s"%(msg,tasks))
			self._debug("%s"%(task))
			if tasks in task.keys():
				if '' in task[tasks].keys():
					task[tasks][msg]=task[tasks]['']
					del (task[tasks][''])
		else:
			self._debug("ERR: %s"%status)
		pop.popdown()
		if button:
			th=threading.Thread(target=self._refresh_box_task,args=[button,task])
			th.start()
		else:
			button=Gtk.Button()
			th=threading.Thread(target=self._refresh_box_task,args=[button,task,True])
			th.start()
	#def _save_tasks

	def _refresh_box_task(self,widget,task,add=False):
		if add:
			(gtkgrid,hbox)=self._get_tasks_grid()
			if gtkgrid:
				items=len(gtkgrid.get_children())
				row=int(items/self.tasks_per_row)
				col=items-(row*self.tasks_per_row)
				gtkgrid.attach(widget,col,row,1,1)

		for i in range(10,0,-1):
			widget.set_opacity(i/10)
			time.sleep(0.1)
		GLib.timeout_add(1,self._refresh_box_task_data,widget,task)
		for i in range(11):
			widget.set_opacity(i/10)
			time.sleep(0.1)
		self._append_task(widget)
	#def _refresh_box_task

	def _refresh_box_task_data(self,widget,task):
		self._debug("Refresh %s"%task)
		info={}
		for g_group, g_index in task.items():
			group=g_group
			for i_index,i_info in g_index.items():
				index=i_index
				info=i_info
		if info['spread']=='false':
			task_type='local'
		else:
			task_type='remote'
		info['cmd']=self._get_cmd_for_description(info['cmd'])
		self._render_task_description(widget,task_type,group,index,info)
		widget.show_all()
		return(False)
	#def _refresh_box_task_data

	def _append_task(self,button):
		pass

	def _load_tasks(self):
		tasks=[]
		names=[]
		cmds=[]
		tasks=self.scheduler.get_available_tasks()
		for name,command in tasks.items():
			if name not in names and name:
				names.append(name)
				self._add_translation_for_desc(name)
			for cmd in command.keys():
				if cmd not in cmds and cmd:
					cmds.append(cmd)
					self._add_description_for_cmd(cmd,command[cmd])
		return(tasks,names)
	#def load_tasks

	def _get_tasks_grid(self):
		gtkgrid=None
		for stack_children in self.stack.get_children():
			if "Grid" in str(stack_children):
				for grid_children in stack_children.get_children():
					if "Box" in str(grid_children):
						for hbox_children in grid_children.get_children():
							if "Scrolled" in str(hbox_children):
								for scroll_children in hbox_children.get_children():
									hbox=scroll_children
									for children in scroll_children.get_children():
										if "Grid" in str(children):
											gtkgrid=children
											break
					if gtkgrid:
						break
			if gtkgrid:
				break
		return (gtkgrid,hbox)
	#def _get_tasks_grid

	def _about(self,*args):
		dlg_about=Gtk.AboutDialog()
		dlg_about.set_license_type(Gtk.License.GPL_3_0_ONLY)
		pb=GdkPixbuf.Pixbuf.new_from_file("%s"%BANNER_IMG)
		dlg_about.set_logo(pb)
		dlg_about.set_program_name("TaskScheduler")
		dlg_about.set_version("2.0")
		dlg_about.set_website("http://lliurex.net")
		dlg_about.set_website_label("LliureX")
		dlg_about.set_copyright("LliureX Team")
		dlg_about.set_authors("LliureX Team")
		r=dlg_about.run()
		if r<0:
			dlg_about.close()
	#def _about

	def _help(self,*args):
		webbrowser.open("http://wiki.lliurex.net/tiki-index.php?page=Programador+de+Tareas")

	def _add_description_for_cmd(self,cmd,desc):
		sw_ok=True
		if cmd not in self.command_description:
			self._debug("Desc add %s -> %s"%(cmd,desc))
			self.command_description.update({cmd:desc})
			self.description_command.update({desc:cmd})
	#def _add_description_for_cmd(self,cmd,desc):

	def _get_description_for_cmd(self,cmd):
		desc=cmd
		if cmd in self.command_description.keys():
			desc=self.command_description[cmd]
		self._debug("Desc get %s -> %s"%(cmd,desc))
		return desc
	#def _get_description_for_cmd(self,cmd,desc):

	def _get_cmd_for_description(self,desc):
		cmd=desc
		if "bellscheduler-token-management" in cmd:
			cmd=self._get_bell_name(cmd)
		elif desc in self.description_command.keys():
			cmd=self.description_command[desc]
		self._debug("Cmd get %s -> %s"%(desc,cmd))
		return cmd
	#def _get_description_for_cmd(self,cmd,desc):

	def _get_translation_for_desc(self,desc):
		i18n_name=desc
		if desc in self.i18n.keys():
			i18n_name=self.i18n[desc]
		self._debug("i18n get %s -> %s"%(desc,i18n_name))
		return i18n_name
	#def _get_translation_for_desc

	def _add_translation_for_desc(self,desc):
		sw_ok=True
		self._debug("i18n add %s -> %s"%(_(desc),desc))
		self.i18n.update({_(desc):desc})
		return sw_ok
	#def _add_translation_for_desc

	def _get_bell_name(self,cmd):
		desc="Bell"
		f_bell='/etc/bellScheduler/bell_list'
		if os.path.isfile(f_bell):
			index=''
			list_cmd=cmd.split(' ')
			list_cmd.reverse()
			for word in list_cmd:
				if word.isdigit():
				#First number must be bell index
					index=word
					break
			if index:
				try:
					data=json.loads(open(f_bell).read())
					if index in data.keys():
						desc+=": %s"%data[index]['name']
				except:
					pass
		return desc

	def set_css_info(self):
		css = b"""

		#GtkCombo
		{
			font-family: Roboto;
			border:0px;
			border-bottom:1px grey solid;
			margin-top:0px;
			padding-top:0px;
		}

		#GtkEntry{
			font-family: Roboto;
			border:0px;
			border-bottom:1px grey solid;
			margin-top:0px;
			padding-top:0px;
		}

		#TASK_GRID
		{
			margin:6px;
		}

		#TASK_BOX, #TASK_BOX:focus
		{
			border:0px;
			margin:6px;
			padding:0px;
			background:white;
			box-shadow: -0.5px 3px 2px #aaaaaa;
			font: 12px roboto;
			background-image:none;

		}
	
		#SPREAD_TASK_BOX
		{
			background-image: url("/home/lliurex/git/taskscheduler/scheduler-gui.install/usr/share/taskscheduler/rsrc/dist_task.png");
			background-size: auto;
			background-repeat:no-repeat;
		}

		#SPREAD_TASK_BOX2
		{
			border:1px solid grey;
			margin:6px;
			padding:3px;
			background: linear-gradient(
			  45deg,
			  white,
			  white 50%,
			  #c9c9c9 50%,
			  #c9c9c9
			  );
			box-shadow: -0.5px 3px 2px #aaaaaa;
			font: 12px roboto;

		}


		#TASK_BOX_HEADER
		{
			border-bottom:0px solid grey;
			font: 16px roboto;
			background: orange;
			padding:6px;
		}

		#ADD_BUTTON
		{
			font: 32px roboto bold;
			color: silver;
		}

		#HOUR_BOX
		{
			font:36px roboto;
			font-stretch: ultra-condensed;
			color:gray;
			padding:0px;
		}

		#DATE_BOX
		{
			font: 16px roboto;
			border:1px solid silver;
			margin:6px;
			background-color:white;
		}

		#DATE_BOX_HEADER
		{
			color:white;
			background:red;
			padding:3px;
		}

		#DOW_BOX
		{
			font: 14px Roboto;
			font-stretch: expanded;
		}

		#MAIN_COMMANDS_GRID
		{
			background: rgba(0,0,0,0.5);
		}

		#COMMANDS_GRID
		{
			border:1px solid grey;
			margin:6px;
			padding:3px;
			background:white;
			box-shadow: 0.5px 4px 3px #000000;
			font: 12px roboto;
		}

		#ENTRY_LABEL{
			color:grey;
			padding:6px;
			padding-bottom:0px;
			margin-bottom:0px;
			border:0px;
		}
		"""
		self.style_provider=Gtk.CssProvider()
		self.style_provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
	#def set_css_info	
	
	def sig_refresh_grid_tasks(self,*args):
		if self.autorefresh==False:
			self.autorefresh=True
		else:
			(gtkgrid,hbox)=self._get_tasks_grid()
			for i in range(10,0,-1):
				gtkgrid.set_opacity(i/10)
				time.sleep(0.1)
			GLib.timeout_add(1,self._refresh_grid_task_data,gtkgrid,hbox)
			for i in range(11):
				gtkgrid.set_opacity(i/10)
				time.sleep(0.1)
		GLib.idle_add(self.install_handler,signal.SIGUSR1,priority=GLib.PRIORITY_HIGH)
	#def sig_refresh_grid_tasks

#class TaskScheduler
pid=str(os.getpid())
pidfile="/tmp/taskscheduler.pid"
if os.path.isfile(pidfile):
	os.unlink(pidfile)
f_pid=open(pidfile,'w')
f_pid.write(pid)
f_pid.close()
GObject.threads_init()
t=TaskScheduler()
t.start_gui()		
