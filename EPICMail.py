#!/usr/bin/env python3

# /**********************************************************************************
# *    Copyright (C) by Ran Novitsky Nof                                            *
# *                                                                                 *
# *    This file is part of ElViS                                                   *
# *                                                                                 *
# *    This is a free software: you can redistribute it and/or modify               *
# *    it under the terms of the GNU Lesser General Public License as published by  *
# *    the Free Software Foundation, either version 3 of the License, or            *
# *    (at your option) any later version.                                          *
# *                                                                                 *
# *    This program is distributed in the hope that it will be useful,              *
# *    but WITHOUT ANY WARRANTY; without even the implied warranty of               *
# *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                *
# *    GNU Lesser General Public License for more details.                          *
# *                                                                                 *
# *    You should have received a copy of the GNU Lesser General Public License     *
# *    along with this program.  If not, see <http://www.gnu.org/licenses/>.        *
# ***********************************************************************************/

# By Ran Novitsky Nof @ GSI, 2022
# ran.nof@gmail.com

import os
import sys
import signal
from amq2py import AMQListener
from alertgram import tgdaemon  # Needs Telergram bot credentials
from alertmail import maildaemon  # Needs a mail server relay
import asyncio
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d | %(name)s | %(levelname)s | %(message)s',
                              datefmt='%Y-%m-%dT%H:%M:%S')


# PARAMETERS
PID = '~/.epicmail.pid'  # Process ID file
AMQSERVER = '127.0.0.1'  # AMQ host url
AMQPORT = '61613'  # AMQ stomp port
AMQUSER = 'monitor'  # AMQ user
AMQPSWD = 'monitor'  # AMQ password
AMQTOPIC = '/topic/eew.sys.dm.data'  # AMQ Topic for system clients listen/write to
VERBOSE = True  # print to screen?
LOG_FILE = None  # save log to file?
LOG_LEVEL = 'DEBUG'  # logging level
log_name = 'EPICMAIL'  # logger name
log = logging.getLogger(log_name)  # set logger name
log.propagate = False

# parser
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''TADAM Client''',
    epilog='''Created by Ran Novitsky Nof (ran.nof@gmail.com), 2022 @ GSI''')
parser.add_argument('-H', '--host', help='ActiveMQ server URL', default=AMQSERVER)
parser.add_argument('-p', '--port', help='ActiveMQ port', type=int, default=AMQPORT)
parser.add_argument('-U', '--user', help="AMQ user", default=AMQUSER)
parser.add_argument('-P', '--password', help="AMQ user password", default=AMQPSWD)
parser.add_argument('--topic', help='Topic destination on the AMQ server', default=AMQTOPIC)
parser.add_argument('-v', '--verbose', help='verbose - print messages to screen?', action='store_true', default=VERBOSE)
parser.add_argument('-l', '--log_level', choices=_LOG_LEVEL_STRINGS, default=LOG_LEVEL,
                    help="Log level (Default: {LOG_LEVEL}). see Python's Logging module for more details".format(LOG_LEVEL=LOG_LEVEL))
parser.add_argument('--logfile', metavar='log file name', help='log to file', default=LOG_FILE)


class E2Mail:
    def __init__(self, host, port, topic, verbose, log_level, logfile, user, password):
        AMQListener.processMessages = self.processMessages
        self.host = host
        self.port = port
        self.topic = topic
        self.verbose = verbose
        self.log_level = log_level
        self.logfile = logfile
        self.user = user
        self.password = password
        self.amq = AMQListener(subscribeTo=self.topic, usr=self.user, passwd=self.password, name='EPIC2MAIL', ID=1, verbose=self.verbose, loglevel=self.log_level, host_and_ports=[(self.host, self.port)])
        self.telegram = tgdaemon()
        self.mail = maildaemon()
        self._running = False

    def processMessages(self):
        if self.amq._lastMessage.type == 'X':
            alert = self.amq._lastMessage
            if alert.msgtype == 'new':
                self.telegram.sendalert(alert)
                self.mail.sendalertmail(alert)

    async def run(self):
        if self.amq.connectToActiveMQ():
            if self.amq.subscribeToActiveMQ():
                self._running = True
        while self._running:
            await asyncio.sleep(1)

    def shutdown(self):
        self._running = False
        self.amq.unsubscribeToActiveMQ()
        self.amq.disconnectToActiveMQ()


async def shutdown(loop, signal=None, worker=None):
    """Cleanup tasks tied to the service's shutdown."""
    if signal is not None:
        log.info(f"Received exit signal {signal}...")
    if worker is not None:
        worker.shutdown()
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    [task.cancel() for task in tasks]
    if len(tasks):
        log.debug(f"Press ctrl-C again to exit or wait...")
    await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 60.0)
    loop.stop()


def set_logger(log, verbose=VERBOSE, log_level=LOG_LEVEL, logfile=LOG_FILE):
    if verbose:
        # create console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        log.setLevel(log_level)
        ch.setFormatter(formatter)
        if logging.StreamHandler not in [h.__class__ for h in log.handlers]:
            log.addHandler(ch)
        else:
            log.warning('log Stream handler already applied.')
    if logfile:
        # create file handler
        fh = TimedRotatingFileHandler(logfile,
                                      when='midnight',
                                      utc=True)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        if TimedRotatingFileHandler not in [h.__class__ for h in log.handlers]:
            log.addHandler(fh)
        else:
            log.warning('Log file handler already applied.')
        log.info(f'Log file is: {logfile}')
    else:
        log.debug(f'No Log file was set')


def lockfile_on(filename=PID):
    filename = os.path.expanduser(filename)
    currentpid = os.getpid()  # get pid
    if os.path.exists(filename):
        # get old pid
        with open(filename, 'r') as f:
            pid = f.read()
        # see if process is still running
        if pid and os.path.exists('/proc/'+pid):  # running - exit
            log.info("Prosses is running. No restarts for now. pid={}".format(pid))
            sys.exit(0)
    # no lock file or process ended unexpectedly: create new or update pid
    with open(filename, 'w') as f:
        f.write(str(currentpid))


def lockfile_off(filename=PID):
    filename = os.path.expanduser(filename)
    os.remove(filename)


if __name__=='__main__':
    lockfile_on()
    args = parser.parse_args()
    set_logger(log, args.verbose, args.log_level, args.logfile)
    loop = asyncio.get_event_loop()
    worker = E2Mail(**args.__dict__)
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda sig=s: asyncio.create_task(shutdown(loop, sig, worker)))
    try:
        loop.create_task(worker.run(), name='mainloop')
        loop.run_forever()
    finally:
        loop.close()
        logging.info('Done.')
    lockfile_off()
