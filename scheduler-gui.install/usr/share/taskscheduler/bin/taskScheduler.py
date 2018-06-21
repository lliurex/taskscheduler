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
#import commands
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib, PangoCairo, Pango
import time
from taskscheduler.taskscheduler import TaskScheduler as scheduler
from taskscheduler.cronParser import cronParser
from detailDateBox import DetailBox as detailDateBox 
from edupals.ui.n4dgtklogin import *
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext

BASE_DIR="/usr/share/taskscheduler/"
#BASE_DIR="../share/taskscheduler/"
GLADE_FILE=BASE_DIR+"rsrc/taskScheduler.ui"
REMOVE_ICON=BASE_DIR+"rsrc/trash.svg"
EDIT_ICON=BASE_DIR+"rsrc/edit.svg"
LOGIN_IMG=BASE_DIR+"rsrc/scheduler.svg"
NO_EDIT_ICON=BASE_DIR+"rsrc/no_edit.svg"
LOCK_PATH="/var/run/taskScheduler.lock"
WIDGET_MARGIN=6
DBG=0

class TaskScheduler:
	def __init__(self):
		self.is_scheduler_running()
		try:
			self.flavour=subprocess.getoutput("lliurex-version -f")
		except:
			self.flavour="client"
		self.last_task_type='remote'
		self.ldm_helper='/usr/sbin/sched-ldm.sh'
		self.i18n={}
			
	#def __init__		

	def _debug(self,msg):
		if DBG:
			print("taskScheduler: %s"%msg)
	#def _debug

	def is_scheduler_running(self):
		if os.path.exists(LOCK_PATH):
			dialog = Gtk.MessageDialog(None,0,Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Task Scheduler")
			dialog.format_secondary_text(_("There's another instance of Task Scheduler running."))
			dialog.run()
			sys.exit(1)
	#def is_scheduler_running

	def start_gui(self):
		self.scheduler=scheduler()
		builder=Gtk.Builder()
		builder.set_translation_domain('taskscheduler')

		self.stack = Gtk.Stack()
		self.stack.set_transition_duration(1000)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

		glade_path=GLADE_FILE
		builder.add_from_file(glade_path)

		self.window=builder.get_object("main_window")
		self.window.set_resizable(False)
		self.main_box=builder.get_object("main_box")
		btn_exit=builder.get_object("btn_exit")
		btn_exit.connect('clicked',self.quit)
		self.login=N4dGtkLogin()
		self.login.set_allowed_groups(['adm','teachers'])
		desc=_("Welcome to the Task Scheduler for Lliurex.\nFrom here you can:\n<sub>* Schedule tasks in the local pc\n* Distribute tasks among all the pcs in the network\n*Show scheduled tasks</sub>")
		self.login.set_info_text("<span foreground='black'>Task Scheduler</span>",_("Task Scheduler"),"<span foreground='black'>"+desc+"</span>\n")
#		self.login.set_info_background(image='taskscheduler',cover=True)
		self.login.set_info_background(image=LOGIN_IMG,cover=False)
		self.login.after_validation_goto(self._signin)
		self.login.hide_server_entry()
		self.inf_message=Gtk.InfoBar()
		self.inf_message.set_show_close_button(True)
		self.lbl_message=Gtk.Label("")
		self.inf_message.get_action_area().add(self.lbl_message)
		self.inf_message.set_halign(Gtk.Align.CENTER)
		self.inf_message.set_valign(Gtk.Align.CENTER)
		def hide(widget,response):
			self.inf_message.hide()
		self.inf_message.connect('response',hide)
#		self.inf_message.props.no_show_all=True

		self.inf_question=Gtk.InfoBar()	
		self.lbl_question=Gtk.Label("")
		self.inf_question.get_action_area().add(self.lbl_question)
		self.inf_question.add_button(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL)
		self.inf_question.add_button(Gtk.STOCK_OK,Gtk.ResponseType.OK)
		self.inf_question.set_halign(Gtk.Align.CENTER)
		self.inf_question.set_valign(Gtk.Align.CENTER)
#		self.inf_question.props.no_show_all=True
		self.main_box.pack_start(self.inf_question,False,False,0)
		self.main_box.pack_start(self.inf_message,False,False,0)
		self.view_tasks_button_box=builder.get_object("view_tasks_button_box")
		self.view_tasks_eb=builder.get_object("view_tasks_eventbox")
		self.btn_signal_id=None
		#Toolbar
		self.toolbar=builder.get_object("toolbar")
		self.toolbar.set_visible(False)
		self.btn_add_task=builder.get_object("btn_add_task")
		self.btn_add_task.connect("button-release-event", self.add_task_clicked)
		self.btn_refresh_tasks=builder.get_object("btn_refresh_tasks")
		self.btn_refresh_tasks.connect("button-release-event", self._reload_grid)
		self.btn_manage_tasks=builder.get_object("btn_manage_tasks")
		self.btn_manage_tasks.connect("button-release-event", self._manage_tasks)
		self.txt_search=builder.get_object("txt_search")
		self.txt_search.connect('changed',self.match_tasks)
		#tasks list
		self._load_task_list_gui(builder)
		#Manage tasks
		self._load_manage_tasks(builder)
		#Icons
		image=Gtk.Image()
		image.set_from_file(REMOVE_ICON)		
		self.remove_icon=image.get_pixbuf()
		image.set_from_file(EDIT_ICON)		
		self.edit_icon=image.get_pixbuf()
		image.set_from_file(NO_EDIT_ICON)		
		self.no_edit_icon=image.get_pixbuf()

		self.stack.add_titled(self.tasks_box, "tasks", "Tasks")
		self.stack.add_titled(self.manage_box, "manage", "Manage")
		self.stack.add_titled(self.add_task_box, "add", "Add Task")
		self.stack.add_titled(self.login, "login", "Login")
		#Packing
		self.main_box.pack_start(self.stack,True,False,0)

		self.toolbar.props.no_show_all=True
		self.window.connect("destroy",self.quit)
		self.window.set_resizable(False)
		self.window.show_all()
		self.inf_message.hide()
		self.inf_question.hide()
		self.set_css_info()
		#Load stack
		self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
		self.stack.set_visible_child_name("login")
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

		Gtk.main()
	#def start_gui

	def _load_task_list_gui(self,builder):
		self.tasks_box=builder.get_object("tasks_box")
		self.tasks_label=builder.get_object("tasks_label")
		self.tasks_tv=builder.get_object("tasks_treeview")
		self.tasks_store=Gtk.ListStore(str,str,str,GdkPixbuf.Pixbuf,GdkPixbuf.Pixbuf,str,str,str,str)
		self.tasks_store_filter=self.tasks_store.filter_new()
		self.tasks_store_filter.set_visible_func(self.filter_tasklist)
		self.tasks_tv.set_model(self.tasks_store_filter)
		self.tasks_tv.connect("button-release-event",self.task_clicked)
		self.tasks_tv.connect("row-activated",self.task_clicked)
		self.tasks_tv.connect("cursor-changed",self.task_clicked)

		column=Gtk.TreeViewColumn(_("Task"))
		cell=Gtk.CellRendererText()
		column.pack_start(cell,True)
		column.add_attribute(cell,"markup",0)
		column.add_attribute(cell,"cell_background",7)
		column.add_attribute(cell,"foreground",8)
		column.set_expand(True)
		self.tasks_tv.append_column(column)
		
		column=Gtk.TreeViewColumn(_("Serial"))
		cell=Gtk.CellRendererText()
		column.pack_start(cell,True)
		column.add_attribute(cell,"markup",1)
		column.add_attribute(cell,"cell_background",7)
		column.add_attribute(cell,"foreground",8)
		column.set_expand(True)
		column.set_visible(False)
		self.tasks_tv.append_column(column)
		
		column=Gtk.TreeViewColumn(_("When"))
		cell=Gtk.CellRendererText()
		cell.set_property("alignment",Pango.Alignment.CENTER)
		column.pack_start(cell,False)
		column.add_attribute(cell,"markup",2)
		column.add_attribute(cell,"cell_background",7)
		column.add_attribute(cell,"foreground",8)
		column.set_expand(True)
		self.tasks_tv.append_column(column)		

		column=Gtk.TreeViewColumn(_("Edit"))

		cell=Gtk.CellRendererPixbuf()
		column.pack_start(cell,True)
		column.add_attribute(cell,"pixbuf",3)
		column.add_attribute(cell,"cell_background",7)
		self.col_edit=column
		self.tasks_tv.append_column(column)
		
		column=Gtk.TreeViewColumn(_("Remove"))
		cell=Gtk.CellRendererPixbuf()
		column.pack_start(cell,True)
		column.add_attribute(cell,"pixbuf",4)
		column.add_attribute(cell,"cell_background",7)
		self.col_remove=column
		self.tasks_tv.append_column(column)

		column=Gtk.TreeViewColumn(_("Command"))
		cell=Gtk.CellRendererText()
		column.pack_start(cell,True)
		column.add_attribute(cell,"markup",5)
		column.set_expand(True)
		column.set_visible(False)
		self.tasks_tv.append_column(column)
		
		column=Gtk.TreeViewColumn(_("Type"))
		cell=Gtk.CellRendererText()
		column.pack_start(cell,True)
		column.add_attribute(cell,"markup",6)
		column.set_expand(True)
		column.set_visible(False)
		self.tasks_tv.append_column(column)

		self.tasks_tv.set_search_column(2)
		self.tasks_tv.set_search_entry(self.txt_search)

		#Add tasks
		self.add_task_box=builder.get_object("add_task_box")
		self.add_task_grid=detailDateBox(self.scheduler)
		at_grid=self.add_task_grid.render_form(builder.get_object("add_task_grid"))
		at_grid=builder.get_object("add_task_grid")
		at_grid.set_hexpand(False)
		self.cmb_task_names=builder.get_object("cmb_task_names")
		self.cmb_task_cmds=builder.get_object("cmb_task_cmds")
		builder.get_object("btn_back_add").connect("clicked", self.cancel_add_clicked)
		builder.get_object("btn_cancel_add").connect("clicked", self.cancel_add_clicked)
		self.btn_confirm_add=builder.get_object("btn_confirm_add")
		self.btn_confirm_add.connect("clicked", self.save_task_details)
	#def _load_task_list_gui

	def _load_manage_tasks(self,builder):
		self.manage_box=builder.get_object("manage_box")
		custom_grid=builder.get_object("custom_grid")
		custom_grid.set_margin_left(WIDGET_MARGIN*2)
		custom_grid.set_margin_top(WIDGET_MARGIN*2)
		txt_taskname=Gtk.Entry()
		txt_taskname.set_tooltip_text(_("A descriptive name for the command"))
		txt_taskname.set_placeholder_text(_("Task name"))
		lbl_name=Gtk.Label(_("Task name"))
		lbl_name.set_halign(Gtk.Align.END)
		btn_add_cmd=Gtk.Button.new_from_stock(Gtk.STOCK_ADD)
		custom_grid.attach(lbl_name,0,0,1,1)
		custom_grid.attach(txt_taskname,1,0,1,1)
		cmb_cmds=Gtk.ComboBoxText()
		i18n_cmd=self.load_cmb_cmds(cmb_cmds)
		lbl_cmd=Gtk.Label(_("Command"))
		lbl_cmd.set_halign(Gtk.Align.END)
		custom_grid.attach(lbl_cmd,0,1,1,1)
		custom_grid.attach(cmb_cmds,1,1,1,1)
		custom_grid.attach(btn_add_cmd,2,1,1,1)
		chk_parm_is_file=Gtk.CheckButton(_("Needs a file"))
		chk_parm_is_file.set_tooltip_text(_("Mark if the command will launch a file"))
		btn_file=Gtk.FileChooserButton()
		chk_parm_is_file.set_tooltip_text(_("Select the file that will be launched"))
		chk_parm_is_file.connect('toggled',self._enable_filechooser,btn_file)
		txt_params=Gtk.Entry()
		txt_params.set_placeholder_text(_("Needed arguments"))
		txt_params.set_tooltip_text(_("Put here the arguments for the command (if any)"))
		lbl_arg=Gtk.Label(_("Arguments"))
		lbl_arg.set_halign(Gtk.Align.END)
		custom_grid.attach(lbl_arg,3,1,1,1)
		custom_grid.attach(txt_params,4,1,1,1)
		custom_grid.attach(chk_parm_is_file,3,0,1,1)
		custom_grid.attach(btn_file,4,0,1,1)
		btn_file.set_sensitive(False)
		self.btn_apply_manage=builder.get_object("btn_apply_manage")
		self.btn_apply_manage.connect("clicked",self._add_custom_task,txt_taskname,cmb_cmds,txt_params,chk_parm_is_file,btn_file,i18n_cmd)
		self.btn_back_manage=builder.get_object("btn_back_manage")
		self.btn_back_manage.connect("clicked",self._cancel_manage_clicked)
		self.btn_cancel_manage=builder.get_object("btn_cancel_manage")
		self.btn_cancel_manage.connect("clicked",self._cancel_manage_clicked)
		btn_add_cmd.connect("clicked",self._add_cmd_clicked,cmb_cmds)
	#def _load_manage_tasks

	def load_cmb_cmds(self,cmb_cmds):
		cmb_cmds.remove_all()
		cmds=self.scheduler.get_commands()
		i18n_cmd={}
		for cmd in cmds.keys():
			i18n_cmd[_(cmd)]=cmd
			cmb_cmds.append_text(_(cmd))
		return(i18n_cmd)

	def _add_cmd_clicked(self,*args):
		cmb_cmds=args[-1]
		def show_file_dialog(*args):
			file_response=dlg_file.run()
			if file_response == Gtk.ResponseType.OK:
				txt_file.set_text(dlg_file.get_filename())
#			dlg_file.destroy()
		dialog=Gtk.Dialog()
		dialog.add_buttons(Gtk.STOCK_APPLY,42,"Close",Gtk.ResponseType.CLOSE)
		box=dialog.get_content_area()
		hbox=Gtk.Grid()
		hbox.set_column_spacing(WIDGET_MARGIN)
		hbox.set_row_spacing(WIDGET_MARGIN)
		lbl_name=Gtk.Label(_("Action name"))
		txt_name=Gtk.Entry()
		txt_name.set_tooltip_text("Enter the name for the action")
		lbl_file=Gtk.Label(_("Command"))
		txt_file=Gtk.Entry()
		txt_file.set_tooltip_text("Enter the command or choose one from the file selector")
		dlg_file=Gtk.FileChooserDialog(_("Choose a command"),dialog,Gtk.FileChooserAction.OPEN,(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK))
		btn_file=Gtk.Button.new_from_stock(Gtk.STOCK_FILE)
		btn_file.connect("clicked",show_file_dialog)
		hbox.attach(lbl_name,0,0,1,1)
		hbox.attach(txt_name,1,0,1,1)
		hbox.attach(lbl_file,0,1,1,1)
		hbox.attach(txt_file,1,1,1,1)
		hbox.attach(btn_file,2,1,1,1)
		hbox.attach(Gtk.Separator(),0,2,2,1)
		box.add(hbox)
		box.show_all()
		response=dialog.run()
		if response==Gtk.ResponseType.CLOSE:
			dialog.destroy()
		if response==42:
			self._add_custom_cmd(txt_name.get_text(),txt_file.get_text())
			self.load_cmb_cmds(cmb_cmds)
	#def _add_cmd_clicked

	def _add_custom_cmd(self,name,cmd):
		self.scheduler.add_command(name,cmd)
	
	def _enable_filechooser(self,widget,filechooser):
		if widget.get_active():
			filechooser.set_sensitive(True)
		else:
			filechooser.set_sensitive(False)
	#def _enable_filechooser

	def _add_custom_task(self,widget,w_name,w_cmd,w_parms,w_chk,w_file,i18n_cmd=None):
		name=w_name.get_text()
		cmd=w_cmd.get_active_text()
		if i18n_cmd:
			cmd_desc=i18n_cmd[cmd]
		else:
			cmd_desc=cmd
		parms=w_parms.get_text()
		cmd=self.scheduler.get_command_cmd(cmd_desc)
		if w_chk.get_active():
			parms=parms+' '+w_file.get_uri().replace('file://','')
		if self.scheduler.write_custom_task(name,cmd,parms):
			self._show_info(_("Task saved"))
		else:
			self._show_info(_("Permission denied"))
	#def _add_custom_task

	def _signin(self,user=None,pwd=None,server=None,data=None):
		self.scheduler.set_credentials(user,pwd,server)
		self.stack.set_visible_child_name("tasks")
		self.populate_tasks_tv()
		self.toolbar.show()
	#def _signin

	def populate_tasks_tv(self,sw_remote=False):
		self._debug("Populating task list")
		self.scheduled_tasks={}
		tasks=[]
		sw_tasks=False
		tasks=self.scheduler.get_scheduled_tasks(sw_remote)
		self.tasks_store.clear()
		if type(tasks)==type({}):	
			parser=cronParser()
			self.i18n['cmd']={}
			self.i18n['name']={}
			for task_name in tasks.keys():
				for serial in tasks[task_name].keys():
					task=tasks[task_name][serial]
					task['sw_remote']=''
					color_palette=['goldenrod','DarkSlateGrey','Burlywood','DarkSlateGrey','DarkSlateBlue','bisque','LightSteelBlue','DarkSlateGrey']
					bg_color=color_palette[0]
					fg_color=color_palette[1]
					if 'kind' in task.keys():
						if 'fixed' in task['kind']:
							bg_color=color_palette[2]
							fg_color=color_palette[3]
						elif 'repeat' in task['kind']:
							bg_color=color_palette[4]
							fg_color=color_palette[5]
						elif 'daily' in task['kind']:
							bg_color=color_palette[6]
							fg_color=color_palette[7]
					else:
						task['kind']=''
					remote='Local task'
					if 'spread' in task.keys():
						if task['spread']==True:
							remote="Client task"
					else:
						task['spread']=False
					self.scheduled_tasks[task_name]=tasks[task_name]
					sw_tasks=True
					parsed_calendar=''
					parsed_calendar=parser.parse_taskData(task)
					task['cmd']=task['cmd'].replace(self.ldm_helper+' ','')
					task['action']=self.scheduler.get_task_description(task['cmd'])
					if 'name' in task.keys():
						name=task['name']
					else:
						name=_(task['action'])
					self.i18n['cmd'].update({name:task['action']})
					self.i18n['name'].update({_(task_name):task_name})
					img=self.edit_icon
					if 'protected' in task.keys():
						if task['protected']==True:
							img=self.no_edit_icon
					row=self.tasks_store.append(("<span font='Roboto'><b>"+name+"</b></span>\n"+\
								"<span font='Roboto' size='small'><i>"+\
								_(task_name)+"</i></span>",serial,"<span font='Roboto' size='small'>"+\
								parsed_calendar+"</span>\n"+"<span font='Roboto' size='small'><i>"+remote+"</i></span>",img,self.remove_icon,str(task['spread']),','.join(task['kind']),bg_color,fg_color))
	#def populate_tasks_tv
	
	def filter_tasklist(self,model,iterr,data):
		sw_match=True
		match=self.txt_search.get_text().lower()
		task_data=model.get_value(iterr,0).split('\n')
		task_sched_data=model.get_value(iterr,2).split('\n')
		task_cmd=task_data[0][task_data[0].find("<b>")+3:task_data[0].find("</b>")]
		task_name=task_data[1][task_data[1].find("<i>")+3:task_data[1].find("</i>")]
		task_sched=task_sched_data[0][task_sched_data[0].find("ll'>")+4:task_sched_data[0].find("</span>")]

		task_text=task_cmd+' '+task_name+' '+task_sched
		if match and match not in task_text.lower():
			sw_match=False
		return sw_match
	#def filter_tasklist

	def match_tasks(self,widget):
		self.tasks_store_filter.refilter()
		GObject.timeout_add(100,self.tasks_tv.set_cursor,0)
	#def match_tasks

	def _process_model(self,model,data):
		task={}
		task['data']=model[data][0].split('\n')
		if _("client task") in model[data][2]:
			task['spread']=True
		else:
			task['spread']=False
		task['serial']=model[data][1].split('\n')[0]
		cmd=task['data'][0][task['data'][0].find("<b>")+3:task['data'][0].find("</b>")]
		if cmd in self.i18n['cmd'].keys():
			task['cmd']=self.i18n['cmd'][cmd]
		else:
			task['cmd']=cmd

		name=task['data'][1][task['data'][1].find("<i>")+3:task['data'][1].find("</i>")]
		if name in self.i18n['name'].keys():
			task['name']=self.i18n['name'][name]
		else:
			task['name']=name

		task['serial']=model[data][1]
		return(task)

	def _click_on_list(self,event):
		action=''
		row=None

		if type(event)==type(Gtk.TreePath()):
			action='edit'
		else:
			try:
				row=self.tasks_tv.get_path_at_pos(int(event.x),int(event.y))
			except Exception as e:
				self._debug(e)
			if row:
				if row[1]==self.col_remove:
					action='remove'
				elif row[1]==self.col_edit:
					action='edit'
		self._debug(action)
		return action

	def task_clicked(self,treeview,event=None,*args):
		self._debug("task clicked %s"%event)
		selection=self.tasks_tv.get_selection()
		model,data=selection.get_selected()
		if not data:
			return
		task={}
		action=''
		if event!=None:
			action=self._click_on_list(event)
		task=self._process_model(model,data)
		if action=='remove':
			self.lbl_question.set_text(_("Are you sure to delete this task?"))
			for widget in self.main_box.get_children():
				widget.set_sensitive(False)
			self.inf_question.set_sensitive(True)
			self.inf_question.show_all()
			try:
				self.inf_question.disconnect_by_func(self.manage_remove_responses)
			except:
				pass
			self.inf_question.connect('response',self.manage_remove_responses,model,task)
		elif action=='edit':
			if task['name'] in self.scheduled_tasks.keys():
				if task['serial'] in self.scheduled_tasks[task['name']].keys():
					task['data']=self.scheduled_tasks[task['name']][task['serial']]
					self._debug("Loading details of task %s of group %s"% (task['serial'],task['name']))
					self.add_task_grid.set_task_data(task)
					self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
					self.cmb_task_names.remove_all()
					self.cmb_task_cmds.remove_all()
					self.cmb_task_names.append_text(_(task['name']))
					cmd=task['cmd']
					if 'protected' in task['data'].keys():
						if task['data']['protected']:
							self.btn_confirm_add.set_sensitive(False)
							cmd='...'
						else:
							self.btn_confirm_add.set_sensitive(True)
					else:
						self.btn_confirm_add.set_sensitive(True)
					self.cmb_task_cmds.append_text(_(cmd))
					self.cmb_task_names.set_active(0)
					self.cmb_task_cmds.set_active(0)
					self.add_task_grid.load_task_details()
					self.stack.set_visible_child_name("add")
	#def task_clicked			

	def save_task_details(self,widget):
		task={}
		name=self.cmb_task_names.get_active_text()
		task['name']=self.i18n['name'][name]
		action=self.cmb_task_cmds.get_active_text()
		i18n_action=self.i18n['cmd'][action]
		tasks=self.scheduler.get_available_tasks()
		task['cmd']=tasks[task['name']][i18n_action]
		self.add_task_grid.update_task_data(task)
		task=self.add_task_grid.get_task_details()

		self._debug("Writing task info...%s"%task)
		for key in task.keys():
			for data in task[key].keys():
				if task[key][data]['spread']==False:
					status=self.scheduler.write_tasks(task,'local')
				else:
					status=self.scheduler.write_tasks(task,'remote')
			break
		if status:
			self._show_info(_("Task saved"))
		else:
			self._show_info(_("Permission denied"))
		return()
	#def save_task_details

	def view_tasks_clicked(self,widget,sw_remote):
		if widget:
			if not widget.get_active():
				return True
		self._debug("loading tasks (remote: %s)" % sw_remote)
		if sw_remote:
			self.last_task_type='remote'
		else:
			self.last_task_type='local'
		self._debug("Task clicked")
		self.populate_tasks_tv()
		self.tasks_tv.set_model(self.tasks_store_filter)
		self.tasks_tv.set_cursor(0)
		if self.stack.get_visible_child_name!='tasks':
			self.stack.set_visible_child_name("tasks")
	#def view_tasks_clicked	

	def load_add_task_details(self):
		tasks=[]
		names=[]
		self.cmb_task_names.remove_all()
		tasks=self.scheduler.get_available_tasks()
		for name in tasks.keys():
			if name not in names:
				names.append(name)
				self.i18n['name'].update({_(name):name})
				self.cmb_task_names.append_text(_(name))
		
		self.cmb_task_names.connect('changed',self.load_add_task_details_cmds,tasks)
		self.cmb_task_names.set_active(0)
	#def load_add_task_details

	def load_add_task_details_cmds(self,widget,tasks):
		actions=[]
		self.i18n['cmd']={}
		self.cmb_task_cmds.remove_all()
		task_name=self.cmb_task_names.get_active_text()
		if task_name:
			orig_name=self.i18n['name'][task_name]
			for action in tasks[orig_name].keys():
				if action not in actions:
					self.i18n['cmd'].update({_(action):action})
					actions.append(action)
					self.cmb_task_cmds.append_text(_(action))
		self.cmb_task_cmds.set_active(0)
	#def load_add_task_details_cmds
	
	def update_task(self,widget,data=None):
		self._debug("Updating task")
		if self.task_details_grid.update_task_details():
			self._show_info(_('Task updated'))
			self._reload_grid()
		else:
			self._show_info(_('Permission denied'))
		
	#def update_task

	def add_task_clicked(self,widget,event):
		self._debug("Loading new task form")
		self.add_task_grid.clear_screen()
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_visible_child_name("add")
		self.load_add_task_details()
	#def add_task_clicked	

	def cancel_add_clicked(self,widget,event=None):
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("tasks")	
		self._debug("Cancel add clicked")
		self._reload_grid()
	#def cancel_add_clicked

	def _reload_grid(self,widget=None,data=None):
		cursor=self.tasks_tv.get_cursor()[0]
		self._debug("CURSOR %s"%widget)
		self._debug("Reload grid")
		self.populate_tasks_tv()
		if cursor:
			self._debug("Restoring cursor")
			self.tasks_tv.set_cursor(cursor)

		if type(widget)==type(Gtk.CheckButton()):
			self.task_details_grid.chk_node.connect("toggled",self._reload_grid)
	#def _reload_grid

	def manage_remove_responses(self,widget,response,model,task):
		self.inf_question.hide()
		if response==Gtk.ResponseType.OK:
			self._debug("Removing task %s"%(task))
			if task['name'] in self.i18n['name'].keys():
				task['name']=self.i18n['name'][task['name']]
			if task['cmd'] in self.i18n['cmd'].keys():
				task['cmd']=self.i18n['cmd'][task['cmd']]
			if self.scheduler.remove_task(task):
				self.populate_tasks_tv()
				self.tasks_tv.set_cursor(0)
			else:
				self._show_info(_("Permission denied"))
		for widget in self.main_box.get_children():
			widget.set_sensitive(True)
	#def manage_remove_responses

	def _show_info(self,msg):
		self.lbl_message.set_text(_(msg))
		self.inf_message.show_all()
		GObject.timeout_add(5000,self.inf_message.hide)
	#def _show_info
	
	def _manage_tasks(self,widget,event):
		self._debug("Loading manage tasks form")
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("manage")
	#def _manage_tasks	

	def _cancel_manage_clicked(self,widget):
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_visible_child_name("tasks")	
	
	def set_css_info(self):
	
		css = b"""
		#WHITE_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#ffffff),  to (#ffffff));;
		
		}

		#BLUE_FONT {
			color: #3366cc;
			font: Roboto Bold 11;
			
		}	
		

		#TASKGRID_FONT {
			color: #3366cc;
			font: Roboto 11;
			
		}

		#LABEL_OPTION{
		
			color: #808080;
			font: Roboto 11;
		}

		#ERROR_FONT {
			color: #CC0000;
			font: Roboto Bold 11; 
		}
		"""
		self.style_provider=Gtk.CssProvider()
		self.style_provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
		self.window.set_name("WHITE_BACKGROUND")
		self.tasks_box.set_name("WHITE_BACKGROUND")
	#def set_css_info	

	def quit(self,*args):
		Gtk.main_quit()	
	#def quit	

#class TaskScheduler

GObject.threads_init()
t=TaskScheduler()
t.start_gui()		
