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
#
#
# based on a module of Qingkai Kong, qingkai.kong@gmail.com Date: 2014-10-21
#
#
#
import numpy as np
import re,math
from urllib import urlopen
import ElViSCUtils as cutil # must be compiled with swig
# from User Display
P_WAVE_VELOCITY = 6.10
S_WAVE_VELOCITY = 3.55


def eta_userDisplay(stlo, stla, evlo, evla, evdp, evt0, tstep):
    '''
    function to get the warning time based on the userdisplay model
    '''
    epi_val = cutil.geo_to_km(evlo, evla, stlo, stla)[0] # epicentral distance in km
    hypo_dist = np.sqrt(epi_val**2 + evdp**2) # hypocentral distance in km
    timediff = (tstep - evt0).total_seconds()
    eta = hypo_dist/S_WAVE_VELOCITY - timediff
    return eta

def wavePoints(lon0,lat0,dt,v):
    '''
    Get wave circle points
    '''
    cutil.initlines(lon0,lat0)
    cutil.wave(dt*v)
    return cutil.cvar.lons,cutil.cvar.lats


def get_coeffs_CH2007(IM, ZH, PS, RS):
    if IM == 'PGA' and ZH =='H' and PS == 'P' and RS == 'R':
        a = 0.72
        b=  3.3e-3
        c1= 1.6
        c2= 1.05
        d = 1.2
        e =-1.06
        sigma=0.31

    elif IM == 'PGA' and ZH =='H' and PS == 'P' and RS == 'S':
        a=0.74
        b= 3.3e-3
        c1= 2.41
        c2= 0.95
        d = 1.26
        e =-1.05
        sigma= 0.29

    elif IM == 'PGV' and ZH =='H' and PS == 'P' and RS == 'R':
        a=0.80
        b=8.4e-4
        c1=0.76
        c2=1.03
        d=1.24
        e=-3.103
        sigma=0.27

    elif IM == 'PGV' and ZH =='H' and PS == 'P' and RS == 'S':
        a=0.84
        b=5.4e-4
        c1=1.21
        c2=0.97
        d= 1.28
        e= -3.13
        sigma=0.26

    elif IM == 'FD' and ZH =='H' and PS == 'P' and RS == 'R':
        a=0.95
        b=1.7e-7
        c1=2.16
        c2=1.08
        d=1.27
        e=-4.96
        sigma=0.28

    elif IM == 'FD' and ZH =='H' and PS == 'P' and RS == 'S':
        a=0.94
        b=5.17e-7
        c1=2.26
        c2=1.02
        d=1.16
        e=-5.01
        sigma=0.3

    elif IM == 'PGA' and ZH =='H' and PS == 'S' and RS == 'R':
        a=0.733
        b=7.216e-4
        d=1.48
        c1=1.16
        c2=0.96
        e=-0.4202
        sigma=0.3069

    elif IM == 'PGA' and ZH =='H' and PS == 'S' and RS == 'S':
        a=0.709
        b=2.3878e-3
        d=1.4386
        c1=1.722
        c2=0.9560
        e=-2.4525e-2
        sigma=0.3261

    elif IM == 'PGV' and ZH =='H' and PS == 'S' and RS == 'R':
        a=0.861988
        b=5.578e-4
        d=1.36760
        c1=0.8386
        c2=0.98
        e=-2.58053
        sigma=0.2773

    elif IM == 'PGV' and ZH =='H' and PS == 'S' and RS == 'S':
        a=0.88649
        b=8.4e-4
        d=1.4729
        c1=1.39
        c2=0.95
        e=-2.2498
        sigma=0.3193

    elif IM == 'FD' and ZH =='H' and PS == 'S' and RS == 'R':
        a=1.03
        b=1.01e-7
        c1=1.09
        c2=1.13
        d=1.43
        e=-4.34
        sigma=0.27

    elif IM == 'FD' and ZH =='H' and PS == 'S' and RS == 'S':
        a=1.08
        b=1.2e-6
        c1=1.95
        c2=1.09
        d=1.56
        e=-4.1
        sigma=0.32

    elif IM == 'PGA' and ZH =='Z' and PS == 'P' and RS == 'R':
        a=0.74
        b=4.01e-3
        c1=1.75
        c2=1.09
        d=1.2
        e=-0.96
        sigma=0.29

    elif IM == 'PGA' and ZH =='Z' and PS == 'P' and RS == 'S':
        a=0.74
        b=5.17e-7
        c1=2.03
        c2=0.97
        d=1.2
        e=-0.77
        sigma=0.31

    elif IM == 'PGV' and ZH =='Z' and PS == 'P' and RS == 'R':
        a=0.82
        b=8.54e-4
        c1=1.14
        c2=1.11
        d=1.36
        e=-2.90057
        sigma=0.26

    elif IM == 'PGV' and ZH =='Z' and PS == 'P' and RS == 'S':
        a=0.81
        b=2.65e-6
        c1=1.4
        c2=1.0
        d=1.48
        e=-2.55
        sigma=0.30

    elif IM == 'FD' and ZH =='Z' and PS == 'P' and RS == 'R':
        a=0.96
        b=1.98e-6
        c1=1.66
        c2=1.16
        d=1.34
        e=-4.79
        sigma=0.28

    elif IM == 'FD' and ZH =='Z' and PS == 'P' and RS == 'S':
        a=0.93
        b=1.09e-7
        c1=1.5
        c2=1.04
        d=1.23
        e=-4.74
        sigma=0.31

    elif IM == 'PGA' and ZH =='Z' and PS == 'S' and RS == 'R':
        a= 0.78
        b=2.7e-3
        c1=1.76
        c2=1.11
        d=1.38
        e=-0.75
        sigma=0.30

    elif IM == 'PGA' and ZH =='Z' and PS == 'S' and RS == 'S':
        a=0.75
        b=2.47e-3
        c1=1.59
        c2=1.01
        d=1.47
        e=-0.36
        sigma=0.30

    elif IM == 'PGV' and ZH =='Z' and PS == 'S' and RS == 'R':
        a=0.90
        b=1.03e-3
        c1=1.39
        c2=1.09
        d= 1.51
        e=-2.78
        sigma=0.25

    elif IM == 'PGV' and ZH =='Z' and PS == 'S' and RS == 'S':
        a=0.88
        b=5.41e-4
        c1=1.53
        c2=1.04
        d=1.48
        e=-2.54
        sigma=0.27

    elif IM == 'FD' and ZH =='Z' and PS == 'S' and RS == 'R':
        a=1.04
        b=1.12e-5
        c1=1.38
        c2=1.18
        d=1.37
        e=-4.74
        sigma=0.25

    elif IM == 'FD' and ZH =='Z' and PS == 'S' and RS == 'S':
        a=1.04
        b=4.92e-6
        c1=1.55
        c2=1.08
        d=1.36
        e=-4.57
        sigma=0.28
    return a,b,c1,c2,d,e,sigma

