#!/usr/bin/env python3

#/**********************************************************************************
#*    Copyright (C) by Ran Novitsky Nof                                            *
#*                                                                                 *
#*    This file is part of ElViS                                                   *
#*                                                                                 *
#*    ElViS is free software: you can redistribute it and/or modify                *
#*    it under the terms of the GNU Lesser General Public License as published by  *
#*    the Free Software Foundation, either version 3 of the License, or            *
#*    (at your option) any later version.                                          *
#*                                                                                 *
#*    This program is distributed in the hope that it will be useful,              *
#*    but WITHOUT ANY WARRANTY; without even the implied warranty of               *
#*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                *
#*    GNU Lesser General Public License for more details.                          *
#*                                                                                 *
#*    You should have received a copy of the GNU Lesser General Public License     *
#*    along with this program.  If not, see <http://www.gnu.org/licenses/>.        *
#***********************************************************************************/

# By Ran Novitsky Nof @ BSL, 2014
# ran.nof@gmail.com
# Update for Python3 and QT5 by R.N.N @ GSI, 2019

import matplotlib as mpl
import datetime
mpl.use('QT5Agg')
#from pylab import Line2D
import numpy as np
import sys,os
from matplotlib.backend_bases import NavigationToolbar2, Event
from matplotlib.backends.backend_qt4agg import(
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib import cm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# command line parser
import argparse
# utils for ActiveMQ
import amq2py as AMQ
# util class for Open Street Map
from osm import OSM as osm
# UI modules
from UIModules import zoomForm,messagesWidget,alertPanel,homeDialog,eventDialog
import alertmodule as ALRT

# defaults - can be set similarly in a configuration file given as a commandline parameter
FONTSIZE='8'
GMPEAKtopic='/topic/eew.alg.elarms.gmpeak.data' # peak parameters AMQ topic
TRIGGERtopic='/topic/eew.alg.elarms.trigger.data' # trigger and trigger parameters AMQ topic
ALARMStopic='/topic/eew.alg.elarms.data' # E2 alarms AMQ topic
DMtopic='/topic/eew.sys.dm.data' # DM event AMQ topic
EDATAtopic='/topic/eew.alg.elarms.event.data' # event raw data topic
STATIONS_FILE = '/home/sysop/EEWS/run/bin/stations.cfg' # file with stations ([net] [sta] [lat] [lon])
HomeLat=31.7722064 # latitude of "home" location
HomeLon=35.1958522 # longitude of "home" location
HomeSize=6 # size of "home" marker
HomeLabel='Home' # name of "Home"
HomeColor='red' # color of "home" marker
HomeMarker='s' # style of "home" marker
OSMTILEURL="http://a.tile.openstreetmap.org" # where to read map tiles from
OSMTILEARCHIVE="tiles"
OSMTILEPAT = "{Z}/{X}/{Y}.png"
# AMQ defaults
AMQUSER='monitor' # user for monitoring
AMQPASSWD='monitor' # password for monitoring
AMQDMUSER='decimod' # user of decision module
AMQDMPASSWD='decimod' # password for decision module
AMQHOST='localhost' # AMQ host
AMQPORT=61613 # AMQ port
watchingGMValue='amax' # station values to monitor
GRIDON=False # grid on or off [True | False]
VERBOSE=False # printout message

# general setup
topics = {'gmpeak':GMPEAKtopic, # peak parameters AMQ topic
          'trigger':TRIGGERtopic, # trigger and trigger parameters AMQ topic
          'alarms':ALARMStopic, # E2 alarms AMQ topic
          'dm':DMtopic, # DM event AMQ topic
          'waveforms' : EDATAtopic} # Event waveforms raw data topic
acmap = mpl.colors.LinearSegmentedColormap.from_list('acc',['blue','cyan','yellow','red']) # create a colormap for accelertion
acmap(np.arange(256)) # initialize the colormap
cm.register_cmap(cmap=acmap)
cm.acc = acmap
watchValsDict = {'Acceleration':'amax',
                 'Velocity':'vmax',
                 'Displacement':'dmax'
                }


# command line parser
parser = argparse.ArgumentParser(
         formatter_class=argparse.RawDescriptionHelpFormatter,
         description='''ElarmS Visualization System (ElViS)''',
         epilog='''Created by Ran Novitsky Nof @ BSL
(ran.nof@gmail.com)''')
parser.add_argument('cfgfile',nargs='?',default=None,help='Configuration file.',type=argparse.FileType('r'))
parser.add_argument('--replay',default=False,action='store_true', help='Replay mode')
##################### Some matplotlib Black Magic ##########################################################
## This part will redirect some matplotlib toolbar and canvas callbacks
## adjusting navigation bar for capturing after zoom/pan events

# reference to original matplotlib toolbar functions
canvasHome = NavigationToolbar2.home
canvasBack = NavigationToolbar2.back
canvasForward = NavigationToolbar2.forward
canvasRelease_pan = NavigationToolbar2.release_pan
canvasRelease_zoom = NavigationToolbar2.release_zoom

# new toolbar functions with a callback signal (defined by a)
# each function will call the original toolbar function and emite a callback
# signals can be redirected to a new function at a later stage using mpl_connect.
def new_home(self, *args, **kwargs):
  a = 'after_home_event' # this is the signal called after processing the event
  event = Event(a, self)
  canvasHome(self, *args, **kwargs) # call original matplotlib toolbar function
  self.canvas.callbacks.process(a, event) # process the signal
def new_back(self, *args, **kwargs):
  a = 'after_back_event'
  event = Event(a, self)
  canvasBack(self, *args, **kwargs)
  self.canvas.callbacks.process(a, event)
def new_forward(self, *args, **kwargs):
  a = 'after_forward_event'
  event = Event(a, self)
  canvasForward(self, *args, **kwargs)
  self.canvas.callbacks.process(a, event)
def new_release_pan(self, evt):
  a = 'after_release_pan_event'
  event = Event(a, self)
  canvasRelease_pan(self,evt)
  self.canvas.callbacks.process(a, event)
def new_release_zoom(self, evt):
  a = 'after_release_zoom_event'
  event = Event(a, self)
  canvasRelease_zoom(self,evt)
  self.canvas.callbacks.process(a, event)
# change toolbar functions to the new functions
NavigationToolbar2.home = new_home
NavigationToolbar2.back = new_back
NavigationToolbar2.forward = new_forward
NavigationToolbar2.release_pan = new_release_pan
NavigationToolbar2.release_zoom = new_release_zoom
######################### End of matplotlib black magic ########################################

# QT Form Apllication - the main application.
class AppForm(QMainWindow):
  'QT form for application'
  #  Signals
  drawSignal = pyqtSignal(int)  # redraw map
  chkconnsignal = pyqtSignal()  # check AMQ connection
  togconnstatsignal = pyqtSignal()  # toggle AMQ connection Icon
  addPanelSignal = pyqtSignal(str,object)  # add EQ alert info panel
  updatePanelSignal = pyqtSignal(object,object,object)  # update EQ alert panel
  # messages signals
  sysMsgSignal = pyqtSignal(str, int)  # add system message
  trigMsgSignal = pyqtSignal(str,str)  # add trigger message
  evntMsgSignal = pyqtSignal(str,int)  # add event message
  errMsgSignal = pyqtSignal(str,int)  # add error message



  def __init__(self, splash,args,parent=None):
    splash.showMessage('Initializing...',Qt.AlignCenter)
    QApplication.processEvents()
    QMainWindow.__init__(self, parent)
    ALRT.cutil.initgeod() # init the geoid from ALRT.cutil for later use.
    self.args = args # save command line arguments
    # Icons
    icon ='network-receive'
    self.connectedIcon1 = QIcon.fromTheme(icon,QIcon(":/%s.png" % icon)).pixmap(16,16)
    icon ='network-transmit'
    self.connectedIcon2 = QIcon.fromTheme(icon,QIcon(":/%s.png" % icon)).pixmap(16,16)
    self.connectedIcon = self.connectedIcon1
    icon = 'network-offline'
    self.disconnectedIcon = QIcon.fromTheme(icon,QIcon(":/%s.png" % icon)).pixmap(16,16)
    # some status initialization
    self._resizing=False # are we in a window resize phase
    self._drawing=False # are we in a canvas drawing phase?
    self._watchingGMValue = watchingGMValue
    # init tools and widgets
    self.meter = mpl.lines.Line2D([],[],color='r') # line for measuring distances along canvas
    self.topics = {} # AMQ topics we are connected to
    self.setWindowTitle('ElViS - Elarms Visualization System') # window title
    splash.showMessage('Creating application...',Qt.AlignCenter)
    QApplication.processEvents()
    self.create_menu() # create the app top menu
    self.create_status_bar() # add a status bar
    self.create_main_frame() # create the main frame.
    self.alertPanel = alertPanel(self) # prepare an alert panel.
    self.create_message_widget() # Add messages widget.
    self.create_tooltip_widget()
    self.osm = osm(self.ax,OSMTILEURL,OSMTILEPAT,OSMTILEARCHIVE) # add open street map generator
    splash.showMessage('Loading stations...',Qt.AlignCenter)
    QApplication.processEvents()
    self.replay = args.replay # replay mode indicator
    self.timeshift = 0 # time shift will be determined by the first gm param packet
    self.stations = []
    self.load_stations(STATIONS_FILE) # load stations
    self.set_home(lat=HomeLat,lon=HomeLon,label=HomeLabel,markersize=HomeSize,color=HomeColor,marker=HomeMarker) # set "home" location
    self.homeDialog = homeDialog(self.home._y[0],self.home._x[0],Label=HomeLabel,Markersize=HomeSize,Color=HomeColor,Marker=HomeMarker) # init and update home dialog
    self.eventDialog = eventDialog() # init an event dialog
    self.zoomform = zoomForm()
    self.trigedlist = {} # A dictionary of triggered stations. will hold mpl lines
    self.activeStationsList = {} # A dictionary of currently active stations. mpl lines
    self.eventsList = {} # A dictionary of all events. holds event messages and parameters inc. updates
    self.activeWarnings = {} # A dictionary of all current warnings running. mpl lines
    self.lastEvent = None # a reference to the latest event
    self.sysmsg.add('System Start.',True) # start system message
    # adjusting AMQListner message processing functions replacing original with self functions
    splash.showMessage('Connecting to ActiveMQ server...',Qt.AlignCenter)
    QApplication.processEvents()
    AMQ.AMQListener.processMessages = self.processAMQmsg # what to do with messages
    AMQ.AMQListener.on_connecting = self.on_connecting # what to do on connection
    AMQ.AMQListener.on_disconnected = self.on_disconnected # what to do on disconnection
    self.amq = AMQ.AMQListener(usr=AMQUSER,passwd=AMQPASSWD,host_and_ports=[(AMQHOST,AMQPORT)],name='ActiveMQ',ID=1,log=True,verbose=VERBOSE) # create AMQ listener
    self.connectToAMQ() # connect listener to server
    self.subscribeToAMQ(topics) # subscribe listener to topics
    self.start_timers() # start QT Timers to process triggers, station values (colors) and EQ warnings.
    self.init_connections() # connect signals and functions
    self.acmap = cm.acc # set colormap for accelerations
    self.chkconn() # check connection and update icons
    splash.showMessage('Starting...',Qt.AlignCenter)
    QApplication.processEvents()

  def start_timers(self):
    ' Start QT timers for periodic processing of triggers, station values and alerts'
    self.trigertimer = QTimer(self) # Triggers Timer
    self.trigertimer.timeout.connect(self.processtrigs) # will run processtrigs
    self.trigertimer.start(1000) # every second.
    self.ActiveSationsTimer = QTimer(self) # Stations activity Timer
    self.ActiveSationsTimer.timeout.connect(self.processactivestations) # will run processactivestations
    self.ActiveSationsTimer.start(1000) # every second
    self.ActiveWarningsTimer = QTimer(self) # EQ warnings Timer
    self.ActiveWarningsTimer.timeout.connect(self.processwarnings) # will run processwarnings
    self.ActiveWarningsTimer.start(300) # every 300 milliseconds

  def init_connections(self):
    """Connect signals to functions.
       Using signals to run functions from subprocesses.
    """
    self.chkconnsignal.connect(self.chkconn)  # check AMQ connection
    self.togconnstatsignal.connect(self.togconnstat)  # toggle AMQ connection Icon
    self.addPanelSignal.connect(self.alertPanel.addPanel)  # add EQ alert info panel
    self.updatePanelSignal.connect(self.alertPanel.updatePanel)  # update EQ alert panel
    self.drawSignal.connect(self.draw)  # draw canvas
    # connect widget ok buttons to functions
    self.homeDialog.accepted.connect(self.onSetHomeLocationAccepted) # connect home settings dialog ok button
    self.eventDialog.accepted.connect(self.onNewEventAccepted) # connect event settings dialog ok button
    self.zoomform.accepted.connect(self.onZoomToAccepted) # connect zoom to dialog ok button
    # connecting mpl events
    self.canvas.mpl_connect('scroll_event',self.scroll_event) # connect canvas scroll event
    self.canvas.mpl_connect('after_home_event',self.handle_home) # connect home button on toolbar
    self.canvas.mpl_connect('after_back_event', self.handle_home) # connect back button on toolbar
    self.canvas.mpl_connect('after_forward_event',self.handle_home) # connect forward button on toolbar
    self.canvas.mpl_connect('after_release_pan_event',self.handle_home) # connect pan button on toolbar
    self.canvas.mpl_connect('after_release_zoom_event',self.handle_home) # connect zoom button on toolbar
    self.canvas.mpl_connect('motion_notify_event',self.on_move) # connect mouse motion on canvas
    self.canvas.mpl_connect('button_press_event',self.on_click) # connect click on canvas
    self.canvas.mpl_connect('button_release_event',self.on_unclick) # connect mouse button release on canvas
    self.canvas.mpl_connect('resize_event',self.resizeEvent) # connect resize event
    # connect messages signals
    self.sysMsgSignal.connect(self.sysmsg.add)  # add system message
    self.trigMsgSignal.connect(self.trigmsg.add)  # add trigger message
    self.evntMsgSignal.connect(self.evntmsg.add)  # add event message
    self.errMsgSignal.connect(self.errmsg.add)  # add error message

  def draw(self,idle=True):
    'Draw the figure on canvas.'
    self._drawing = True # entering a drawing mode
    if idle:
      self.canvas.draw_idle() # draw idle (see matplotlib for details)
    else:
      self.canvas.draw() # draw anyways.
    self._drawing = False # leaving drawing mode

  def grid(self):
    'toggle grid on or off'
    self.ax.grid()
    self.draw()

  ########## AMQ related functions ###########
  def on_connecting(self,host_and_port):
    'runs automatically when AMQ server is connected'
    host,port=host_and_port
    m = 'Connected to ActivMQ server @ '+':'.join([host,str(port)])
    self.sysMsgSignal.emit(m,True) # send a system message
    self.chkconnsignal.emit() # verify connection (will also update icon and tooltip)

  def on_disconnected(self):
    'runs automatically when AMQ is disconnected'
    self.sysMsgSignal.emit('Disconnected from ActiveMQ server.',True) # send a system message
    self.chkconnsignal.emit() # verify connection (will also update icon and tooltip)

  def subscribeToAMQ(self,topics):
    'subscribe to topics on AMQ server.'
    for topic in topics:
      if self.amq.subscribeToActiveMQ(topics[topic],topic):
        self.sysmsg.add('Subscribed to '+topics[topic],True) # send system message
        self.topics[topic] = topics[topic] # save a list of topics
      else:
        self.sysmsg.add("Can't subscribed to "+topics[topic],True)

  def connectToAMQ(self):
    'connect listener to AMQ server'
    try:
      self.amq.connectToActiveMQ()
      self.chkconnsignal.emit()
    except TimeoutError:
      self.sysmsg.add("Can't connect to AMQ @ "+self.amq.host_and_ports,True)

  def disconnectAMQ(self):
    'Diconnect Listener from AMQ server'
    for topic in topics:
      if self.amq.unsubscribeToActiveMQ(topic):
        self.topics[topic] = None # remove topics from list
    self.amq.conn.disconnect()

  def reconnectToAMQ(self):
    'reconnect to AMQ server'
    try:
        self.disconnectAMQ()
    except Exception as msg:
        self.errmsg.add(str(msg),True)
    self.connectToAMQ() # connect
    self.subscribeToAMQ(topics) # subscribe
#    self.chkconnsignal.emit()

  def connectToNewAMQ(self):
    '''connect to a new AMQ.
    connectToNewAMQ is not active yet.
    Should have a dialog with user, password, host, port etc.
    ok will change the default values of AMQ connection,
    remove and current connection
    and create a new listener with a new connection.'''
    self.message(self.connectToNewAMQ.__doc__,'To Do List')

  def statusAMQ(self):
    'Display info on AMQ connection'
    maxmessages = self.amq.maxmessages # messages buffer size
    usr = self.amq.usr # user
    passwd = self.amq.passwd # password
    name = self.amq.name # listener name
    host,port = self.amq.conn.transport.current_host_and_port or self.amq.host_and_ports[0] # host and port used
    nmessages = len(self.amq.MESSAGES) # number of current messages
    isconn = lambda x: "connected" if x else "not connected" # lambda expression for connection status
    connected = isconn(self.amq.conn.is_connected()) # connection status
    topics = self.amq.SUBSCRIBES # subsciption list
    msg = 'AMQ Listner "%s" is %s to %s:%s@%s:%d\nMessages: %d (max: %d)\nTopics:\n  %s' \
          %(name,connected,usr,passwd,host,port,nmessages,maxmessages,'\n  '.join([': '.join([k,v]) for k,v in topics.items()]))
    self.message(msg, 'ElViS - AMQ Connection Status')

  def connstat(self,connected,details):
    'update AMQ connection status'
    if not connected:
      self.connstatLabel.setPixmap(self.disconnectedIcon)
    else:
      self.connstatLabel.setPixmap(self.connectedIcon)
    self.connstatLabel.setToolTip(details)

  def togconnstat(self):
    'toggle AMQ connection icon so it looks like a live connection. will run each time a message arrives from server'
    if self.connectedIcon==self.connectedIcon1:
      self.connectedIcon=self.connectedIcon2
    else:
      self.connectedIcon=self.connectedIcon1
    self.connstatLabel.setPixmap(self.connectedIcon) # update icon

  def chkconn(self):
    'check current connection to AMQ server.'
    host,port=self.amq.host_and_ports[0]
    if self.amq.conn.transport.is_connected():
      self.connstat(True,'Connected to ActiveMQ server @ '+':'.join([host,str(port)]))
      self.status_text.setText('Monitoring.')
      return 1
    else:
      self.connstat(False,'No Connection to '+':'.join([host,str(port)]))
      self.status_text.setText('Not Monitoring.')
      return 0

  def processAMQmsg(self):
    'Runs automatically every time a message arrives from AMQ server'
    ts = datetime.datetime.utcnow() # get current time stamp
    self.togconnstatsignal.emit() # toggle AMQ connection icon
    l = self.amq # easier shortcut
    message = l._lastMessage # get last message
    if message.type=='T': # trigger message
      self.trigMsgSignal.emit(str(message),datetime.datetime.utcnow().strftime('[%T.%f] ')) # send a trigger message
      stationID = AMQ.ID(message.packets)[0][:-7] # get station ID
      station = [i for i in self.stations if stationID in i.get_label()][0] # find first station in self.stations (matplotlib lines) with a label similar to stationID
      self.trigstation(station) # Mark station as triggered
      self.trigedlist[station]=ts # add time stamp to triggered station list
      self.drawSignal.emit(True) # redraw figure if idle
    if message.type=='G': # ground values
      stationIDs = AMQ.ID(message.packets) # get station IDs in message
      params = message.packets[self._watchingGMValue] # get parameter (dmax,vmax,amax for displacement,velocity or acceleration)
      stations = [i for i in self.stations if i.get_label().split()[0] in [s[:-7] for s in stationIDs]] # get mpl lines objects for stations
      if self.replay and not self.timeshift:  # if we are in a replay mode
        ptime = datetime.datetime.utcfromtimestamp(message.packets['ts'][0])  # get first packet time stamp
        self.timeshift = (datetime.datetime.utcnow() - ptime).total_seconds()  # determine timeshift
      for station in stations:
        self.activeStationsList[station]=ts # add a timestamp for station activity
        vals = [abs(v) for i,v in zip(stationIDs,params) if station.get_label().split()[0] in i] # get values for station from all channels (E,N,Z)
        val = max(vals) # get maximal value
        color = self.color(val) # get color by value
        station.set_markerfacecolor(color) # set station color
        station.set_zorder(10) # move station to front of visibility
        station.set_label(station.get_label().split()[0]+' (%s=%0.2e)'%(self._watchingGMValue,val)) # set station label with value
      self.drawSignal.emit(True) # redraw figure if idle
    if message.type=='X': # event message (X=xml)
      self.evntMsgSignal.emit(str(message),True) # send an event message
      self.processEvent(message) # process the event
  ########## AMQ related functions END ###########

  def processEvent(self,m):
    '''Process an event message from AMQ server.
     This will be called by AMQ event processor for each event message'''
    m.intensity = ALRT.get_intensity(self.home._y[0],self.home._x[0],m.lat, m.lon, m.mag, RS = 'R', IM = 'PGA', ZH = 'H', PS = 'S')[0] # calculate event intensity
    m.dist,m.azimuth = ALRT.cutil.geo_to_km(self.home._x[0],self.home._y[0],m.lon,m.lat) # calculate distance and azimuth from "home"
    lbl = str(m) # get label
    lbl = lbl.split(')') # split to two parts
    lbl = '\n'.join((lbl[0]+')').split('|')+(lbl[1]+')').split()) # rearrange in lines.
    m.point = mpl.lines.Line2D([m.lon],[m.lat],marker='o',ms=10,mew=3,mec=(1.0,0,0,1.0),mfc=(1.0,0,0,0.5),label=lbl) # create a point at location
    if m.azimuth<0: m.azimuth+=360.0 # correct for 0-360 azimuth range
    self.lastEvent = m # set last event variable
    if not m.Eid in self.eventsList: # if this is first time we see this event ID
      self.eventsList[m.Eid] = [m] # add to event list
    else:
      self.eventsList[m.Eid].append(m) # or append to solutions record of the event
    self.starteventwarning(m) # start a warning or update an active one
    # uncomment for a zoom to event
    #self.ax.set_ylim(m.lat-0.5,m.lat+0.5)
    #self.ax.set_xlim(m.lon-0.5,m.lon+0.5)
    # comment for a zoom to event
    self.drawSignal.emit(False)

  def clear_events(self):
    'Clear all events from memory and map except for the active events'
    for Eid in self.eventsList.keys(): # for every event
      if not Eid in self.activeWarnings: # if not active warning
        for m in self.eventsList[Eid]: # for every solution fount and displayed
          m.point.remove() # remove the point from map
        self.eventsList.pop(Eid) # remove event form event list
        if Eid in self.alertPanel.eq: self.alertPanel.eq[Eid].widget.parent().close() # remove panel if still visible
    self.drawSignal.emit(False)

  def starteventwarning(self,m):
    '''Add an event warning panel or update an existing one.
       also update event location on map.
       will be called by processEvent'''
    params = {'m':m,
                 'ot':m.orig_time,
                 'lat':m.lat,
                 'lon':m.lon,
                 'depth':m.depth,
                 'mag':m.mag,
                 'I': m.intensity,
                 'dist':m.dist,
                 'azimuth':m.azimuth,
                 'point':m.point
                 } # get parameters for panel
    if not m.Eid in self.activeWarnings: # if this is the first time we open a panel for the event
      params['S'] = mpl.lines.Line2D(np.ones(361)*m.lon,np.ones(361)*m.lat,c='red',label='S wave '+str(m)) # Create a line for S wave on map
      params['P'] = mpl.lines.Line2D(np.ones(361)*m.lon,np.ones(361)*m.lat,c='blue',label='P wave '+str(m))# Create a line for P wave on map
      self.ax.add_line(m.point) # add a point for event location on map
      self.ax.add_line(params['S']) # add a line for S wave on map
      self.ax.add_line(params['P']) # add a line for P wave on map
      self.activeWarnings[m.Eid] = params # update the current parameters of warning
      self.addPanelSignal.emit(m.Eid,params) # add a warning panel widget - see UIModules for panel class details
    else: # or if this is an update
      self.ax.add_line(m.point) # add a corrected location
      self.eventsList[m.Eid][-2].point.set_mfc('None') # change color of old location
      self.eventsList[m.Eid][-2].point.set_mec((1,0,0,0.75))
      self.eventsList[m.Eid][-2].point.set_mew(1)
      self.activeWarnings[m.Eid].update(params) # update the parameters of the event

  def processwarnings(self):
    '''Process active warnings. Called by a timer every 300 milliseconds.
    Will update S and P waves on map and on alert panel if it is still open.
    updating will be done for 180 seconds after origin time and than be removed form active events.
    '''
    if len(self.activeWarnings)==0: return # don't waste time if no active events are available.
    redraw = False # only update figure if needed
    for Eid,params in self.activeWarnings.items(): # for each active alert running get the parameters
      ot = params['ot'] # origin time
      lat0 = params['lat'] # latitude
      lon0 = params['lon'] # longitude
      depth0 = params['depth'] # depth
      S = params['S'] # S wave mpl line
      P = params['P'] # P wave mpl line
      now = datetime.datetime.utcnow() # get the current time
      dt =  (now-ot).total_seconds() # calculate time difference since origin time
      if dt>180: # if we are 3 minutes after the event
        self.ax.lines.remove(P) # remove the P wave line
        self.ax.lines.remove(S) # remove the S wave line
        self.activeWarnings.pop(Eid) # remove event from active warnings
        redraw = True # don't forget to update the map
        continue # go to next active warning
      S.set_data(ALRT.wavePoints(lon0,lat0,dt,ALRT.S_WAVE_VELOCITY)) # update S wave location
      P.set_data(ALRT.wavePoints(lon0,lat0,dt,ALRT.P_WAVE_VELOCITY)) # update P wave location
      redraw= True # don't forget to update the map
      # update ETA to "Home"
      eta = ALRT.eta_userDisplay(self.home._x[0],self.home._y[0],lon0, lat0, depth0,ot,now - datetime.timedelta(0,self.timeshift)) # calculate estimated time of arrival (ETA) of S waves to "home"
      if eta >= 0: # if we still expect the waves
        self.updatePanelSignal.emit(Eid,params,eta) # update the alert panel
      else:
        self.updatePanelSignal.emit(Eid,params,0) # or just put a zero if S wave has passed, hoping someone is still there to see it.
    if redraw: self.drawSignal.emit(False) # update the map with all changes

  def processactivestations(self):
    '''process active station. update non-active stations.
    will be called by a timer every 1 second.
    '''
    redraw = False # don't draw if no changes are needed
    ts = datetime.datetime.utcnow() # get the time
    for station in self.stations: # for every station
      if station in self.activeStationsList: # if station is listed as active (i.e. got a message from it)
        if (ts-self.activeStationsList[station]).total_seconds()>60: # if last message from station is over a minute ago
          redraw = True # don't forget to update at the end
          station.set_markerfacecolor('k') # turn station color to black (not active)
          self.errMsgSignal.emit('Station %s is inactive for the last 60 sec.' % station.get_label().split()[0],True) # send an error message
          self.activeStationsList.pop(station) # remove form active station list
    if redraw: self.drawSignal.emit(False) # update map if needed.

  def processtrigs(self):
    '''Process triggered stations.
       remove highlighting of triggered stations after 5 seconds
    '''
    redraw = False # don't update map if no changes are made
    for station in self.stations: # for each station
      if station in self.trigedlist: # if it was triggered during a trigger message
        if (datetime.datetime.utcnow()-self.trigedlist[station]).total_seconds()>5: # and it was over 5 seconds ago
          redraw = True # don't forget to update the map
          self.untrigstation(station) # un-trigger the station (i.e. remove highlighting)
          self.trigedlist.pop(station) # remove station from triggered station list
    if redraw: self.drawSignal.emit(False) # update map if needed

  def trigstation(self,station):
    '''mark station marker as triggered.
       called by AMQ message processor when a trigger message arrives'''
    station.set_zorder(999) # bring to front
    station.set_markersize(10) # enlarge marker size
    station.set_markeredgecolor('red') # highlight edge in red

  def untrigstation(self,station):
    '''un mark station marker as triggered.
    called by processtrigs (wich is called every 1 second)
    if trigger was over 5 seconds ago.
    '''
    station.set_markersize(6) # back to normal size
    station.set_markeredgecolor('black') # un-highlight edge


  def color(self,val):
    '''determin the color of a station by data value.
       Note that Elarms output is in cm.
    '''
    if self._watchingGMValue=="vmax": # velocity color scheme
      v = val*1000000.0
      if v>150000:
        color='maroon'
      if v<150000:
        color='red'
      if v<60000:
        color='darkorange'
      if v<30000:
        color='gold'
      if v<12000:
        color='yellow'
      if v<4000:
        color='green'
      if v<1500:
        color='cyan'
      if v<800:
        color='skyblue'
      if v<400:
        color='blue'
      return color
    elif self._watchingGMValue=="amax": # acceleration value
      return self.acmap(int(255*(abs(val)/98.1))) # normilized cm/s^2 to g percentage
    elif self._watchingGMValue=="dmax":
      return self.acmap(int(255*(np.log10(abs(val)/1e-9))/10.0)) # order of magnitude with respect to nanometer

  def resizeEvent(self,event):
    '''called by any resize event of the map'''
    if not self._resizing: # only run if we are not in a middle of a resizong process
      self._resizing=True # note that we are resizong
      self.redrawbgmap() # redraw the background map
      self._resizing=False # Done with resizing.

  def zoom(self,e):
    '''called by scroll_event to zoom in or out on map.'''
    ax = self.ax # easier
    x,y = e.xdata,e.ydata # get where to center to (mouse pointer)
    x0,x1 = ax.get_xlim() # get current x limits
    y0,y1 = ax.get_ylim() # get current y limits
    dx=(x1-x0)/2.0 # get distance from center to edge on x axis
    dy=(y1-y0)/2.0 # get distance from center to edge on y axis
    # zoom and center
    ax.set_xlim(x-dx*e.zoom,x+dx*e.zoom)
    ax.set_ylim(y-dy*e.zoom,y+dy*e.zoom)
    self.redrawbgmap() # redraw background map with new limits

  def scroll_event(self,e):
    '''called by a scroll event on map'''
    if e.button=='up': e.zoom = 0.9 # zoom in
    elif e.button=='down': e.zoom = 1.1 # zoom up
    self.zoom(e) # do the zoom

  def redrawbgmap(self):
    '''redraws the background map using open street map object (osm)
    see osm module for more details.
    '''
    self.statusBar().showMessage('hold, redrawing ...') # let user know to wait on drawing. it might take some time
    QApplication.processEvents() # make sure user see the message
    self.ax.images=[] # remove images from map
    self.ax.apply_aspect() # make sure xlim and ylim are updated to screen size. this is because we use equal aspect and datalim. see matplotlib details on axes set_aspect function
    x0,x1 = self.ax.get_xlim() # get requested limits of x axis
    y0,y1 = self.ax.get_ylim() # get requested limits of y axis
    self.osm.relimcorrected(x0,x1,y0,y1) # make sure limits are not out of map phisical boundaries. see osm module for more details.
    tiles = self.osm.gettiles(x0,x1,y0,y1) # get the needed tiles from buffer or url. see osm module for more details
    self.osm.plottiles(tiles) # plot the tiles. see osm module for more details
    self.drawSignal.emit(False) # call self draw using a signal in case we are in a subprocess.
    self.statusBar().showMessage('Done redrawing.',2000) # note user we are done with redrawing.
    QApplication.processEvents() # make sure user see the message

  def handle_home(self,evt):
    'handle mpl toolbar pan/zoom/back/forward/home buttons.'
    self.fixlimits() # fix axes limit to global geographic bounds
    self.redrawbgmap() # redraw the background map

  def on_move(self,evt):
    'handle mouse movements along map'
    if evt.inaxes and self.toolbar.mode=='': # make sure we are not in a toolbar mode of pan/zoom
      if evt.button==3: # check if we measure distance along the map (right button is clicked)
        self.meter.set_data([self.meter._xorig[0],evt.xdata],[self.meter._yorig[0],evt.ydata]) # adjust meter line edges
        self.statusBar().showMessage('Distance: %lfkm'%ALRT.cutil.geo_to_km(self.meter._xorig[0],self.meter._yorig[0],self.meter._xorig[-1],self.meter._yorig[-1])[0]) # show user the distance
        self.drawSignal.emit(True) # draw the map
        return # we're done here
      hide = True # unless we don't measure but simply pointing along the map
      label = [] # a list of labels to present in a tooltip
      for l in self.ax.lines: # see if mouse points at objects of the map
        if l.contains(evt)[0]: # if object is a line
          label += [l.get_label()] # get it's label to the list
          hide=False # a flag for tooltip widget
      if not hide: # if we don't hide the tooltip
        self.stationNameWidget.setText('\n---\n'.join(label)) # set text in tooltip
        self.stationNameWidget.move(QCursor.pos()+QPoint(5,5)) # move the tooltip to the pointer position. might be out of screen area if on edges
        self.stationNameWidget.adjustSize() # adjust the size of tooltip widget to the text
        self.stationNameWidget.show() # show the widget
      else: self.stationNameWidget.hide() # if nothing is on the hit list - hide the tooltip widget

  def on_click(self,evt):
    'handle mouse clicks'
    if evt.button==1 and not evt.dblclick: # in case its a single left button click
      if evt.inaxes and self.toolbar.mode=='': # and not on a toolbar action of pan/zoom
        if self.homeDialog.isVisible(): # if we try to set "home" location
          self.homeDialog.setLatLon(evt.ydata,evt.xdata) # get the mouse click location and put in dialog
          return # we're out of here
        if self.eventDialog.isVisible(): # if we try to set an event location
          self.eventDialog.setLatLon(evt.ydata,evt.xdata) # get the mouse click location and put in dialog
          return # we're out of here
    elif evt.button==3 and evt.dblclick: # if its a right button double click
      if evt.inaxes and self.toolbar.mode=='': # and not on a toolbar action of pan/zoom
        self.eventDialog.setLatLon(evt.ydata,evt.xdata) # get the mouse click location and put in event dialog
        self.setNewEvent() # show the event dialog for creating a test event
        return # we're out of here
    elif evt.button==3 and not evt.dblclick: # if its a right button and not a double click
      if evt.inaxes and self.toolbar.mode=='': # and not on a toolbar action of pan/zoom
        self.meter.set_data([evt.xdata],[evt.ydata]) # update the meter measurement tool
        self.ax.add_artist(self.meter) # add the meter to the axes
        return # we're out of here

  def on_unclick(self,evt):
    'handle mouse unclick or mouse button release'
    if evt.button==3 and any(self.meter.get_data()): # if its the right button and there is some data set in the meter
      self.meter.remove() # remove the meter from the axes
      self.drawSignal.emit(True) # redraw the map
      self.statusBar().showMessage('Distance: %lfkm'%ALRT.cutil.geo_to_km(self.meter._xorig[0],self.meter._yorig[0],self.meter._xorig[-1],self.meter._yorig[-1])[0],1000) # last update of the measurement distance
      self.meter.set_data([],[]) # remove any data from the meter line

  def save_figure(self):
    print('todo: save_figure')

  def saveAs_figure(self):
    print('todo: saveAs_figure')

  def create_main_frame(self):
    'Create the main window widget with spliter, figure, toolbar'
    self.splitter = QSplitter(Qt.Vertical) # main widget splitter
    self.viewer = QWidget(self.splitter) # viewer for upper splitter panel
    self.vbox = QVBoxLayout(self.viewer) # vbox for figure and toolbar
    self.fig = Figure((6,3),dpi=100) # mpl figure (see matplotlib for details
    self.ax = self.fig.add_subplot(111) # mpl axes - see matplotlib for details
    self.ax.get_xaxis().get_major_formatter().set_useOffset(False) # make sure longitude are real numbers as %f
    self.ax.get_yaxis().get_major_formatter().set_useOffset(False) # make sure latitude are real numbers as %f
    self.ax.set_xlim(-160,90) # set starting view limits to map longitudes
    self.ax.set_ylim(-80,80) # set starting view limits to map latitudes
    self.ax.set_aspect('equal','datalim','C') # make sure lat and lon are not scaled differently and that widow size is fixed. data limits might change according to window size change
    self.ax.set_position([0,0,1,1]) # fill up the figure with the map axes
    self.ax.grid(True,color=[1,1,1,0.75]) # add grid
    self.ax.grid(GRIDON) # set grid to default state
    self.ax.tick_params('x',length=0,width=5,pad=-10,colors=[1,1,1,0.75]) # adjust x ticks
    self.ax.tick_params('y',length=0,width=5,pad=-20,colors=[1,1,1,0.75])# adjust y ticks
    [t.set_ha('left') for t in self.ax.xaxis.get_majorticklabels()] # adjust x ticks
    [t.set_va('bottom') for t in self.ax.yaxis.get_majorticklabels()] # adjust y ticks
    self.ax.drag_pan = self.drag_pan # replacing original drag_pan function of axes to home made one to make sure no panning out of geo bounderies
    self.canvas = FigureCanvas(self.fig) # set the canvas of figure
    self.canvas.setParent(self.viewer) # place canvas in viewer
    self.toolbar = NavigationToolbar(self.canvas, self.viewer) # add the toolbar of the canvas
    self.vbox.addWidget(self.canvas) # add canvas to layout
    self.vbox.addWidget(self.toolbar) # add toolbar to layout
    self.setCentralWidget(self.splitter) # set splitter as the main widget
    self.viewer.setFocus() # focus on viewer

  def create_message_widget(self):
    'creates the bottom tabed message widget.'
    self.mw = messagesWidget(self.splitter) # see UIModules for more details
    self.sysmsg = self.mw.sysmsg # easy access to system messages tab
    self.trigmsg = self.mw.trigmsg # easy access to trigers messages tab
    self.evntmsg = self.mw.evntmsg # easy access to event messages tab
    self.errmsg = self.mw.errmsg # easy access to messages tab

  def create_tooltip_widget(self):
    'creates tooltip of figure elements'
    self.stationNameWidget = QLabel() # take a QLabel
    self.stationNameWidget.setFrameShape(QFrame.StyledPanel) # add a frame
    self.stationNameWidget.setWindowFlags(Qt.ToolTip) # make window look like a tooltip
    self.stationNameWidget.setAttribute(Qt.WA_TransparentForMouseEvents) # mouse events can't affet it.
    self.stationNameWidget.hide() # hide for now. see self.on_move function on how to use.

  def drag_pan(self,button,key,x,y):
    'a replacement to the original drag_pan function of the mpl axes.'
    mpl.axes.Axes.drag_pan(self.ax,button,key,x,y) # see matplotlib for more details.
    self.fixlimits() # fix the limits so we stay within the geo bounderies.

  def fixlimits(self):
    'fix the limits of the axes to acceptable geographic bounds'
    x0,x1 = self.ax.get_xlim() # get current longitude limits
    y0,y1 = self.ax.get_ylim() # get current latitude limits
    dx = x1-x0 # distance from center to edge horizontal
    dy = y1-y0 # distance from center to edge vertical
    if dy>150: dy=150 # don't exceed latitude limit
    if y1>75: # fix maximal latitude
      y1=75
      y0=y1-dy # and adjust minimal one
    if y0<-75: # fix maximal latitude
      y0 = -75
      y1 = y0+dy # and adjust maximal one
    if dx>358: dx=358 # don't exceed longidute limit
    if x1>179: # fix maximal longitude
      x1=179
      x0=x1-dx # adjust minimal one
    if x0<-179: # fix minimal longitude
      x0=-179
      x1=x0+dx# adjust maximal one
    # set limits to corrected ones
    self.ax.set_ylim(y0,y1)
    self.ax.set_xlim(x0,x1)

  def get_stations_file(self):
    'open a dialog to get a file name'
    defaultpath = os.path.split(STATIONS_FILE)[0] # default to original file location. set original file in configuration file or defaults
    fileurl = str(QFileDialog.getOpenFileName(self, 'Open stations file',defaultpath)) # get the file name
    if fileurl:
      self.load_stations(fileurl) # load the stations

  def load_stations(self,fileurl=STATIONS_FILE):
    '''load stations names from a file.
       file should be in the format of:
         [network] [station] [latitude] [longitude]
       additional columns will be ignored
       for comments in file use '#'
    '''
    try:
      stations = np.loadtxt(fileurl,dtype=np.dtype([('net','|U2'),('sta','|U5'),('lat',float),('lon',float)]),usecols=range(4)) # read file
    except Exception as msg:
#      self.message("Can't load stations from %s: \n"%(fileurl)+msg,'ElViS - Error loading stations') # show a message window if failed
      return
    ids = ['.'.join([n,s]) for n,s in zip(stations['net'],stations['sta'])] # get stations ids as net.sta
    stations = [mpl.lines.Line2D([stations['lon'][i]],[stations['lat'][i]],marker='^',c='k',ms=6,label=ids[i]) for i in range(len(ids))] # create lines (a marker) for each station
    [station.remove() for station in self.stations] # remove old stations if available
    self.trigedlist = {} # refresh the list of triggered stations
    self.activeStationsList = {} # refresh the list of active stations
    self.stations = stations # set new stations
    [self.ax.add_line(station) for station in stations] # add stations locations to map
    self.draw(True) # redraw the map

  def set_home(self,lat=HomeLat,lon=HomeLon,label=HomeLabel,markersize=HomeSize,color=HomeColor,marker=HomeMarker):
    'plot the "home" location on map'
    if not 'home' in self.__dict__: # if this is the first time we set the home location
      self.home, = self.ax.plot([lon],[lat],label=label,markersize=markersize,color=color,marker=marker) # create a line (marker) and add it to the map
    self.home.set_xdata(lon) # update longitude
    self.home.set_ydata(lat)# update latitude
    self.home.set_label(label) # update label
    self.home.set_markersize(markersize) # update marker size
    self.home.set_color(color) # update marker color
    self.home.set_marker(marker) # update marker type
    self.drawSignal.emit(True)

  def setHomeLocation(self):
    'open home setup dialog'
    self.homeDialog.show() # see UIModules for more details.

  def onSetHomeLocationAccepted(self):
    '''get the parameters from the homeDialog and sets the home location on map
      fires when homeDialog is accepted.'''
    lat,lon,label,markersize,color,marker = self.homeDialog.getParams() # get parameters from dialog
    self.set_home(lat,lon,label,markersize,color,marker) # set location on map

  def goHomeLocation(self):
    'zoom to home location'
    x,y = (self.home._x[0],self.home._y[0]) # get the home location
    self.osm.relimcorrected(x-1,x+1,y-1,y+1) # change limits of the map to zoom in on home location
    self.redrawbgmap() # redraw the map (updating background maps)

  def zoomIsrael(self):
    'zoom to israel'
    self.osm.relimcorrected(32.5,37.5,29,34) # adjust map limits
    self.redrawbgmap() # redraw the map (updating background maps)

  def ZoomTo(self):
    'zoom to area set by user'
    self.zoomform.show() # run a widget to get zoom extents. see UIModules for details.

  def onZoomToAccepted(self):
    '''get limits from zoomform and zoom to area.
       fires when zoomform is accepted'''
    if self.zoomform.validate(): # make sure limits are acceptable
      w,e,s,n = self.zoomform.getLims() # get limits
      self.osm.relimcorrected(w,e,s,n) # adjust map limits
      self.redrawbgmap() # redraw the map (updating background maps)

  def setNewEvent(self):
    'open new event dialog'
    self.eventDialog.show() # see UIModules for details.

  def onNewEventAccepted(self):
    '''get event location and parameters and send a test decition module event to server.
    needs to be more agile and configurable '''
    lat,lon,depth,label,mag,delay = [str(i) for i in self.eventDialog.getParams()] # get parameters
    body = AMQ.getDMxmlmsg(label,mag,lat,lon,depth,float(delay)) # get DM xml message. see amq2py for details.
    writer = AMQ.AMQWriter(usr=AMQDMUSER,passwd=AMQDMPASSWD,verbose=False,host_and_ports=[(AMQHOST,AMQPORT)]) # see amq2py module for details
    self.evntmsg.add("Attempting to send an event message",True)
    self.sysmsg.add("Writer connecting to ActiveMQ server...",True)
    writer.connectToActiveMQ() # connect to amq server
    self.sysmsg.add("Writer sending message to ActiveMQ server...",True)
    writer.sendActiveMQmsg(body) # send the message
    self.sysmsg.add("Writer disconnecting from ActiveMQ server...",True)
    writer.disconnectToActiveMQ() # disconnect from amq server
    self.sysmsg.add("You should see an alert now...",True)

  def set_watch_value(self,text):
    'change station monitoring value type (displacement,velocity or acceleration'
    text = str(text) # get text from combobox (see create_menu function)
    self._watchingGMValue =  watchValsDict[text] # get value code (dmax,vmax,amax)
    self.statusBar().showMessage('Watching %s values.'%text,2000) # note the user of the change
    # change will take affect as data packets arrive from the AMQ server.

  def create_menu(self):
    'Creates main menu'
    # Populate the menubar:
    # Add File submenu
    self.file_menu = self.menuBar().addMenu("&File")
    # load stations
    load_stations_action = self.create_action("&Load",
            shortcut="Ctrl+L", slot=self.get_stations_file,
            icon='document-open',tip="Load stations from a file")
    # Save
    save_action = self.create_action("&Save",
            shortcut="Ctrl+S", slot=self.save_figure,
            icon='filesave',tip="Save the figure")
    # Save As...
    saveAs_action = self.create_action("S&ave As...",
            shortcut="Shift+Ctrl+S", slot=self.saveAs_figure,
            icon='filesaveas',tip="Save the figure")
    # Quit
    quit_action = self.create_action("&Quit", slot=self.close,
            icon='system-shutdown',shortcut="Ctrl+Q", tip="Close the application")
    # populate the file submenu
    self.add_actions(self.file_menu,
            (load_stations_action,save_action, saveAs_action, None, quit_action))
    # Add view submenue
    self.view_menu = self.menuBar().addMenu("&View")
    # ZoomTo
    ZoomTo_action = self.create_action("&Zoom To...",
            shortcut="Shift+Ctrl+Z", slot=self.ZoomTo,
            icon='viewmagfit',tip="Zoom to area")
    # Israel
    ZoomIsrael_action = self.create_action("Zoom To &Israel",
            shortcut="Shift+Ctrl+I", slot=self.zoomIsrael,
            icon='viewmag1',tip="Zoom to Israel")
    # go to "home" location
    gohome_action = self.create_action("Zoom To &Home",
            shortcut="Shift+Ctrl+V", slot=self.goHomeLocation,
            icon='user-home',tip="Zoom to your location for alerts.")
    # toggle grid on or off
    togGrid_action = self.create_action("&Grid (on/off)",
            shortcut="Shift+Ctrl+G", slot=self.grid,
            icon=None,tip="Toggle map grid.",checkable=True)
    togGrid_action.setChecked(GRIDON)
    # set watch value (displacement, velocity or acceleration)
    watchval_cbox = QComboBox()
    # set value types
    watchval_cbox.addItem("Acceleration")
    watchval_cbox.addItem("Velocity")
    watchval_cbox.addItem("Displacement")
    # set the current value according to configuration
    i = [watchValsDict[v] for v in ["Acceleration","Velocity","Displacement"]].index(self._watchingGMValue)
    watchval_cbox.setCurrentIndex(i)
    # connect the combobox to function
    watchval_cbox.activated[str].connect(self.set_watch_value)
    # add add to a submenu
    watchval_widget = QWidgetAction(watchval_cbox)
    watchval_widget.setDefaultWidget(watchval_cbox)
    watchval_action = QMenu('Watch value',self.view_menu)
    watchval_action.addAction(watchval_widget)
    # set "home" location
    sethome_action = self.create_action("Set &Location",
            shortcut="Shift+Ctrl+H", slot=self.setHomeLocation,
            icon='preferences-system',tip="Set your location for alerts.")
    # clear events locations
    clear_events_action = self.create_action("&Clear Events",
            shortcut="Shift+Ctrl+C", slot=self.clear_events,
            icon='edit-clear',tip="Clear Events location from the map.")
    # populate the view submenu
    self.add_actions(self.view_menu,
            (ZoomTo_action,gohome_action,ZoomIsrael_action,None,sethome_action,clear_events_action,None,togGrid_action))
    self.view_menu.addMenu(watchval_action) # add the submenu to view menu
    # Add Edit submenu
    self.edit_menu = self.menuBar().addMenu("&Event")
    # Create a fake event
    event_action = self.create_action("Create &Event",
            shortcut="Shift+Ctrl+E", slot=self.setNewEvent,
            icon='preferences-system',tip="Fire a New Event.")
    # populate the Edit menu
    self.add_actions(self.edit_menu,
            [event_action])
    # Add Connection submenu
    self.connection_menu = self.menuBar().addMenu("&Connection")
    reconnect_action = self.create_action("&Reconnect",
            shortcut="Shift+Ctrl+C", slot=self.reconnectToAMQ,
            icon='server',tip="Connect to current AMQ server.")
    connectTo_action = self.create_action("Connect &To...",
            shortcut="Shift+Ctrl+T", slot=self.connectToNewAMQ,
            icon='network',tip="Connect to New AMQ server.")
    disconect_action = self.create_action("&Disconnect from AMQ server",
            shortcut="Shift+Ctrl+D", slot=self.disconnectAMQ,
            icon='stock_delete',tip="Disconnect from AMQ server")
    status_action = self.create_action("St&atus",
            shortcut="Shift+Ctrl+A", slot=self.statusAMQ,
            icon='dialog-question',tip="AMQ Server connection detail and status")
    # populate the connection submenu
    self.add_actions(self.connection_menu,
                     (connectTo_action,reconnect_action,disconect_action,None,status_action))
    # Add help submenu
    self.help_menu = self.menuBar().addMenu("&Help")
    # Help
    help_action = self.create_action("&Help",
            shortcut='F1', slot=self.on_help,
            icon='help',tip='help')
    # About
    about_action = self.create_action("&About",
            shortcut='F2', slot=self.on_about,
            icon='user-info',tip='About This Application')
    # About QT
    aboutQt_action = self.create_action("&About QT",
            shortcut='F3', slot=self.on_aboutQt,
            icon='stock_about',tip='About QT')
    # License
    license_action = self.create_action("&License",
            shortcut='F4', slot=self.on_license,
            icon='access',tip='Application License')
    # Populate help submenu
    self.add_actions(self.help_menu, (help_action,None,about_action,aboutQt_action,license_action))


  def add_actions(self, target, actions):
    'Utility function for menu creation'
    for action in actions:
      if action is None:
        target.addSeparator()
      else:
        target.addAction(action)

  def create_action(self, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False,
                      signal="triggered()"):
    'Utility function for menu actions creation'
    action = QAction(text, self)
    action.setIconVisibleInMenu(True)
    if icon is not None:
      i = QIcon.fromTheme(icon,QIcon(":/%s.png" % icon))
      action.setIcon(i)
    if shortcut is not None:
      action.setShortcut(shortcut)
    if tip is not None:
      action.setToolTip(tip)
      action.setStatusTip(tip)
    if slot is not None:
      #self.connect(action, SIGNAL(signal), slot)
      action.triggered.connect(slot)
    if checkable:
      action.setCheckable(True)
    return action

  def create_pushButton(self,text,toolbar=None, slot=None, shortcut=None, icon=None, tip=None):
    'Utility function for button creation'
    # create the button
    button = QPushButton(text,self)
    # populate properties
    if slot:
      # connect a function
      button.clicked.connect(slot)
    if icon:
      # add icon
      i = QIcon.fromTheme(icon,QIcon(":/%s.png" % icon))
      button.setIcon(i)
      button.setIconSize(QSize(24,24))
    if shortcut:
      # set the shortcut
      button.setShortcut(shortcut)
    if tip:
      # add tooltip and status tip
      button.setToolTip(tip)
      button.setStatusTip(tip)
    if toolbar:
      # add the button to a toolbar (or any widget)
      toolbar.addWidget(button)
    return button

  def create_status_bar(self):
    'Add a status bar'
    # set default message
    self.status_text = QLabel("Initializing...")
    self.connstatLabel = QLabel()
    self.statusBar().addWidget(self.status_text, 1)
    self.statusBar().addPermanentWidget(self.connstatLabel)
    self.connstat(False,'ActiveMQ server is Not Connected.')


  def on_about(self):
    'show a messagebox about the application'
    msg = "<p align='center'><big>ElarmS Visualization System (ElViS)</big><br><br> \
    Visually Monitoring ElarmS Earthquake Early Warning System<br><br> \
    <small>Created<br> \
    by<br> \
    Ran Novitsky Nof @ BSL, 2014</small><br><br>\
    <a href='http://ran.rnof.info/'>http://ran.rnof.info</a><p>"
    QMessageBox.about(self,"About", msg.strip())

  def on_aboutQt(self):
    'show a messagebox about QT'
    QMessageBox.aboutQt(self,'')

  def on_license(self):
    'GPL licanse message'
    msg = "<p><b>This</b> is a free software; you can redistribute it and/or modify it under the \
terms of the GNU General Public License as published by the Free Software \
Foundation; either version 3 of the License, or (at your option) any later \
version.</p>\
<p><b>This application</b> is distributed in the hope that it will be useful, but WITHOUT ANY \
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR \
A PARTICULAR PURPOSE.  See the GNU General Public License for more details.</p> \
<p>You should have received a copy of the GNU General Public License along with \
this application; if not, see <a href='http://www.gnu.org/licenses/'>http://www.gnu.org/licenses/</a>.</p>"
    QMessageBox.about(self,"Application Licanse", msg.strip())

  def on_help(self):
    'Show help on a message window. Uses the argparse help'
    msg = parser.format_help()
    QMessageBox.about(self,"Help", msg.strip())

  def message(self,msg,title='Error'):
    'a simple message window'
    QMessageBox.about(self,title,msg)

def main(args):
  print(VERBOSE)
  # create the application
  app = QApplication(sys.argv)
  #splash
  splash_pix = QPixmap('splash.png')
  splash_pix.scaledToHeight(50)
  splash = QSplashScreen(splash_pix)
  splash.setMask(splash_pix.mask())
  splash.show()
  app.processEvents()
  # populate the QT4 form
  appwin = AppForm(splash,args)
  appwin.show()
  splash.finish(appwin)
  # run the application
  sys.exit(app.exec_())

if __name__=="__main__":
  # parse the arguments
  args = parser.parse_args(sys.argv[1:])
  if args.cfgfile:
    # execute configuration file
    try:
      exec(args.cfgfile)  # python2
    except TypeError:
      exec(args.cfgfile.read())  # python3
  topics = {'gmpeak':GMPEAKtopic, # peak parameters AMQ topic
          'trigger':TRIGGERtopic, # trigger and trigger parameters AMQ topic
          'alarms':ALARMStopic, # E2 alarms AMQ topic
          'dm':DMtopic, # DM event AMQ topic
          'waveforms' : EDATAtopic} # Event waveforms raw data topic
  mpl.rcParams['font.size']=float(FONTSIZE)
  main(args)
