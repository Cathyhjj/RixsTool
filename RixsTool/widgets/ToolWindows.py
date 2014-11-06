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
__doc__ = """Module provides a base class for a data manipulation GUI for py:mod:`PyMca.widgets.PlotWindow`"""

# Imports for GUI
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyQt4 import uic

from RixsTool.UiPaths import UiPaths
from RixsTool.Operations import Filter, SlopeCorrection, Integration
from RixsTool.Items import FunctionItem

import platform

DEBUG = 1
PLATFORM = platform.system()


class AbstractToolTitleBar(qt.QWidget):

    __doc__ = """Customized version of a generic title bar, mainly to include a check box."""

    def __init__(self, parent=None):
        super(AbstractToolTitleBar, self).__init__(parent)
        uiFilePath = UiPaths.abstractTitleToolBar()
        uic.loadUi(uiFilePath, self)
        self.closeButton.setFlat(True)


class AbstractToolWindow(qt.QDockWidget):

    __doc__ = """py:class:`RixsTool.widgets.AbstractToolWindow` is the base class for widgets that can be placed in the
    dock area of a py:mod:`PyMca.widgets.PlotWindow`. Tool windows can be divided into two types: inplace
    calculations with the result being immediately displayed and export tools that take data present in the visualization
    (or an underlying data structure for that matter), performs operations on it and inject the results of these
    operations into a data structure (in case of the RixsTool this is py:class:`RixsProject`)

    While the former uses the :py:attribute::`valuesChangedSignal` to indicate a change in the tools parameters (i.e.
    the GUI elements) the latter needs custom signals (e.g. :py:attribute::`exportSelectedSignal` in
    :py:class:'SumImageTool') to propagate the demand for calculation to a parent GUI element. The parent GUI element
    can then perform the calculations itself or delegate them to other entities.

    **TODO:**
        * Make class hierarchy reflect the two types of tool windows"""

    #
    # valuesChangedSignal tranports the tool parameters in dict
    # TODO: Maybe this is unnecessary, since the tools parameters can be recovered using the getValue function
    #
    valuesChangedSignal = qt.pyqtSignal(object)

    def __init__(self, uiPath=None, parent=None):
        super(AbstractToolWindow, self).__init__(parent)
        self._values = {}
        self.__active = None  # True or False
        self.__uiLoaded = False
        self.__uiPath = uiPath
        self.process = None

    def emitValuesChangedSignal(self, **kw):
        ddict = self.getValues()
        self.valuesChangedSignal.emit(ddict)

    def setWindowTitle(self, title):
        titleBar = self.titleBarWidget()
        if isinstance(titleBar, AbstractToolTitleBar):
            titleBar.titleLabel.setText(title)
        else:
            qt.QDockWidget.setWindowTitle(self, title)

    def active(self):
        return self.__active

    def hasUI(self):
        return self.__uiLoaded

    def setUI(self, uiPath=None):
        if uiPath is None:
            uiPath = self.__uiPath
        try:
            #uic.loadUi(uiPath, self._widget)
            uic.loadUi(uiPath, self)
        except IOError:
            self.__uiLoaded = False
            raise IOError("AbstractToolWindow.setUI -- failed to find ui-file: '%s'" % uiPath)
        titleBar = AbstractToolTitleBar()
        #titleBar.closeButton.clicked.connect(self.destroy)  # Ends the whole process
        titleBar.closeButton.clicked.connect(self.close)  # Hides the tool
        titleBar.activeCheckBox.stateChanged.connect(self.stateChanged)
        self.__active = (titleBar.activeCheckBox.checkState() == qt.Qt.Checked)
        self.setTitleBarWidget(titleBar)
        self.__uiLoaded = True

    def stateChanged(self, state):
        titleBar = self.titleBarWidget()
        if state == qt.Qt.Unchecked:
            titleBar.titleLabel.setEnabled(False)
            self.__active = False
        else:
            titleBar.titleLabel.setEnabled(True)
            self.__active = True
        #self.toolStateChangedSignal.emit(state, self)
        parameters = self.getValues()
        self.valuesChangedSignal.emit(parameters)

    def getValues(self):
        ddict = {}
        sortedKeys = sorted(self._values.keys())
        for key in sortedKeys:
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or isinstance(obj, qt.QTextEdit):
                val = obj.getPlainText()
            elif isinstance(obj, qt.QLineEdit):
                val = obj.text()
            elif isinstance(obj, qt.QCheckBox) or isinstance(obj, qt.QRadioButton):
                val = obj.checkState()
            elif isinstance(obj, qt.QComboBox):
                val = obj.currentText()
            elif isinstance(obj, qt.QAbstractSlider) or \
                    isinstance(obj, qt.QSpinBox) or \
                    isinstance(obj, qt.QDoubleSpinBox):
                val = obj.value()
            else:
                val = None
            ddict[key] = val
        return ddict

    def setValues(self, ddict):
        for key, val in ddict.items():
            obj = self._values[key]
            if isinstance(obj, qt.QPlainTextEdit) or isinstance(obj, qt.QTextEdit):
                obj.setPlainText(val)
            elif isinstance(obj, qt.QLineEdit):
                obj.setText(str(val))
            elif isinstance(obj, qt.QCheckBox) or isinstance(obj, qt.QRadioButton):
                obj.setCheckState(val)
            elif isinstance(obj, qt.QComboBox):
                idx = obj.findText(val)
                obj.setCurrentIndex(idx)
            elif isinstance(obj, qt.QAbstractSlider) or \
                    isinstance(obj, qt.QSpinBox) or \
                    isinstance(obj, qt.QDoubleSpinBox):
                obj.setValue(val)
            else:
                if DEBUG >= 1:
                    print("AbstractToolWindow.setValues -- Could not set value for key '%s'" % str(key))


