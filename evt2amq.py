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

import sys,os,threading
import stomp,datetime,zlib
from numpy import frombuffer,dtype,array, zeros
from xml.dom import minidom
import argparse
import logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

msglock = threading.Lock()

if sys.hexversion >= 0x03000000:  # Python 3+
  PY3 = True
else:
  PY3 = False

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

# PARAMETERS
HOST = 'localhost'
PORT = 61613
VERBOSE = True
LOG_LEVEL = 'DEBUG'
TOPIC='/topic/eew.sys.dm.test'
USER='decimod'
PASSWORD='decimod'
NAME='writer'
AUTO_DECODE=False

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''ActiveMQ Event generator''',
    epilog='''Created by Ran Novitsky Nof (ran.nof@gmail.com), 2019 @ GSI''')
group1 = parser.add_argument_group('Connection', 'AMQ connection parameters')
group1.add_argument('-H', '--host', metavar='HOST', help='AMQ server address. Default: {HOST}'.format(HOST=HOST), default=HOST, type=str)
group1.add_argument('-p', '--port', metavar='PORT', help='AMQ server listen on port PORT. Default: {PORT}'.format(PORT=PORT), default=PORT, type=int)
group1.add_argument('--name', help='Name of writer. Default: {NAME}'.format(NAME=NAME),default=NAME)
group1.add_argument('--user', help='AMQ server user',default=USER)
group1.add_argument('--password', help='AMQ server password',default=PASSWORD)
group1.add_argument('--auto_decode', action='store_true', default=AUTO_DECODE, help='Automatically decode message. Dafault: {AUTO_DECODE}'.format(AUTO_DECODE=AUTO_DECODE))
group1.add_argument('--topic',help='Topic to send message to. Must start with "/topic/", default={TOPIC}'.format(TOPIC=TOPIC),default=TOPIC)
group1.add_argument('-t','--test',action='store_true',default=False,help='Test only. Will connect to server but message is sent to stdout')
group2 = parser.add_argument_group('Earthquake', 'Earthquake message parameters')
group2.add_argument('-c','--category',choices=['live','test','excercise'],default='test',help='Message category. Dafult: test')
group2.add_argument('--ver',type=int,default=0,help='Message version. 0 for new event. Default: 0')
group2.add_argument('--EID',type=str,default='TEST',help='Event ID. DEfault: TEST')
group2.add_argument('-m','--mag',type=float,default=5.0,help='Event Magnitude. Default: 5')
group2.add_argument('--lat',type=float,default=32.5,help='Event Latitude. Default: 32.5')
group2.add_argument('--lon',type=float,default=35.0,help='Event longitude. Default: 35.0')
group2.add_argument('--depth',type=float,default=8.0,help='Event Depth. Default: 8.0')
group2.add_argument('-d','--delay',type=float,default=0,help='Event report delay in seconds. Origin time will be [delay] seconds before current time. Default: 0')
group3 = parser.add_argument_group('Logging', 'Verbosity level')
group3.add_argument('-v', help='verbose - print messages to screen?', action='store_true', default=VERBOSE)
group3.add_argument('-l', '--log_level', choices=_LOG_LEVEL_STRINGS, default=LOG_LEVEL,
                    help="Log level (Default: {LOG_LEVEL}). see Python's Logging module for more details".format(LOG_LEVEL=LOG_LEVEL))



def getmsg(category='test', hostname=None, timestamp=None, ver=0, EID='TEST', mag=5.0, magu='0.5', lat=32.5, latu=0.2, lon=35.0, lonu=0.25, depth=8.0,depthu=1.0,OT=None, delay=0, OTu='0.01', likelihood=0.991,nstations=4):
  if timestamp is None:
    timestamp = (datetime.datetime.utcnow() - datetime.timedelta(0,delay)).isoformat()[:-3]
  else:
    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f').isoformat()[:-3]
  if OT is None:
    OT = (datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f') - datetime.timedelta(0,delay)).isoformat()[:-3] 
  else:
    OT = datetime.datetime.strptime(OT, '%Y-%m-%dT%H:%M:%S.%f').isoformat()[:-3]
  if hostname is None:
    hostname = os.uname()[1]
  if ver==0:
    msgtype='new'
  else:
    msgtype='update'
  xmlmsg = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<event_message alg_vers="2.0.26 2017-04-10" category="{category}" instance="dm@{hostname}" message_type="{msgtype}" orig_sys="dm" ref_id="0" ref_src="" timestamp="{timestamp}Z" version="{ver}">

  <core_info id="{EID}">
    <mag units="Mw">{mag}</mag>
    <mag_uncer units="Mw">{magu}</mag_uncer>
    <lat units="deg">{lat}</lat>
    <lat_uncer units="deg">{latu}</lat_uncer>
    <lon units="deg">{lon}</lon>
    <lon_uncer units="deg">{lonu}</lon_uncer>
    <depth units="km">{depth}</depth>
    <depth_uncer units="km">{depthu}</depth_uncer>
    <orig_time units="UTC">{OT}Z</orig_time>
    <orig_time_uncer units="sec">{OTu}</orig_time_uncer>
    <likelihood>{likelihood}</likelihood>
    <num_stations>{nstations}</num_stations>
  </core_info>

  <contributors>
    <contributor alg_instance="./E2r@EEWS" alg_name="elarms" alg_version="3.1.3-2018-08-28" category="live" event_id="98" version="3"/>
  </contributors>

</event_message>'''.format(category=category, hostname=hostname, msgtype=msgtype, timestamp=timestamp, ver=ver, EID=EID, mag=mag, magu=magu, lat=lat, latu=latu, lon=lon, lonu=lonu, depth=depth,depthu=depthu,OT=OT,OTu=OTu, likelihood=likelihood,nstations=nstations)
  return xmlmsg.encode()


 
