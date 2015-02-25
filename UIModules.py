#!/usr/bin/env python

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


# By Ran Novitsky Nof @ BSL, 2015
# ran.nof@gmail.com


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import datetime,matplotlib

# zoomto form line class
class zoomLineEdit(QLineEdit):
  def __init__(self,val,minval,maxval):
    QLineEdit.__init__(self)
    self.setText(val)
    self.minval=minval
    self.maxval=maxval
    validator = QDoubleValidator()
    validator.setRange(minval,maxval,7)
    self.setValidator(validator)
    self.textChanged.connect(self.validate)
    self.setToolTip('%d <= Value >= %d'%(minval,maxval))
  def validate(self):
    if not self.validator().validate(self.text(),2)==(2,2):
      self.backspace()

# Zoom to map area dialog
class zoomForm(QDialog):
  def __init__(self,parent=None):
    QDialog.__init__(self,parent=parent)
    self.setWindowTitle('ElViS - Zoom to area rectangle')
    vbox = QVBoxLayout(self)
    w = QWidget()
    grid = QGridLayout(w)
    vbox.addWidget(w)
    westlabel = QLabel('West')
    W = zoomLineEdit('-180',-180,180)
    grid.addWidget(westlabel,2,1)
    grid.addWidget(W,2,2)
    eastlabel = QLabel('East')
    E = zoomLineEdit('180',-180,180)
    grid.addWidget(eastlabel,2,5)
    grid.addWidget(E,2,6)
    northlabel = QLabel('North')
    N = zoomLineEdit('90',-90,90)
    grid.addWidget(northlabel,1,3)
    grid.addWidget(N,1,4)
    southlabel = QLabel('South')
    S = zoomLineEdit('-90',-90,90)
    grid.addWidget(southlabel,3,3)
    grid.addWidget(S,3,4)
    self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal, self)
    vbox.addWidget(self.buttons)
    self.buttons.accepted.connect(self.accept)
    self.buttons.rejected.connect(self.reject)
    self.W = W
    self.E = E
    self.S = S
    self.N = N
  def setLims(self,w,e,s,n):
    self.W.setText(str(w))
    self.E.setText(str(e))
    self.S.setText(str(s))
    self.N.setText(str(n))
  def getLims(self):
    w = self.W.text().toDouble()[0]
    e = self.E.text().toDouble()[0]
    s = self.S.text().toDouble()[0]
    n = self.N.text().toDouble()[0]
    return w,e,s,n
  def validate(self):
    w,e,s,n = self.getLims()
    if w>=e and s>=n:
      QMessageBox.warning(self,'ElViS - Erorr','West value should be lower than East value.\nSouth value should be lower than North value.')
      return 0
    elif w>=e:
      QMessageBox.warning(self,'ElViS - Erorr','West value should be lower than East value.')
      return 0
    elif s>=n:
      QMessageBox.warning(self,'ElViS - Erorr','South value should be lower than North value.')
      return 0
    else:
      return 1


# event dialog
class eventDialog(QDialog):
  def __init__(self,parent=None):
    QDialog.__init__(self,parent=parent)
    self.setWindowTitle('ElViS - Send an Event')
    vbox = QVBoxLayout(self)
    w = QWidget()
    grid = QGridLayout(w)
    vbox.addWidget(w)
    lonLabel = QLabel('Longitude')
    lon = zoomLineEdit(str(0),-180,180)
    grid.addWidget(lonLabel,1,1)
    grid.addWidget(lon,1,2)
    latLabel = QLabel('Latitude')
    lat = zoomLineEdit(str(0),-90,90)
    grid.addWidget(latLabel,2,1)
    grid.addWidget(lat,2,2)
    depthLabel = QLabel('Depth')
    depth = zoomLineEdit(str(8),0,6200)
    depth.setToolTip('Set depth (0-6200)')
    grid.addWidget(depthLabel,3,1)
    grid.addWidget(depth,3,2)
    labelLabel = QLabel('ID')
    label = QLineEdit()
    label.setText('Testing Event')
    label.setToolTip('Enter the event ID')
    grid.addWidget(labelLabel,4,1)
    grid.addWidget(label,4,2)
    magLabel = QLabel('Magnitude')
    mag= QLineEdit()
    validator = QDoubleValidator(-2,10,1)
    mag.setValidator(validator)
    mag.setToolTip('Set Magnitude (-2 - 10)')
    mag.setText(str(7.5))
    grid.addWidget(magLabel,5,1)
    grid.addWidget(mag,5,2)
    delayLabel = QLabel('Delay')
    delay = zoomLineEdit(str(4),0,180)
    depth.setToolTip('Set message delay in seconds (0-180)')
    grid.addWidget(delayLabel,6,1)
    grid.addWidget(delay,6,2)
    self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal, self)
    vbox.addWidget(self.buttons)
    self.buttons.accepted.connect(self.accept)
    self.buttons.rejected.connect(self.reject)
    self.lon = lon
    self.lat = lat
    self.label = label
    self.mag=mag
    self.delay=delay
    self.depth=depth
  def setLatLon(self,lat,lon):
    self.lat.setText(str(lat))
    self.lon.setText(str(lon))
  def getLatLon(self):
    lat = self.lat.text().toDouble()[0]
    lon = self.lon.text().toDouble()[0]
    return lat,lon
  def setParams(self,Lat,Lon,Depth,Label,Mag,Delay):
    self.lat.setText(str(Lat))
    self.lon.setText(str(Lon))
    self.depth.setText(str(Depth))
    self.label.setText(str(Label))
    self.mag.setText(str(Mag))
    self.delay.setText(str(Delay))
  def getParams(self):
    lat = self.lat.text().toDouble()[0]
    lon = self.lon.text().toDouble()[0]
    depth = self.depth.text().toDouble()[0]
    label = str(self.label.text())
    mag = self.mag.text().toDouble()[0]
    delay = self.delay.text().toDouble()[0]
    return lat,lon,depth,label,mag,delay


