# ElViS - ElarmS Visualization System
### An application for monitoring ElarmS system
Elarms is an Earthquake Early Warning System (EEWS), developed at Berkeley Seismological Lab (http://seismo.berkeley.edu/).
This tool is aimed for visually monitoring the ElarmS system.<br>
Created by Ran Novitsky Nof (ran.rnof.info), 2014.  
![screenshot](screentshot.jpg)
#### DEPENDENCIES:
-  swig - http://swig.org

python (tested on 2.7) modules:

-   numpy - http://numpy.org
-   obspy - http://obspy.org
-   matplotlib - http://matplotlib.org
-   PyQt4 - http://www.riverbankcomputing.com
-   stomp - https://github.com/jasonrbriggs/stomp.py

C external software (included as c files):

-   geodesic - http://geographiclib.sourceforge.net/html/C/

#### INSTALL:
  on terminal at main directory, run:
  ```
  make
  ```

#### USAGE:
<pre>
ElViS.py [-h] [cfgfile]

positional arguments:  
  cfgfile     Configuration file.

optional arguments:  
  -h, --help  show this help message and exit
</pre>
#### LICENSE:
  ElViS is free software: you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
