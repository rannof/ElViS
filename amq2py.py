#!/bin/env python
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

import sys,os,threading
import stomp,datetime,zlib
from numpy import frombuffer,dtype,array, zeros
from xml.dom import minidom
import logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

msglock = threading.Lock()

if sys.hexversion >= 0x03000000:  # Python 3+
  PY3 = True
else:
  PY3 = False


def ID(a):
  'get network,station,location,channal from a Structured Array.'
  net = a['net']
  sta = a['sta']
  chn = a['chn']
  loc = a['loc']
  return ['.'.join([n,s,l,c]) for n,s,l,c in zip(net,sta,loc,chn)]

class GMPeak(object):
  def __init__(self,m=None):
    self.type='G'
    # see data structure in GMPeak.h
    self.rawheadertype = dtype([('type', 'S1'), ('version','>i4'),('source', 'S20'), ('id', '>i4'), ('npackets', '>i4')])
    self.headertype = dtype([('type', 'U1'), ('version','>i4'),('source', 'U20'), ('id', '>i4'), ('npackets', '>i4')])
    self.rawdatatype = dtype([('sta', 'S5'), ('chn', 'S4'), ('net', 'S3'), ('loc', 'S3'), ('lat', '>f8'), ('lon', '>f8'), ('ts', '>f8'), ('nsamps', '>i4'), ('samprate', '>f4'), ('dmax', '>f4'), ('vmax', '>f4'), ('amax', '>f4'), ('dindex', '>i4'), ('vindex', '>i4'), ('aindex', '>i4'), ('latency', '>f4')])
    self.datatype = dtype([('sta', 'U5'), ('chn', 'U4'), ('net', 'U3'), ('loc', 'U3'), ('lat', '>f8'), ('lon', '>f8'), ('ts', '>f8'), ('nsamps', '>i4'), ('samprate', '>f4'), ('dmax', '>f4'), ('vmax', '>f4'), ('amax', '>f4'), ('dindex', '>i4'), ('vindex', '>i4'), ('aindex', '>i4'), ('latency', '>f4')])
    self.header = array([],dtype=self.headertype)
    self.packets= array([],dtype=self.datatype)
    if m: self.decode(m)
  def decode(self,m):
    self.raw=m
    header = frombuffer(m,self.rawheadertype,1)
    try:
      data = zlib.decompress(m[self.rawheadertype.itemsize+1:])
    except:
      data = m[self.headertype.itemsize+1:]
    self.header = header.astype(self.headertype)
    packets = frombuffer(data,self.rawdatatype,header['npackets'][0])
    self.packets = packets.astype(self.datatype)
  def __call__(self,m):
    self.decode(m)
  def __str__(self):
    return '\n'.join([datetime.datetime.utcfromtimestamp(p['ts']).isoformat()+' | G: '+' '.join([str(p[n]) for n in self.packets.dtype.names if not n=='ts' ]) for p in self.packets])

class TrigParam(object):
  def __init__(self,m=None):
    self.type='P'
    # see data structure in TrigParams.h
    self.headertype = dtype([('type', 'S1'),('version','>i4'), ('source', 'S20'), ('id', '>i4'), ('npackets', '>i4')])
    self.trigvaluestype = dtype([('tauP','>f4'),('tauPsnr','>f4'),('ttime','>i4'),('d','>f4'),('dsnr','>f4'),('dtime','>i4'),('v','>f4'),('vsnr','>f4'),('vtime','>i4'),('a','>f4'),('asnr','>f4'),('atime','>i4')])
    self.rawtype = dtype([('sta', 'S5'), ('chn', 'S4'), ('net', 'S3'), ('loc', 'S3'), ('lat', '>f8'), ('lon', '>f8')\
                           ,('sec', '>i4'),('msec','>i4'), ('packlength', '>i4')\
                           ,('recent_sample', '>i4'),('samplerate', '>f4'),('toffset', '>f4'),('arrtime', '>f8')\
                           ,('protime', '>f4'),('fndtime', '>f4'),('quetime', '>f4'),('sndtime', '>f4')\
                           ,('trigvalues',self.trigvaluestype,10)])
    self.datatype = dtype([('sta', 'U5'), ('chn', 'U4'), ('net', 'U3'), ('loc', 'U3'), ('lat', '>f8'), ('lon', '>f8')\
						   ,('ts', datetime.datetime),('msec','>i4'),('packlength', '>i4')\
                           ,('recent_sample', '>i4'),('samplerate', '>f4'),('toffset', '>f4'),('arrtime', '>f8')\
                           ,('protime', '>f4'),('fndtime', '>f4'),('quetime', '>f4'),('sndtime', '>f4')\
                           ,('trigvalues',self.trigvaluestype,10)])
    self.header = array([],dtype=self.headertype)
    self.packets= array([],dtype=self.datatype)
    if m: self.decode(m)
  def decode(self,m):
    self.raw=m
    header = frombuffer(m,self.headertype,1)
    data = zlib.decompress(m[self.headertype.itemsize+1:])
    self.header = header
    packets = frombuffer(data,self.rawtype,header['npackets'])
    names = ' '.join(packets.dtype.names).replace('sec','ts',1).split()
    packets.dtype.names = names
    self.packets = packets.astype(self.datatype)
    self.packets['ts'] = [datetime.datetime.utcfromtimestamp(float('.'.join([str(p['ts']),str(p['msec'])]))) for p in packets]
  def __str__(self):
    return '\n'.join(['%s | P: %s %s %s %s %f %f %f'% tuple([p['ts'].isoformat()]+[p[i] for i in range(6)]+[p[7]]) +\
      '\n'+'\n'.join(['\t'+' %10.6f'*len(v) % tuple(v) for v in p['trigvalues']]) for p in self.packets])

