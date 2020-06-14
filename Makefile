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

CC = gcc
CCFLAGS = -O2 -Wall
LIBFLAGS = -lm
sysswig := $(shell which swig)
PYINCLUDE := $(shell python3.7-config --includes)

all: ElViSCUtils
  
ElViSCUtils:
	$(CC) $(CCFLAGS) geodesic.c ElViSCUtils.c -o ElViSCUtils -lm
ifeq (swig,$(findstring swig,$(sysswig)))  
	swig -python ElViSCUtils.i
	$(CC) $(CCFLAGS) -c geodesic.c ElViSCUtils.c $(LIBFLAGS) ElViSCUtils_wrap.c $(PYINCLUDE) -fPIC
	$(CC) $(CCFLAGS) -shared ElViSCUtils.o geodesic.o ElViSCUtils_wrap.o -o _ElViSCUtils.so $(LIBFLAGS)
	@mkdir -p log
endif

clean:
	rm -r *.o *_wrap.c *.so *.pyc ElViSCUtils.py ElViSCUtils

  