def CH2007(M,Rjb,IM,ZH,PS,RS,Sigma):
    # Cua and Heaton 2007 relationships
    # IM = {PGA, PGV, FD}, where FD = 3 sec high pass filtered displacement
    # ZH = {Z,H}, where Z=vertical, H=horizontal
    # PS = {P, S}, P=P-wave, S=S-wave
    # RS = {Rock, Soil}, where Rock is for sites w/ NEHRP class BC and above,
    # Soil is for sites w/ NEHRP class C and below

    # note: output units are PGA (cm/s/s), PGV (cm/s), FD (cm)
    # y is median ground motion level
    # up is median + sigma
    # low is median - sigma
    # sigma is in log10

    #global IM ZH PS RS
    R1=np.sqrt(Rjb**2 + 9)

    a,b,c1,c2,d,e,sigma = get_coeffs_CH2007(IM,ZH,PS,RS)

    if Sigma != 0:
        sigma=Sigma

    CM=c1*np.exp(c2*(M-5))*(math.atan(M-5)+1.4)
    log10Y= a*M - b*(R1+CM) - d*np.log10(R1+CM) + e
    logup=log10Y + sigma
    loglow=log10Y - sigma


    y=pow(10, log10Y)
    up=pow(10, logup)
    low=pow(10, loglow)

    return y,up,low,sigma, log10Y

