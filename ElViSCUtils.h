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

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include "geodesic.h"

int initgeod();
//  Initialize the geoid of the geodesic module
//  OUTPUT:
//    g: a geoid initialized for wgs84 (global)

int initline(struct geod_geodesicline *l,double *lon,double *lat,int *azimuth);
// Initialize a geodesicline of the geodesic module
//  INPUT:
//    lon: Event longitude, East positive.
//    lat: Event latitude in decimal degrees, North positive.
//    azimuth: azimuath from event (lat,lon) in degrees.
//  OUTPUT:
//    l: geod_geodesicline variable initialized at point (lon,lat) and azimuth (azimuth)

int initlines(double *lon,double *lat);
// Initialize an array of geodesiclines for the geodesic module
// Uses initline to initialize each line of 360 directions
//  INPUT:
//    lon: Event longitude, East positive.
//    lat: Event latitude in decimal degrees, North positive.
//  OUTPUT:
//    lines[361]: an array of geod_geodesicline variables initialized at point (lon,lat) and 360 degrees. (global)

void wave(double *dist);
// Calculate array of points (lons,lats) around a point at a distance (dist)
// must have initlines initialized first.
// INPUT:
//   dist: distance from point in km.
// OUTPUT:
//   lons[360]: array of longitues, East positive.(global)
//   lats[360]: array of latitudes, North positive.(global)

void geo_to_km(double *lon1,double *lat1,double *lon2,double *lat2,double* dist,double* azm);
//  compute the distance and azimuth between two points.
//  INPUT:
//    lon1: Event longitude, East positive.
//    lat1: Event latitude in decimal degrees, North positive.
//    lon2: station longitude.
//    lat2: station latitude.
//  OUTPUT:
//    dist: epicentral distance in km.
//    azm : azimuth in degrees.


void distaz_geo(double *olon,double *olat,double *dist,double *azimuth,double *lon,double *lat);
//  compute latitude and longitude given a distance and azimuth from a geographic point (olat,olon).
//  INPUT:
//    olon:    longitude in decimal degrees, East positive.
//    olat:    latitude in decimal degrees, North positive.
//    dist:    distance from point (olat,olon) in km.
//    azimuth: azimuath between point (olat,olon) and (lat,lon) in degrees.
//  OUTPUT ARGUMENTS:
//    lon:    longitude in decimal degrees, East positive.
//    lat:    latitude in decimal degrees, North positive.

