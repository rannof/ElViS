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

import smtplib
import logging
#from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
log = logging.getLogger('EPICMAil')

# list of mail recipients
RECIPIENTS = []  # example: ['first@server', 'second@server']

TITLE = "EPIC ALERT {category}: M {mag:.2f}, {lat:.4f}, {lon:.4f}, {ot}, nT {nT}"
ALERTBODY = """EPIC Initial Alert ID {eventid} from {instance}:
This is a {category} message!
Magnitude:\t{mag}
Origin-Time:\t{ot}
Lat/long: \t{lat},{lon}
Alert-Time:\t{timestamp}
   
This is an initial estimate of earthquake parameters, based on a very little information.
PLEASE DO NOT FORWARD THIS MESSAGE!!!

Google Map:
https://www.google.com/maps/place/{lat}N+{lon}E/@{lat},{lon},8z

Earthquake information:
http://udim.koeri.boun.edu.tr/zeqmap/hgmmapen.asp


You have received this message because you listed up for EPIC initial alerts.
Please contact Süleyman Tunç for any questions.
"""

class maildaemon(object):
    def __init__(self, recipients=RECIPIENTS):
        self.recipients = recipients
        log.info('Mail daemon is initialize')

    def title(self, alert):
        return TITLE.format(category=alert.category, mag=float(alert.mag), lat=float(alert.lat), lon=float(alert.lon), ot=alert.orig_time, nT=int(alert.num_stations))

    def body(self, alert):
        return ALERTBODY.format(instance=alert.instance, eventid=alert.Eid, placeholder=" "*(len(str(alert.Eid))-2), category=alert.category, mag=alert.mag, nT=int(alert.num_stations), ot=alert.orig_time, lat=alert.lat, lon=alert.lon, timestamp=alert.msgtime)

    def sendalertmail(self, alert):
        log.info('Got alert: {alert}'.format(alert=alert))
        # Create email with alert message
        msg = MIMEMultipart()
        msg['Subject'] = self.title(alert)
        msg.attach(MIMEText(self.body(alert)))
        # send email
        log.info('Sending alert message to {}'.format(self.recipients))
        try:
            s = smtplib.SMTP('localhost')
            s.sendmail("EPIC", self.recipients, msg.as_string())
            s.quit()
            log.info('Mail sent.')
        except Exception as EX:
            log.warning('Alert mail warning: {EX}'.format(EX=EX))

def test():
    import pandas as pd
    alerts = pd.read_csv('alerts.csv')
    alerts.loc[0] = [145, 0, 31.9853, 35.2397, 8.0000, 2.7360, "2019-06-29T05:43:18.758Z", 0.9256, 5, "dm@sandbox", "test", "new", "2019-06-29T05:43:30.159Z"]
    alert = alerts.loc[0]
    md = maildaemon()
    return alert, md

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d | %(name)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',level='DEBUG')
    alert, md = test()
    md.sendalertmail(alert)