# set home location dialog
class homeDialog(QDialog):
  def __init__(self,Lat,Lon,Label='Home',Markersize=6,Color='red',Marker='s',parent=None):
    QDialog.__init__(self,parent=parent)
    self.setWindowTitle('ElViS - Set your location')
    vbox = QVBoxLayout(self)
    w = QWidget()
    grid = QGridLayout(w)
    vbox.addWidget(w)
    lonLabel = QLabel('Longitude')
    lon = zoomLineEdit(str(Lon),-180,180)
    grid.addWidget(lonLabel,1,1)
    grid.addWidget(lon,1,2)
    latLabel = QLabel('Latitude')
    lat = zoomLineEdit(str(Lat),-90,90)
    grid.addWidget(latLabel,2,1)
    grid.addWidget(lat,2,2)
    labelLabel = QLabel('Name')
    label = QLineEdit()
    label.setText(Label)
    label.setToolTip('Enter the name for "Home"')
    grid.addWidget(labelLabel,3,1)
    grid.addWidget(label,3,2)
    markersizeLabel = QLabel('Size')
    markersize= QLineEdit()
    validator = QIntValidator()
    validator.setRange(1,100)
    markersize.setValidator(validator)
    markersize.setToolTip('Set Marker Size (1-100)')
    markersize.setText(str(Markersize))
    grid.addWidget(markersizeLabel,4,1)
    grid.addWidget(markersize,4,2)
    colorLabel = QLabel('Color')
    color = QComboBox()
    [color.addItem(i) for i in matplotlib.colors.cnames]
    color.setCurrentIndex(color.findText(Color))
    color.setMaxVisibleItems(10)
    grid.addWidget(colorLabel,5,1)
    grid.addWidget(color,5,2)
    markerLabel = QLabel('Marker')
    marker = QComboBox()
    [marker.addItem(i) for i in matplotlib.markers.MarkerStyle.markers.values() if not i =='nothing']
    Marker = [i[1] for i in matplotlib.markers.MarkerStyle.markers.items() if i[0]==Marker][0]
    marker.setCurrentIndex(marker.findText(Marker))
    grid.addWidget(markerLabel,6,1)
    grid.addWidget(marker,6,2)
    self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,Qt.Horizontal, self)
    vbox.addWidget(self.buttons)
    self.buttons.accepted.connect(self.accept)
    self.buttons.rejected.connect(self.reject)
    self.lon = lon
    self.lat = lat
    self.label = label
    self.markersize=markersize
    self.color=color
    self.marker=marker
  def setLatLon(self,lat,lon):
    self.lat.setText(str(lat))
    self.lon.setText(str(lon))
  def getLatLon(self):
    lat = self.lat.text().toDouble()[0]
    lon = self.lon.text().toDouble()[0]
    return lat,lon
  def setParams(self,Lat,Lon,Label,Markersize,Color,Marker):
    self.lat.setText(str(Lat))
    self.lon.setText(str(Lon))
    self.label.setText(str(Label))
    self.markersize.setText(str(Markersize))
    self.color.setCurrentIndex(self.color.findText(Color))
    Marker = [i[1] for i in matplotlib.markers.MarkerStyle.markers.items() if i[0]==Marker][0]
    self.marker.setCurrentIndex(self.marker.findText(Marker))
  def getParams(self):
    lat = self.lat.text().toDouble()[0]
    lon = self.lon.text().toDouble()[0]
    label = str(self.label.text())
    markersize = self.markersize.text().toDouble()[0]
    color = str(self.color.currentText())
    marker = str(self.marker.currentText())
    marker = [i[0] for i in matplotlib.markers.MarkerStyle.markers.items() if i[1]==marker][0]
    return lat,lon,label,markersize,color,marker