class Trigger(object):
  def __init__(self,m=None):
    self.type='T'
    self.sta=''
    self.chn=''
    self.net=''
    self.loc=''
    self.lat=0.0
    self.lon=0.0
    self.ts=datetime.datetime.min
    self.rawtype = dtype([('type', 'S1'),('version','>i4'), ('source', 'S20'), ('id', '>i4'), ('sta', 'S5'), ('chn', 'S4'), ('net', 'S3'), ('loc', 'S3'), ('lat', '>f8'), ('lon', '>f8'), ('sec', '>i4'), ('msec', '>i4')])
    self.datatype = dtype([('sta', 'U5'), ('chn', 'U4'), ('net', 'U3'), ('loc', 'U3'), ('lat', '>f8'), ('lon', '>f8'), ('ts', datetime.datetime)])
    if m: self.decode(m)
  def decode(self,m):
    self.raw=m
    data = frombuffer(m,self.rawtype,1)
    ts = float('.'.join([data['sec'].astype(str)[0], data['msec'].astype(str)[0]]))
    self.packets = array(zeros(len(data)),dtype=self.datatype)
    for k in self.datatype.names:
      if k in self.rawtype.names:
        self.packets[k] = data[k] 
    self.packets['ts'] = datetime.datetime.utcfromtimestamp(ts)
    self.sta= self.packets['sta'][0]
    self.chn= self.packets['chn'][0]
    self.net= self.packets['net'][0]
    self.loc= self.packets['loc'][0]
    self.lat= self.packets['lat'][0]
    self.lon= self.packets['lon'][0]
    self.ts = self.packets['ts'][0]
  def __call__(self,m):
    self.decode(m)
  def __str__(self):
    return self.ts.isoformat()+' | T: '+' '.join(['',self.net,self.sta,self.loc,self.chn,str(self.lat),str(self.lon)])

class RawData(object):
  def __init__(self,m=None):
    self.type='D'
    self.headertype = dtype([('type', 'S1'),('version','>i4'), ('source', 'S20'), ('id', '>i4'), ('npackets', '>i4')])
    if m: self.decode(m)
  def decode(self,m):
    self.raw=m
    pass
  def __str__(self):
    return 'Data packets are not supported at this version'

class algXML(object):
  def __init__(self,m=None):
    self.type='X'
    self.lat=0.0
    self.lon=0.0
    self.depth=0.0
    self.msgtime=datetime.datetime.min
    self.raw = None
    self.Eid = None
    self.msgorigsys = None
    self.msgtype = None
    self.orig_time=datetime.datetime.min
    self.mag=0.0
    self.magU = None
    if m: self.decode(m)
  def decode(self,m):
    self.raw = m
    xmldoc=minidom.parseString(m)
    em = xmldoc.getElementsByTagName('event_message')[0]
    self.Eid=xmldoc.getElementsByTagName('core_info')[0].attributes['id'].value
    self.msgorigsys=em.attributes['orig_sys'].value
    self.msgtime=datetime.datetime.strptime(em.attributes['timestamp'].value,'%Y-%m-%dT%H:%M:%S.%fZ')
    self.msgtype=em.attributes['message_type'].value
    self.lat=float(xmldoc.getElementsByTagName('lat')[0].firstChild.data)
    self.lon=float(xmldoc.getElementsByTagName('lon')[0].firstChild.data)
    self.depth=float(xmldoc.getElementsByTagName('depth')[0].firstChild.data)
    self.orig_time=datetime.datetime.strptime(xmldoc.getElementsByTagName('orig_time')[0].firstChild.data,'%Y-%m-%dT%H:%M:%S.%fZ')
    self.mag=float(xmldoc.getElementsByTagName('mag')[0].firstChild.data)
    self.magU=xmldoc.getElementsByTagName('mag')[0].attributes['units'].value
  def __call__(self,m):
    self.decode(m)
  def __str__(self):
    return '%s | E: %s (%s - %s) %f %f %f %f%s (%f)'%(self.orig_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),self.Eid,self.msgorigsys,self.msgtype,self.lat,self.lon,self.depth,self.mag,self.magU,(self.msgtime-self.orig_time).total_seconds())

