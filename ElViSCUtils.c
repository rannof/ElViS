/**********************************************************************************
*    Copyright (C) by Ran Novitsky Nof                                            *
*                                                                                 *
*    This file is part of ElViS                                                   *
*                                                                                 *
*    ElViS is free software: you can redistribute it and/or modify                *
*    it under the terms of the GNU Lesser General Public License as published by  *
*    the Free Software Foundation, either version 3 of the License, or            *
*    (at your option) any later version.                                          *
*                                                                                 *
*    This program is distributed in the hope that it will be useful,              *
*    but WITHOUT ANY WARRANTY; without even the implied warranty of               *
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                *
*    GNU Lesser General Public License for more details.                          *
*                                                                                 *
*    You should have received a copy of the GNU Lesser General Public License     *
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.        *
***********************************************************************************/

#include "ElViSCUtils.h"
// Using GeographicLib (http://geographiclib.sourceforge.net/)
// to compute distance between points on the globe
// and points at a given distance around a point.
// basically expose GeographicLib to swig and finally to Python.

double a = 6378137, f = 1/298.257223563; /* WGS84 */
struct geod_geodesic g; // geoid
struct geod_geodesicline lines[361]; // hold lines in a 360 deg around a point
double lons[361],lats[361]; // holds wave location around a point
int azimuth; // for indexing

int initgeod()
{// init the geoid.
  geod_init(&g, a, f);
  return(1);
}

int initline(struct geod_geodesicline *l,double *lon,double *lat,int *azimuth)
{// init a line from point to direction
  double az;
  az = (double)*azimuth;
  geod_lineinit(l, &g, *lat, *lon, az,0);
  return(1);
}

int initlines(double *lon,double *lat)
{// init a set of lines around a point
  for(azimuth=0;azimuth<361;azimuth++)
    initline(&lines[azimuth],lon, lat, &azimuth);
  return(1);
}

void wave(double *dist)
{// calculate wave location around a point at a distance. one must init geoid and lines before use.
  for(azimuth=0;azimuth<361;azimuth++)
	//convert dist to km...
    geod_genposition(&lines[azimuth], 0, *dist*1000.,&lats[azimuth],&lons[azimuth],0,0,0,0,0,0);
}

void geo_to_km(double *lon1,double *lat1,double *lon2,double *lat2,double* dist,double* azm)
{// Solve the inverse geodesic problem.
  geod_inverse(&g, *lat1, *lon1, *lat2,*lon2,dist,azm,0);
  *dist=*dist/1000.; // convert to km
}

void distaz_geo(double *olon,double *olat,double *dist,double *azimuth,double *lon,double *lat)
{ // Solve the direct geodesic problem.
  geod_direct(&g, *olat, *olon, *azimuth, *dist*1000, lat, lon, 0);
}


int main(int argc,char *argv[])
{// just for testing
  double lon,lat,azimuth,maxdist,glon,glat;
  int i;
  if (argc<5)
  {
	  printf("Usage: ElVisCUtils lon lat azimuth distance (km)\n");
	  return 0;
  }
  lon=atof(argv[1]);
  lat=atof(argv[2]);
  azimuth=atof(argv[3]);
  maxdist=atof(argv[4]);
  initlines(&lon,&lat);
  distaz_geo(&lon,&lat,&maxdist,&azimuth,&glon,&glat);
  printf("%lf %lf\n",glon,glat);
  geo_to_km(&lon,&lat,&glon,&glat,&maxdist,&azimuth);
  printf("%lf %lf\n",maxdist,azimuth);
  wave(&maxdist);
  for(i=0;i<361;i++)
    printf("%lf %lf\n",lons[i],lats[i]);
  return 0;
}