class BandPassFilterWindow(AbstractToolWindow):
    def __init__(self, parent=None):
        uiPath = UiPaths.bandPassFilterUiPath()
        super(BandPassFilterWindow, self).__init__(uiPath=uiPath,
                                                   parent=parent)
        self.setUI()
        self.setWindowTitle('Band Pass Filter')

        self._values = {
            'high': self.upperThresholdSpinBox,
            'low': self.lowerThresholdSpinBox,
            'offset': self.offsetSpinBox
        }

        self.setValues({
            'high': 800.,
            'low': 8.,
            'offset': 114.
        })

        #
        # Connects
        #
        self.upperThresholdSpinBox.valueChanged.connect(self.emitValuesChangedSignal)
        self.lowerThresholdSpinBox.valueChanged.connect(self.emitValuesChangedSignal)
        self.offsetSpinBox.valueChanged.connect(self.emitValuesChangedSignal)

        #
        # Process
        #
        self.process = Filter.bandPassFilter


class BandPassID32Window(AbstractToolWindow):
    def __init__(self, parent=None):
        uiPath = UiPaths.bandPassFilterID32UiPath()
        super(BandPassID32Window, self).__init__(uiPath=uiPath,
                                                 parent=parent)
        self.setUI()
        self.setWindowTitle('Band Pass Filter ID32')

        self._values = {
            'energy': self.photonEdit,
            'binning': self.binningEdit,
            'preset': self.exposureEdit
        }

        self.setValues({
            'energy': str(932.0),
            'binning': str(4),
            'preset': str(300)
        })

        #
        # Set validators for the line edits
        #
        photonValidator = qt.QDoubleValidator()
        photonValidator.setBottom(0.0)
        photonValidator.setTop(10000.0)
        photonValidator.setDecimals(4)

        binningValidator = qt.QIntValidator()
        binningValidator.setBottom(0)
        binningValidator.setTop(512)

        exposureValidator = qt.QIntValidator()
        exposureValidator.setBottom(0)
        exposureValidator.setTop(100000)

        self.photonEdit.setValidator(photonValidator)
        self.binningEdit.setValidator(binningValidator)
        self.exposureEdit.setValidator(exposureValidator)

        #
        # Connects
        #
        self.photonEdit.textEdited.connect(self.emitValuesChangedSignal)
        self.binningEdit.textEdited.connect(self.emitValuesChangedSignal)
        self.exposureEdit.textEdited.connect(self.emitValuesChangedSignal)

        self.photonEdit.returnPressed.connect(self.emitValuesChangedSignal)
        self.binningEdit.returnPressed.connect(self.emitValuesChangedSignal)
        self.exposureEdit.returnPressed.connect(self.emitValuesChangedSignal)

        #
        # Process
        #
        self.process = Filter.bandPassFilterID32

    def getValues(self):
        ddict = AbstractToolWindow.getValues(self)
        for key, value in ddict.items():
            ddict[key] = float(value)
        return ddict