# listner class for connecting to activeMQ
class AMQListener(object):
  def __init__(self,subscribeTo='/topic/eew.sys.dm.data',usr='monitor',passwd='monitor',name='listner',ID=1,verbose=False,log=False, loglevel='CRITICAL', host_and_ports=[('localhost',61613)], auto_decode=False, **kwargs):
    self.MESSAGES = []  # cash messages
    self.SUBSCRIBES = {}
    self.maxmessages=200  # cash messages max number
    self.subscribeTo=subscribeTo  # Default topic
    self.name=name  # Listener name
    self.usr=usr  # AMQ user
    self.passwd=passwd  # AMQ password
    self.id=ID
    self.logit=log  # should we save data to file?
    self._lastMessage = None
    self._verbose=verbose  # print to screen?
    self.host_and_ports=host_and_ports
    self._procfuncs = {
                       'T':Trigger,
                       'G':GMPeak,
                       'P':TrigParam,
                       'D':RawData,
                       '<':algXML
                      }
    self.triglogpath='log/triggers_'
    self.triglogext='.trig'
    self.evntlogpath='log/events_'
    self.evntlogext='.log'
    self.conn = stomp.Connection(host_and_ports=host_and_ports,auto_decode=auto_decode,**kwargs)
    self.conn.set_listener(self.name, self)
    if log and not os.path.exists('log'):
      sys.exit("Can't find logging directory: ./log\nCreate a directory:\nmkdir log")
    self.log = logging.getLogger('AMQ_{name}'.format(name=name))
    self.log.setLevel(loglevel)

  def connectToActiveMQ(self):
    if self._verbose: self.log.debug('Trying to Connect to AMQ server')
    self.conn.start()
    if not self.conn.is_connected(): self.conn.connect(self.usr,self.passwd,wait=True)

  def on_connecting(self,host_and_port):
    host,port = self.conn.transport.current_host_and_port
    if self._verbose: self.log.debug(' Connected to '+':'.join([host,str(port)]))

  def on_disconnected(self):
    if self._verbose: self.log.debug(' Connection lost...')

  def on_error(self, headers, message):
    if self._verbose: self.log.error('received an error {message}').format(message=message)

  def on_message(self, headers, message):
    self.MESSAGES += [(headers,message)]
    if len(self.MESSAGES)>self.maxmessages: self.MESSAGES.pop(0)
    self._processMessages(message)

  def processMessages(self):
    'process messages. replace with your own function.'
    pass

  def savebin(self,m):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d")
    l = array([len(m)],dtype='>i4').tostring()
    with open(self.triglogpath+ts+self.triglogext,'ab') as f:
      f.write(l)
      f.write(m)

  def savetxt(self,m):
    t = datetime.datetime.utcnow()
    ts = datetime.datetime.utcnow().strftime("%Y%m%d")
    with open(self.evntlogpath+ts+self.evntlogext,'a') as f:
      f.write(t.isoformat()[:-3]+'Z ')
      f.write(m+'\n')

  def _processMessages(self,lastmessage):
    msglock.acquire()
    m = lastmessage
    mtype = m[:1].decode()
    if mtype in ['T','P'] and self.logit:
      self.savebin(m)
    if mtype in ['<'] and self.logit:
      self.savetxt(m.decode())
    if mtype in self._procfuncs:
      try:
        self._lastMessage = self._procfuncs[mtype](m)
        if self._verbose: self.log.info(self._lastMessage)
      except Exception as msg:
        if self._verbose: self.log.error(' Unknown message {m} \n*************\n{msg}\n*************\n'.format(m=m,msg=msg))
        msglock.release()
        return
    elif mtype in ['K']:
      msglock.release()
      return
    else:
      if self._verbose: self.log.debug(' Unknown message {m}'.format(m=m))
      msglock.release()
      return
    self.processMessages()
    msglock.release()

  def subscribeToActiveMQ(self,destination=None,ID=None,usr=None,passwd=None,ack='auto'):
    if not destination: destination = self.subscribeTo
    if not ID: ID = self.id
    if not usr: usr = self.usr
    if not passwd: passwd = self.passwd
    if not self.conn.is_connected(): return 0
    self.conn.subscribe(destination=destination, id=ID, ack=ack)
    self.SUBSCRIBES[ID]=destination
    if self._verbose: self.log.debug('subscribed to {destination}'.format(destination=destination))
    return 1

  def unsubscribeToActiveMQ(self,ID=None):
    if not ID: ID = self.id
    self.conn.unsubscribe(ID)
    self.SUBSCRIBES.pop(ID)
    return 1

  def disconnectToActiveMQ(self):
    if self._verbose: self.log.debug('Disconnecting from server...')
    self.conn.disconnect()
    return 1