def get_MMI_Worden_Eq3(logpga, logpgv):
    '''
    This is the first intensity relationship without distance correction in
    Worden et al. 2012 paper.

    The input is the logorithm of the pga and pgv, and the output is the final
    intensity based on the average of the MMIpga and MMIpgv.

    Paper: Probabilistic Relationships between Ground-Motion Parameters and Modified Mercalli Intensity in California 2012

    returns: MMI rounded to the closest integer and MMI not rounded
    '''
    if  logpga <= t1pga:
        MMIpga = c1pga+c2pga*logpga
    else:
        MMIpga=c3pga+c4pga*logpga

    if logpgv <= t1pgv:
        MMIpgv=c1pgv+c2pgv*logpgv
    else:
        MMIpgv=c3pgv+c4pgv*logpgv

    pga = 10**logpga
    pgv = 10**logpgv

    if pga > 0 and pgv >0:
        MMI=(MMIpga+MMIpgv)/2
    elif pga > 0:
        MMI = MMIpga
    elif pgv > 0:
        MMI = MMIpgv

    if (MMI < 1.5):
        result = 1.0
    elif MMI > 9.5:
        result = 10.0
    else:
        #here we round the MMI to the closest integer
        result = round(MMI)

    return result, MMI

def get_MMI_Worden_Eq6(logpga, logpgv, R, M):
    '''
    This is the second intensity relationship with distance and magnitude correction in
    Worden et al. 2012 paper

    The input is the logorithm of the pga and pgv, and the distance and magnitude, and
    the output is the final intensity based on the average of the MMIpga and MMIpgv.
    '''
    if  logpga <= t2pga:
        MMIpga = c1pga+c2pga*logpga+c5pga+c6pga*np.log10(R)+c7pga*M
    else:
        MMIpga = c3pga+c4pga*logpga+c5pga+c6pga*np.log10(R)+c7pga*M

    if logpgv <= t2pgv:
        MMIpgv = c1pgv+c2pgv*logpgv+c5pgv+c6pgv*np.log10(R)+c7pgv*M
    else:
        MMIpgv = c3pgv+c4pgv*logpgv+c5pgv+c6pgv*np.log10(R)+c7pgv*M

    MMI=(MMIpga+MMIpgv)/2

    if (MMI < 1.5):
        result = 1.0
    else:
        result = round(MMI)
    return result, MMI

def get_intensity(stla, stlo, evla, evlo, M, RS = 'R', IM = 'PGA', ZH = 'H', PS = 'S'):
    '''
    Function to get the intensity at your location, it returns
    (1) MMI_v - rounded MMI
    (2) MMI - not rounded MMI
    (3) d - the epicentral distance

    IM = 'PGA'    # IM = {PGA, PGV, FD}, where FD = 3 sec high pass filtered displacement
    ZH = 'H'      # ZH = {Z,H}, where Z=vertical, H=horizontal
    PS = 'S'      # PS = {P, S}, P=P-wave, S=S-wave
    RS = 'R'      # RS = {R, S}, R = Rock, S = Soil
    '''
    d = cutil.geo_to_km(stlo, stla, evlo, evla)[0]
    logpga = CH2007(M,d,'PGA',ZH,PS,RS,0)[-1]
    logpgv = CH2007(M,d,'PGV',ZH,PS,RS,0)[-1]
    MMI_v, MMI = get_MMI_Worden_Eq3(logpga, logpgv)
    #MMI_v = get_MMI_Worden_Eq6(logpga, logpgv, d, M)
    return MMI_v, MMI, d

########### coeffs for worden Eq3 and Eq6
c1pga= 1.78
c1pgv= 3.78
c2pga= 1.55
c2pgv= 1.47
c3pga= -1.60
c3pgv= 2.89
c4pga= 3.70
c4pgv= 3.16
c5pga = -0.91
c5pgv = 0.90
c6pga = 1.02
c6pgv = 0.00
c7pga = -0.17
c7pgv = -0.18
t1pga= 1.57
t1pgv= 0.53
t2pga= 4.22
t2pgv= 4.56
#####################################

# get current location
def getuserlatlon():
  'connects to the internet and get current location based on IP'
  try:
    data = str(urlopen('http://checkip.dyndns.com/').read())
    ip = re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    response = urlopen('http://api.hostip.info/get_html.php?ip='+ip+'&position=true').read()
    data = dict([l.split(':') for l in response.split('\n') if l])
    return float(data['Latitude']),float(data['Longitude']),data['City']
  except:
    return None,None,None