# writer class for connecting to activeMQ
class AMQWriter(object):
  def __init__(self,topic='/topic/eew.sys.dm.data',usr='decimod',passwd='decimod',name='writer',id=1,verbose=False,loglevel='CRITICAL',auto_decode=False,host_and_ports=[('localhost',61613)],test=False):
    self.topic=topic
    self.name=name
    self.usr=usr
    self.passwd=passwd
    self.id=id
    self.test = test
    self._verbose=verbose
    self.host_and_ports = host_and_ports
    self.log = logging.getLogger('AMQ_{name}'.format(name=name))
    self.log.setLevel(loglevel)
    self.conn = stomp.Connection(host_and_ports=host_and_ports,auto_decode=auto_decode)
    self.conn.set_listener(self.name, self)
    self.conn.start()

  def on_disconnected(self):
    if self._verbose: self.log.debug('Disconnected.')

  def on_error(self, headers, message):
    self.log.error('Received an error {message}'.format(message=message))

  def on_message(self, headers, message):
    'process messages. replace with your own function.'
    pass

  def connectToActiveMQ(self):
    if not self.conn.is_connected(): 
      if self._verbose: self.log.debug('Trying to Connect to AMQ server')
      self.conn.connect(self.usr,self.passwd,wait=True)
    else:
      if self._verbose: self.log.warning('AMQ server already connected')

  def on_connecting(self,host_and_port):
    host,port = self.conn.transport.current_host_and_port
    if self._verbose: self.log.debug('Connected to '+':'.join([host,str(port)]))

  def disconnectToActiveMQ(self):
    if self.conn.is_connected(): 
      if self._verbose: self.log.debug('Trying to Disconnect from AMQ server')
      self.conn.disconnect()

  def sendActiveMQmsg(self,body=None,topic=None):
    host,port = self.conn.transport.current_host_and_port
    if topic is None:
      topic = self.topic
    if self._verbose: 
      self.log.debug('Sending message to '+':'.join([host,str(port)]))
      self.log.debug('Message:\n{body}'.format(body=body))
    if not self.test:
      self.conn.send(destination=topic,body=body)
    else:
      self.log.debug('Test mode, no actual message was sent to server')

def main(args):
  AMQargs = {a.dest:getattr(args,a.dest,None) for a in group1._group_actions + group3._group_actions}
  amq = AMQWriter(**AMQargs)
  amq.connectToActiveMQ()
  EQargs = {a.dest:getattr(args,a.dest,None) for a in group2._group_actions}
  body = getmsg(**EQargs)
  amq.sendActiveMQmsg(body)
  amq.disconnectToActiveMQ()

if __name__ == '__main__':
  args = parser.parse_args()
  main(args)
