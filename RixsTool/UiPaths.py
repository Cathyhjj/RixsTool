#/*##########################################################################
# Copyright (C) 2014 European Synchrotron Radiation Facility
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

import os
import os.path


class UiPaths(object):
    @staticmethod
    def abstractTitleToolBar():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'abtracttitletoolbar.ui')

    @staticmethod
    def alignmentFilterUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'alignmentfilter.ui')

    @staticmethod
    def bandPassFilterUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'bandpassfilter.ui')

    @staticmethod
    def bandPassFilterID32UiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'bandpassfilterID32.ui')

    @staticmethod
    def energyAlignmentUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'energyalignment.ui')

    @staticmethod
    def fileSystemBrowserUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'filesystembrowser.ui')

    @staticmethod
    def mainWindowUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'mainwindow_imageView.ui')

    @staticmethod
    def sumToolUiPath():
        relativeUiPath = os.path.join(os.path.dirname(__file__), 'ui')
        absolutePath = os.path.abspath(relativeUiPath)
        return os.path.join(absolutePath, 'sumtool.ui')


if __name__ == '__main__':
    print(UiPaths.mainWindowUIPath())