class messageLogger(QTextEdit):
  def __init__(self,parent=None):
    self.MaxLines=1000
    QTextEdit.__init__(self,parent=parent)
    self.setLineWrapMode(0)
    self.setReadOnly(True)
    self.Doc = self.document()
    self.cursor = QTextCursor(self.Doc)

  def add(self,msg,ts=''):
    self.cursor.setPosition(0)
    if not msg.endswith('\n'): msg = msg+'\n'
    if ts == True:
      ts = datetime.datetime.utcnow().isoformat()
    if ts:
      msg = ts+' | '+msg
    while self.Doc.lineCount()>=self.MaxLines: self.deletelastline()
    self.cursor.insertText(msg)

  def deletelastline(self):
    while self.cursor.movePosition(self.cursor.NextBlock): pass
    self.cursor.select(2)
    self.cursor.removeSelectedText()
    self.cursor.deletePreviousChar()
    self.cursor.clearSelection()
    self.cursor.setPosition(0)

# Messages widget
class messagesWidget(QTabWidget):
  def __init__(self,parent=None):
    QTabWidget.__init__(self,parent=parent)
    self.sysmsg = messageLogger()
    self.trigmsg = messageLogger()
    self.evntmsg = messageLogger()
    self.errmsg = messageLogger()
    self.addTab(self.trigmsg,'Triggers')
    self.addTab(self.evntmsg,'Events')
    self.addTab(self.sysmsg,'System')
    self.addTab(self.errmsg,'Errors')
    # clear button
    w = QWidget()
    self.setCornerWidget(w)
    self.corner = QHBoxLayout(w)
    w.setLayout(self.corner)
    btn = QToolButton(w)
    btn.setText('Clear')
    btn.setMinimumSize(50,20)
    btn.clicked.connect(self.cleartabtxt)
    btn.setStatusTip('Clear text in current message box')
    btn.setToolTip('Clear text in current message box')
    self.corner.addWidget(btn)
  def cleartabtxt(self):
    tab = self.currentWidget().clear()

# Alert Panel Widget
class alertPanel(QMainWindow):
  '''Alert panel where ETA of S wave will be shown.
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
                 }


  '''
  def __init__(self,parent=None):
    QMainWindow.__init__(self,parent)
    self.parent=parent
    self.eq = {}
  def addPanel(self,Eid,params):
    eq = type("EQ",(),params)
    eq.eta = -1
    eq.eta0 = -1
    eq.widget = messageLogger()
    eq.widget.Eid=Eid
    self.eq[Eid] = eq
    dock = QDockWidget('Eathquake Alert id: '+Eid)
    dock.setWindowTitle('Eathquake Alert ID: '+Eid)
    dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
    dock.setWidget(eq.widget)
    self.parent.addDockWidget(Qt.TopDockWidgetArea,dock)
    dock.setFloating(True)
    dock.setFixedWidth(self.parent.width())
    dock.move(self.parent.pos()+self.parent.mw.pos())
    dock.setGeometry(dock.pos().x(),dock.pos().y(),self.parent.width()-18,200)
    def removeEid(self,visible):
      if not visible:
        self.emit(SIGNAL('RemoveEID'),Eid)
        self.destroy()
    dock.closeEvent = removeEid.__get__(dock,dock.__class__)
    self.connect(dock,SIGNAL('RemoveEID'),self.removeEventID)
  def updatePanel(self,Eid,params,eta):
    if not Eid in self.eq: return
    eq = self.eq[Eid]
    [setattr(eq,k,v) for k,v in params.items()]
    if eq.eta0==-1: eq.eta0=eta
    eq.eta = eta
    eq.widget.clear()
    eq.widget.setText(self.formatEQAlert(eq))
  def formatEQAlert(self,eq):
    msg = "<h2><b>%.1fs M: %.1f I: %d</b> ID: %s</h2>Lat: %.5f Lon: %.5f Depth: %d (%0.2f deg, %0.1fkm away)<br>Origin Time: %s<br>Max alert time: %0.1fs"%(eq.eta,eq.mag,eq.I,eq.m.Eid,eq.lat,eq.lon,eq.depth,eq.azimuth,eq.dist,eq.ot,eq.eta0)
    return msg
  def removeEventID(self,Eid):
    self.eq.pop(Eid)


