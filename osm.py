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
import numpy as np
import scipy.misc
from StringIO import StringIO
import os
from httplib2 import Http
from PIL import Image
import matplotlib
# util class for Open Street Map
class OSM(object):
  # constants and defaults
  cashedtiles={}
  tilesorder = []
  latmax = 90.0
  latmin = -90.0
  lonmax = 180.0
  lonmin = -180.0
  maxlevel=17
  maxtilecash=500
  def __init__(self,ax,tileurl="http://otile1.mqcdn.com/tiles/1.0.0/osm"):
    # constants and defaults
    self.ax = ax
    self.http = Http()
    self.tileurl = tileurl
  def plotbgmap(self,datafile,limits=[latmin,latmax,lonmin,lonmax]):
    y0,y1,x0,x1=limits
    data = scipy.misc.fromimage(Image.open(datafile))
    im = matplotlib.image.AxesImage(self.ax)
    im.set_data(data)
    im._extent = [x0,x1,y0,y1]
    self.ax.images.append(im)
  def relim(self,x0,x1,y0,y1):
    self.ax.set_ylim(y0,y1)
    self.ax.set_xlim(x0,x1)
    self.ax.apply_aspect()
  def relimcorrected(self,x0,x1,y0,y1):
    x0,x1 = self.checklonrange(x0,x1)
    y0,y1 = self.checklatrange(y0,y1)
    self.relim(x0,x1,y0,y1)
  def checklonrange(self,lonmin,lonmax):
    # The bounds are choosen such that they give the correct results up
    # to zoom level 30 (zoom levels up to 18 actually make sense):
    # lon2tilex(-180.0, 30) == 0
    # lon2tilex(179.9999999, 30) == 1073741823 == 2**30 - 1
    if lonmin < -180.0: lonmin = -180.0
    if lonmin > 179.9999999: lonmin = 179.9999999
    if lonmax < -180.0: lonmax = -180.0
    if lonmax > 179.9999999: lonmax = 179.9999999
    return lonmin, lonmax
  def checklatrange(self,latmin,latmax):
    # The bounds are choosen such that they give the correct results up
    # to zoom level 30 (zoom levels up to 18 actually make sense):
    # lat2tiley(85.0511287798, 30) == 0
    # lat2tiley(-85.0511287798, 30) == 1073741823 == 2**30 - 1
    if latmin < -85.0511287798: latmin = -85.0511287798
    if latmin > 85.0511287798:  latmin = 85.0511287798
    if latmax < -85.0511287798: latmax = -85.0511287798
    if latmax >85.0511287798:   latmax = 85.0511287798
    return latmin,latmax
  def lon2tilex(self,lon,zoom):
    return int(((lon+180)/360.0*2**zoom))
  def tilex2lims(self,tilex,zoom):
    return tilex*360.0/2.0**zoom-180.0,(tilex+1)*360.0/2.0**zoom-180.0
  def lat2tiley(self,lat,zoom):
    lata = lat*np.pi/180.0
    return int(((1-np.log(np.tan(lata)+1.0/np.cos(lata))/np.pi)/2.0*2**zoom))
  def tiley2lims(self,tiley,zoom):
    return np.degrees(np.arctan(np.sinh(np.pi*(1-2*(tiley+1)/2.0**zoom)))),np.degrees(np.arctan(np.sinh(np.pi*(1-2*tiley/2.0**zoom))))
  def tiles2lims(self,tilex,tiley,zoom):
    return np.append(self.tiley2lims(tiley,zoom),self.tilex2lims(tilex,zoom))
  def tile2path(self,tilex,tiley,zoom):
    return "%s/%d/%d/%d.png"%(self.tileurl,zoom,tilex,tiley)
  def tilepath2zoomxy(self,tile):
    zoom,tilex,tiley = os.path.splitext(tile)[0].split('/')[-3:]
    return int(tilex),int(tiley),int(zoom)
  def gettiles(self,lonmin,lonmax,latmin,latmax):
    latmin,latmax = self.checklatrange(latmin,latmax)
    lonmin,lonmax = self.checklonrange(lonmin,lonmax)
    w,h=(self.ax.figure.canvas.width(),self.ax.figure.canvas.height())
    for i in range(self.maxlevel):
      xtiles = list(set([self.lon2tilex(lon,i) for lon in [lonmin,lonmax]]))
      ytiles = list(set([self.lat2tiley(lat,i) for lat in [latmin,latmax]]))
      if len(xtiles)==2 and len(ytiles)==2 and (abs(np.diff(xtiles)[0])>round(w/256) or \
        abs(np.diff(ytiles)[0])>(h/256)):
        break
    mintilex = self.lon2tilex(lonmin,i)
    maxtilex = self.lon2tilex(lonmax,i)
    mintiley = self.lat2tiley(latmax,i)
    maxtiley = self.lat2tiley(latmin,i)
    tiles = []
    for x in range(mintilex,maxtilex+1):
      for y in range(mintiley,maxtiley+1):
        tiles.append(self.tile2path(x,y,i))
    return tiles
  def plottiles(self,tiles):
    for t in tiles:
      if not t in self.cashedtiles:
        datafile = StringIO(self.http.request(t)[1])
        self.cashedtiles[t]=datafile
        self.tilesorder.append(t)
        if len(self.tilesorder)>self.maxtilecash:
          old = self.tilesorder.pop(0)
          self.cashedtiles.pop(old)
      else:
        self.cashedtiles[t].seek(0)
      limits = self.tiles2lims(*self.tilepath2zoomxy(t))
      self.plotbgmap(self.cashedtiles[t],limits)