def getDMxmlmsg(Eid,mag,lat,lon,depth,delay,msgcat='test'):
  now = datetime.datetime.utcnow()
  T = (now-datetime.timedelta(0,delay)).isoformat()[:-3]
  xmlexampl ='''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<event_message alg_vers="2.0.11 2014-04-08" category="'''+msgcat+'''" instance="./dm@eew2" message_type="new" orig_sys="elarms" timestamp="'''+now.isoformat()[:-3]+'''Z" version="0">

  <core_info id="'''+Eid+'''">
    <mag units="Mw">'''+str(mag)+'''</mag>
    <mag_uncer units="Mw">0.3982</mag_uncer>
    <lat units="deg">'''+str(lat)+'''</lat>
    <lat_uncer units="deg">0.1283</lat_uncer>
    <lon units="deg">'''+str(lon)+'''</lon>
    <lon_uncer units="deg">0.1283</lon_uncer>
    <depth units="km">'''+str(depth)+'''</depth>
    <depth_uncer units="km">1.0000</depth_uncer>
    <orig_time units="UTC">'''+T+'''Z</orig_time>
    <orig_time_uncer units="sec">2.5177</orig_time_uncer>
    <likelihood>0.9091</likelihood>
  </core_info>

</event_message>'''
  return xmlexampl


def getE2xmlmsg(Eid,mag,lat,lon,depth,delay,msgcat='test'):
  now = datetime.datetime.utcnow()
  T = (now-datetime.timedelta(0,delay)).isoformat()[:-3]
  xmlexampl ='''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<event_message alg_vers="2.0.11 2014-04-08" category="'''+msgcat+'''" instance="./E2@eew2" message_type="new" orig_sys="elarms" timestamp="'''+now.isoformat()[:-3]+'''Z" version="3">

  <core_info id="'''+Eid+'''">
    <mag units="Mw">'''+str(mag)+'''</mag>
    <mag_uncer units="Mw">0.3982</mag_uncer>
    <lat units="deg">'''+str(lat)+'''</lat>
    <lat_uncer units="deg">0.1283</lat_uncer>
    <lon units="deg">'''+str(lon)+'''</lon>
    <lon_uncer units="deg">0.1283</lon_uncer>
    <depth units="km">'''+str(depth)+'''</depth>
    <depth_uncer units="km">1.0000</depth_uncer>
    <orig_time units="UTC">'''+T+'''Z</orig_time>
    <orig_time_uncer units="sec">2.5177</orig_time_uncer>
    <likelihood>0.9091</likelihood>
    <num_stations>5</num_stations>
  </core_info>

</event_message>'''
  return xmlexampl

# writer class for connecting to activeMQ
class AMQWriter(object):
  def __init__(self,dest='/topic/eew.sys.dm.data',usr='decimod',passwd='decimod',name='writer',id=1,verbose=False,loglevel='CRITICAL',host_and_ports=[('localhost',61613)]):
    self.MESSAGES = []
    self.maxmessages=200
    self.dest=dest
    self.name=name
    self.usr=usr
    self.passwd=passwd
    self.id=id
    self._verbose=verbose
    self.host_and_ports = host_and_ports
    self.log = logging.getLogger('AMQ_{name}'.format(name=name))
    self.log.setLevel(loglevel)

  def on_disconnected(self):
    if self._verbose: self.log.debug(' Disconnected.')

  def on_error(self, headers, message):
    self.log.error(' received an error {message}'.format(message=message))

  def on_message(self, headers, message):
    'process messages. replace with your own function.'
    pass

  def connectToActiveMQ(self):
    self.conn = stomp.Connection(host_and_ports=self.host_and_ports)
    self.conn.set_listener(self.name, self)
    self.conn.start()
    self.conn.connect(self.usr,self.passwd)

  def disconnectToActiveMQ(self):
    self.conn.disconnect()

  def sendActiveMQmsg(self,body,dest='/topic/eew.sys.dm.data'):
    self.conn.send(destination=dest,body=body)
