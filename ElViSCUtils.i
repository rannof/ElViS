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

%module ElViSCUtils
%include "typemaps.i"
%include "carrays.i"

%typemap(varout) double[ANY] {
  int i;
  //$1, $1_dim0, $1_dim1
  $result = PyList_New($1_dim0);
  for (i = 0; i < $1_dim0; i++) {
    PyObject *o = PyFloat_FromDouble((double) $1[i]);
    PyList_SetItem($result,i,o);
  }
}

%{
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "ElViSCUtils.h"
#include "geodesic.h"
double lons[361],lats[361];
%}
double lons[361],lats[361];
extern int initgeod();
extern int initlines(double *INPUT,double *INPUT);
extern void wave(double *INPUT);
extern void distaz_geo(double *INPUT,double *INPUT, double *INPUT ,double *INPUT,double *OUTPUT,double *OUTPUT);
extern void geo_to_km(double *INPUT, double *INPUT, double *INPUT, double *INPUT,double *OUTPUT, double *OUTPUT);

