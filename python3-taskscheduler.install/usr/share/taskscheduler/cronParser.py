#!/usr/bin/env python3
import gettext
gettext.textdomain('taskscheduler')
_ = gettext.gettext

class cronParser():
	def __init__(self):
			self.expr={'of':_('of'),'each':_('each'),'at':_('at'),'on':_('on'),'from':_('from'),\
					'to':_('to'),'and':_('and'),'the':_('the'),'in':_('in'),\
					'atm':_("at minute"),'min':_("minutes"),'emin':_('each minute'),'tmin':_('the minute'),\
					'ehour':_("each hour"),'h':_("hours"),'hoc':_("o'clock"),'evhour':_('every hour'),\
					'evday':_('everyday'),'lmd':_("last day"),'eday':_("each day"),'days':_('days'),\
					'day':_('day'),'evmon':_('every month'),'emon':_("each month"),'months':_('months'),\
					'evweek':_("every week"),'weeks':_("weeks"),'eweek':_("weekly")}
			self.dbg=0

	def _debug(self,msg):
		if self.dbg:
			print("cronParser: %s"%msg)
	###
	#Input: dict
	###
	def parse_taskData(self,taskData):
		self._debug ("parsing: "+str(taskData))
		parsed_data=[]
		parsed_calendar=''
		expr={}
#		day_dict={'1':_('Monday'),'2':_('Tuesday'),'3':_('Wednesday'),'4':_('Thursday'),'5':_('Friday'),\
#				'6':_('Saturday'),'7':_('Sunday'),'*':'every'}
		day_dict={'1':_('Mon'),'2':_('Tue'),'3':_('Wed'),'4':_('Thu'),'5':_('Fri'),\
				'6':_('Sat'),'7':_('Sun'),'*':'every'}
#		mon_dict={'1':_('January'),'2':_('February'),'3':_('March'),'4':_('April'),'5':_('May'),\
#				'6':_('June'),'7':_('July'),'8':_('August'),'9':_('September'),'10':_('October'),\
#				'11':_('November'),'12':_('December'),'*':'every'}
		mon_dict={'1':_('Jan'),'2':_('Feb'),'3':_('Mar'),'4':_('Apr'),'5':_('May'),\
				'6':_('Jun'),'7':_('Jul'),'8':_('Aug'),'9':_('Sep'),'10':_('Oct'),\
				'11':_('Nov'),'12':_('Dec'),'*':'every'}
		mon_expr=self._parse_cron_expression(taskData['mon'],mon_dict)
		dow_expr=self._parse_cron_expression(taskData['dow'],day_dict)
		if 'lmd' in taskData.keys():
			dom_expr=self.expr['lmd']
		else:
			dom_expr=self._parse_cron_expression(taskData['dom'])
		min_expr=self._parse_cron_expression(taskData['m'])
		hou_expr=self._parse_cron_expression(taskData['h'])
		time_expr=self._parse_time_expr(hou_expr,min_expr)
		date_expr=self._parse_date_expr(mon_expr,dow_expr,dom_expr)
		parsed_data=" ".join([time_expr,date_expr])
		if parsed_data[0].isdigit():	
			parsed_calendar=self.expr['at'] +' ' + parsed_data
		else:
			parsed_calendar=parsed_data
		return parsed_calendar.capitalize()
	#def parse_taskData(self,taskData):

	def _parse_time_expr(self,hour,minute):
		sw_err=False
		try:
			int(hour)
			int(minute)
		except:
			sw_err=True
		if not sw_err:
			time_expr=hour+':'+minute
		else:
			if minute!='every':
				if hour.startswith(self.expr['each']):
					minute=self.expr['atm']+' '+minute
				else:
					if hour!='every':
						minute=minute+' '+self.expr['min']
			else:
				minute=self.expr['emin']
			if hour!='every':
				if hour.startswith(_('each')):
					if hour.endswith(' 1 '):
						hour=self.expr['ehour']
					else:
						hour=hour+' '+self.expr['h']
				else:
					hour="%s %s"%(hour,self.expr['hoc'])
				time_expr="%s %s" % (hour,minute)
			else:
				if minute.startswith(_('each')):
					time_expr="%s %s" %(minute,self.expr['min'])
				else:
					hour="%s"%(self.expr['evhour'])
					time_expr="%s %s %s %s" % (hour,self.expr['on'],self.expr['tmin'],minute)
		return time_expr
	#def parse_time_expr

	def _parse_date_expr(self,mon,dow,dom):
		sw_dom_err=False
		sw_mon_err=False
		time_expr=''
		try:
			int(dom)
		except:
			sw_dom_err=True
		try:
			int(mon)
		except:
			sw_mon_err=True
		time_expr="%s %s" % (dom,mon)
		if sw_dom_err:
			if dom=='every' or dom=='*':
				dom=self.expr['evday']
			elif dom==self.expr['lmd']:
				pass
			elif 'every' in mon or mon=='*':
				if dom.startswith(self.expr['each']):
					if dom.endswith(' 1 '):
						dom=self.expr['eday']
					else:
						self._debug(dom)
						interval=int(dom.rstrip(' ').split(' ')[-1])
						if interval%7:
							dom="%s %s" % (dom,self.expr['days'])
						else:
							weeks=int(dom.rstrip(' ').split(' ')[-1])/7
							if weeks==1:
								dom=self.expr['eweek']
							else:
								dom="%s %s %s" % (self.expr['each'],int(weeks),self.expr['weeks'])
				else:
					dom="%s %s" % (self.expr['day'],dom)
			elif ',' in dom:
				dom="%s %s" % (self.expr['days'],dom)
			elif 'from' in dom:
				dom="%s %s" % (self.expr['days'],dom)
			elif dom.startswith(self.expr['each']):
					if dom.endswith(' 1 '):
						dom=self.expr['eday']
					else:
						dom="%s %s" % (dom,self.expr['days'])
		else:
