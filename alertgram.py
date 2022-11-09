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

# By Ran Novitsky Nof @ GSI, 2019
# ran.nof@gmail.com

import requests
import urllib
import logging
log = logging.getLogger('EPICMAil')

# Telegram credentials file (Bot token and chat ID)
# Follow instruction on Telegram site to create a bot and obtain token and chat ID
# see here some easy instructions: https://towardsdatascience.com/how-to-write-a-telegram-bot-with-python-8c08099057a8
TGCREDS = 'telegram.dat'

ALERTBODY = """This is a {category} message!
Magnitude   : {mag}
Origin-Time : {ot}
Alert-Time  : {timestamp}
Lat/Long    : {lat} , {lon}

Alert ID {eventid} from {instance}:
   
This is an initial estimate of earthquake parameters, based on a very little information.
PLEASE DO NOT FORWARD THIS MESSAGE!!!

Google Map:
https://www.google.com/maps/place/{lat}N+{lon}E/@{lat},{lon},8z

Earthquake information:
http://udim.koeri.boun.edu.tr/zeqmap/hgmmapen.asp


You have received this message because you listed up for EPIC initial alerts.
Please contact Süleyman Tunç for any questions.

Sent by Süleyman's bot
"""

class tgdaemon(object):
    def __init__(self, creds=TGCREDS):
        self.token = None
        self.chat_id = None
        try:
            cred = {}
            with open(TGCREDS,'r') as f:
                exec(f.read(),None, cred)
                if 'bot_chatID' in cred and 'bot_token' in cred:
                    self.token = cred['bot_token']
                    self.chat_id = cred['bot_chatID']
                else:
                    raise(AttributeError('Missing Telegram bot parameters bot_chatID and bot_token'))
        except Exception as ex:
            log.error(f"Can't read {TGCREDS} for telegram messages: {ex}")
        log.info('Telegram daemon is initialize')


    def body(self, alert):
        return ALERTBODY.format(instance=alert.instance, eventid=alert.Eid, placeholder=" "*(len(str(alert.Eid))-2), category=alert.category, mag=alert.mag, nT=int(alert.num_stations), ot=alert.orig_time, lat=alert.lat, lon=alert.lon, timestamp=alert.msgtime)

    def sendalert(self, alert):
        log.info('Got alert: {alert}'.format(alert=alert))
        # Create telegram with alert message
        msg = urllib.parse.quote(self.body(alert), safe='')
        send_text = f'https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.chat_id}&parse_mode=Markdown&text={msg}'
        # send telegram message
        log.info('Sending alert message to telegram')
        try:
            if self.token is None or self.chat_id is None:
                raise(RuntimeError('Missing Telegram ChatID or bot token'))
                response = requests.get(send_text)
            if response.ok:
                log.info('Telegram sent.')
            else:
                raise(RuntimeError(response.reason))
        except Exception as EX:
            log.warning('Alert telegram warning: {EX}'.format(EX=EX))

def test():
    import pandas as pd
    alerts = pd.read_csv('alerts.csv')
    alerts.loc[0] = [145, 0, 31.9853, 35.2397, 8.0000, 2.7360, "2019-06-29T05:43:18.758Z", 0.9256, 5, "dm@sandbox", "test", "new", "2019-06-29T05:43:30.159Z"]
    alert = alerts.loc[0]
    md = tgdaemon()
    return alert, md

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d | %(name)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',level='DEBUG')
    alert, md = test()
    md.sendalert(alert)