class ImageAlignmenWindow(AbstractToolWindow):
    def __init__(self, parent=None):
        uiPath = UiPaths.alignmentFilterUiPath()
        super(ImageAlignmenWindow, self).__init__(uiPath=uiPath,
                                                  parent=parent)
        self.setUI()
        self.setWindowTitle('Slope correction')

        self._values = {
            'a': self.aSpinBox,
            'b': self.bSpinBox,
            'c': self.cSpinBox
        }

        self.setValues({
            'a': -5.25*10**-5,
            'b': 0.18877,
            'c': 0.
        })

        #
        # Connects
        #
        self.aSpinBox.valueChanged.connect(self.emitValuesChangedSignal)
        self.bSpinBox.valueChanged.connect(self.emitValuesChangedSignal)
        self.cSpinBox.valueChanged.connect(self.emitValuesChangedSignal)

        #
        # Process
        #
        self.process = self.alignImage  # Expects smile function

    def alignImage(self, image, params):
        func = FunctionItem('Slope Function', '')
        expression = lambda x, a, b, c: a*x**2 + b*x + c
        params = self.getValues()

        params['a'] *= 10.**-5

        func.setExpression(expression)
        func.setParameters(params)

        return SlopeCorrection.alignImage(image, func)


class SumImageTool(AbstractToolWindow):
    __doc__ = """GUI to transform image to spectrum by summation along lines/columns"""

    exportSelectedSignal = qt.pyqtSignal()
    exportCurrentSignal = qt.pyqtSignal()

    def __init__(self, parent=None):
        uiPath = UiPaths.sumToolUiPath()
        super(SumImageTool, self).__init__(uiPath=uiPath,
                                           parent=parent)
        self.setUI()
        self.setWindowTitle('Integration')

        self._values = {
            'axis': self.axisComboBox
        }

        self.axisComboBox.addItems([
            'columns',
            'rows'
        ])

        self.setValues({
            'axis': 'columns'
        })

        #
        # Connect the buttons
        #
        self.selectedButton.clicked.connect(self.exportSelectedSignal.emit)
        self.currentButton.clicked.connect(self.exportCurrentSignal.emit)

        #
        # Process
        #
        self.process = self.sumImage

    def sumImage(self, image, param=None):
        params = self.getValues()
        if str(params['axis']) == 'columns':
            axis = 1
        else:
            axis = 0
        return Integration.axisSum(image, {'axis': axis})


class EnergyScaleTool(AbstractToolWindow):
    __doc__ = """GUI to set an energy scale to the project"""

    energyScaleSignal = qt.pyqtSignal()

    def __init__(self, parent=None):
        uiPath = UiPaths.energyAlignmentUiPath()
        super(EnergyScaleTool, self).__init__(uiPath=uiPath,
                                              parent=parent)
        self.setUI()
        self.setWindowTitle('Energy alignment')

        self._values = {
            'slope': self.slopeSpinBox,
            'zero': self.zeroSpinBox
        }

        self.setValues({
            'slope': 1.0,
            'zero': 0.
        })

        #
        # Connect the spin boxes
        #
        self.slopeSpinBox.valueChanged.connect(self.energyScaleSignal)

        #
        # Process
        #
        self.process = self.energyScale

    def energyScale(self):
        #
        # Create function item
        #
        scale = FunctionItem('Energy scale', '')

        #
        # Set expression
        #
        scale.setExpression(lambda x, a, b: a*x + b)

        #
        # Set parameters
        #
        parameters = self.getValues()
        scale.setParameters({
            'a': parameters['slope'],
            'b': parameters['zero']
        })

        if DEBUG >= 1:
            print('EnergyScaleTool.energyScale -- called')
        return scale


def unitTest_BandPassFilter():
    dummy = DummyNotifier()
    app = qt.QApplication([])
    filterWindow = ImageAlignmenWindow()
    #filterWindow.exportSelectedSignal.connect(dummy.signalReceived)
    #filterWindow.exportCurrentSignal.connect(dummy.signalReceived)
    filterWindow.show()
    app.exec_()


class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n', str(val))

if __name__ == '__main__':
    unitTest_BandPassFilter()