#			dom="%s %s %s" % (self.expr['on'],self.expr['day'],dom)
			dom="%s %s %s" % (self.expr['of'],self.expr['day'],dom)

		if sw_mon_err:
			if mon=='every' or mon =='*':
				if dow!='*' and dow!='every':
#					mon=self.expr['evweek']
					mon=''
				else:
					mon=self.expr['evmon']
			elif mon.startswith(self.expr['each']):
				if mon.endswith(' 1 '):
					mon=self.expr['emon']
				else:
					mon="%s %s" % (mon,self.expr['months'])
		else:
			mon="%s %s" % (self,expr['mon'],mon)

		if dow!='every' and dow!='*':	
			if mon==self.expr['emon'] or mon.startswith(self.expr['each']):
				time_expr="%s %s %s %s %s" % (self.expr['the'],dow,self.expr['in'],self.expr['evweek'],mon)
			else:
				if mon!=self.expr['emon'] and mon!=self.expr['evmon'] and mon!='':
					time_expr="%s %s %s %s" % (self.expr['the'],dow,self.expr['in'],mon)
				else:
					time_expr="%s %s" % (self.expr['the'],dow)
		else:
			if dom==self.expr['eday'] and mon==self.expr['emon']:
				time_expr="%s" % (self.expr['evday'])
			else:
				if dom.startswith(self.expr['each']):
					if mon!='*' and mon!=self.expr['evmon']:
						time_expr="%s %s %s" % (dom,self.expr['in'],mon)
					else:
						time_expr="%s" % (dom)
				else:
					if mon!=self.expr['evmon'] or (dom!=self.expr['evday'] and dom!=self.expr['eweek']):
						if dom==self.expr['evday']:
							dom=self.expr['eday']
						time_expr="%s %s %s" % (dom,self.expr['in'],mon)
					else:
						time_expr="%s" % (dom)
#				time_expr="%s %s %s" % (self.expr['on'],dom,mon)
#				time_expr="%s %s %s" % (dom,self.expr['of'],mon)
#				if dom==self.expr['evday']:
#					time_expr="%s" % (dom)


		return time_expr
	#def parse_date_expr

	def _parse_cron_expression(self,data,description_dict={}):
		(each,at_values,range_values,extra_range,values)=('','','','','')
#	*/2 -> Each two time units
#	1-2 -> Range between 1 and 2
#	1,2 -> At 1 and 2
#	1 -> direct value
		if data in description_dict.keys():
			values=description_dict[data]
		else:
			if '/' in data:
				expr=data.split('/')
				each=expr[-1]
				data=expr[0]
			if ',' in data:
				at_values=data.split(',')
				value_desc=[]
				for value in at_values:
					if '-' in value:
						extra_range=value
					else:
						if value in description_dict.keys():
							value_desc.append(description_dict[value])
				at_values=value_desc
			if '-' in data or extra_range:
				if extra_range:
					data=extra_range
				range_values=data.split('-')
				value_desc=[]
				for value in range_values:
					if value in description_dict.keys():
						value_desc.append(description_dict[value])
				if value_desc:
					range_values=value_desc
		(str_range,str_each,str_at)=('','','')
		if range_values:
			str_range="%s %s %s %s " % (self.expr['from'],range_values[0],self.expr['to'],range_values[1])
		if each:
			str_each="%s %s " % (self.expr['each'],each)
		if at_values:
			if range_values:
				str_at="%s %s %s %s" % (self.expr['and'],', '.join(at_values[:-1]),self.expr['and'],at_values[-1])
			else:
				str_at="%s %s %s" % (', '.join(at_values[:-1]),self.expr['and'],at_values[-1])

		retval=str_range+str_at+str_each+values
		if retval=='':
			if len(data)<2 and data!='*':
				data='0'+data
			elif data=='*':
				data='every'
			retval=data
		return (retval.rstrip('\n'))
	#def parse_cron_expression
