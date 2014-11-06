#/*##########################################################################
# Copyright (C) 2004-2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"
__version__ = '0.0'
import glob
import os
import distutils.sysconfig
from distutils.core import setup
data_files = [(os.path.join(distutils.sysconfig.get_python_lib(),"RixsTool", "ui"),
               glob.glob(os.path.join("RixsTool","ui","*")))]
distribution = setup(
    name="RixsTool",
    version= __version__,
    description = "Here be short desciption",
    author = __author__,
    author_email="tonn.ruter@esrf.fr",
    license= "GPL - Please read LICENSE.GPL for details",
    url = "https://github.com/tonnrueter/RixsTool",
    long_description = "Here be long description",
    platforms='any',
    data_files=data_files,
    packages=['RixsTool', "RixsTool.widgets"]
)
