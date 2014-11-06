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

#
# Import for EDF file I/O
#
from PyMca5.PyMcaIO.EdfFile import EdfFile

#
# Imports for spec file I/O
#
#from PyMca.PyMcaIO.specfilewrapper import specfilewrapper as SpecFile
#from PyMca.PyMcaIO.specfilewrapper import myscandata

#
# Imports for file access
#
from os.path import split as OsPathSplit
from os import linesep as NEWLINE
from os import access as OsAccess
from os import R_OK as OS_R_OK

#
# Utilities
#
import numpy as np
import time

#
# ProjectItem to wrap data in
#
from RixsTool.Items import ImageItem, SpecItem, ScanItem

DEBUG = 0


class IODict(object):
    EDF_TYPE = 'edf'    # -> Wrapper for edf files
    DAT_TYPE = 'dat'    # -> Wrapper for plaintext data

    # TODO: Use these type too
    SPEC_TYPE = 'stack'  # -> Wrapper for spec files

    @staticmethod
    def inputReaderDict():
        ddict = {
            IODict.EDF_TYPE: EdfReader(),
            IODict.DAT_TYPE: RawReader()
        }
        return ddict


class InputReader(object):
    def __init__(self):
        self._srcType = None
        self.key = ''
        self.reader = None

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        inputType = str(self._srcType)
        return '%s %s %s' % (inputType, 'instance at', id(self))

    def __initReader(self, fileName):
        """
        :param fileName: absolute file name
        :type fileName: str

        Creates reader instance and sets the key.
        """
        if isinstance(self._srcType, type(None)):
            raise NotImplementedError('InputReader.__initReaders -- Do not instantiate base class')
        if DEBUG >= 1:
            print("InputReader.__initReaders -- reading: '%s'" % fileName)
        if not OsAccess(fileName, OS_R_OK):
            return False
        path, name = OsPathSplit(fileName)
        self.key = name
        self.reader = self._srcType(fileName)
        return True

    def itemize(self, fileName):
        """
        :param fileName: File name including absolute path to the file
        :type fileName: str

        Method serves as interface between the different reader types and the DataItem container class.
        :func:`InputReader.itemize` must be reimplemented in every child class.

        :raises ValueError: In case the file is inaccessible
        :raises NotImplementedError: In case the base class is instantiated
        """
        try:
            success = self.__initReader(fileName)
        except NotImplementedError:
            # Reraise error from correct function
            raise NotImplementedError('InputReader.itemize -- Do not instantiate base class')
        if not success:
            raise ValueError("InputReader.itemize -- Invalid file '%s'" % fileName)


class EdfReader(InputReader):
    def __init__(self):
        super(EdfReader, self).__init__()
        self._srcType = EdfFile

    def itemize(self, fileName):
        timeStart = time.time()
        InputReader.itemize(self, fileName)

        numImages = self.reader.GetNumImages()
        llist = []
        if numImages > 1:
            raise NotImplementedError('EdfReader.itemize -- No support for edfs containing multiple images')
            #for idx in range(numImages):
            #    arr = reader.GetData(idx)
            #    newItem = ImageItem(
            #        key=key,
            #        header=reader.GetHeader(0),
            #        array=np.ascontiguousarray(arr, arr.dtype),
            #        fileLocation=reader.FileName
            #    )
        else:
            arr = self.reader.GetData(0)
            newItem = ImageItem(
                key=self.key,
                header=self.reader.GetHeader(0),
                array=np.ascontiguousarray(arr, arr.dtype),
                fileLocation=self.reader.FileName)
            llist += [newItem]

        timeEnd = time.time()
        if DEBUG >= 1:
            print('EdfInputReader.itemize -- Method finished in %.3f s' % (timeEnd - timeStart))
        return llist


class RawReader(InputReader):
    def __init__(self):
        super(RawReader, self).__init__()
        self._srcType = open

    def itemize(self, fileName):
        #raise NotImplementedError('Shit ain\'t ready yet..')
        timeStart = time.time()
        InputReader.itemize(self, fileName)

        if self.reader.closed:
            raise IOError('RawReader -- File handler is closed')

        #
        # Guess key
        #
        key = OsPathSplit(fileName)[-1]
        if DEBUG >= 1:
            print("RawReader -- key: '%s'" % key)

        raw = self.reader.read()
        raw = raw.strip().split(NEWLINE)
        if DEBUG >= 1:
            print("RawReader -- raw: %s" % str(raw))

        if not len(raw):
            if DEBUG >= 1:
                print('RawReader.itemize -- Received empty file')
            return []

        #
        # Try to determine the number of columns
        #
        nRows = len(raw)
        if DEBUG >= 1:
            print('RawReader.itemize -- Determined %d rows' % nRows)

        #
        # Try to determine the number of columns
        #
        nCols = len(raw[0].split())
        if DEBUG >= 1:
            print('RawReader.itemize -- Determined %d columns' % nCols)

        data = np.zeros((nRows, nCols))

        for idx, line in enumerate(raw):
            iterator = [float(number.strip()) for number in line.split()]  # is list even in python3(.2.3)
            data[idx, :] = np.fromiter(iterator, dtype=float)
        data = np.squeeze(data.T)

        if DEBUG >= 1:
            print('RawReader.itemize -- data.shape %s, data:\n%s' % (str(data.shape), data))

        if len(data.shape) == 1:
            item = SpecItem(
                key=key,
                header='',
                array=data,
                fileLocation=fileName
            )
        elif len(data.shape) == 2:
            #
            # Set zero-th column as scale, and first column as data. IGNORE THE REST
            #
            item = ScanItem(
                key=key,
                header='',
                array=data[1],
                fileLocation=fileName
            )
            item.setScale(np.copy(data[0]))
        else:
            raise ValueError('RawReader.itemize -- Unexpected dimensionality')

        llist = [item]

        timeEnd = time.time()
        if DEBUG >= 1:
            print('RawReader.itemize -- Method finished in %.3f s, item %s' % ((timeEnd - timeStart), str(item)))
        return llist


def unitTest_RawReader():
    fname = '/home/truter/lab/rixs/rixs_data/Spectra/test0483.DAT'

    reader = RawReader()
    reader.itemize(fname)


def unitTest_InputReader():
    #rixsImageDir = '/Users/tonn/DATA/rixs_data/Images'
    rixsImageDir = '/home/truter/lab/rixs/rixs_data/Images'
    from os import listdir as OsListDir
    from os.path import isfile as OsPathIsFile, join as OsPathJoin
    edfImageList = [OsPathJoin(rixsImageDir, fn) for fn in OsListDir(rixsImageDir)\
                    if OsPathIsFile(OsPathJoin(rixsImageDir, fn))][1:]

    edfReader = EdfReader()
    for elem in sum([edfReader.itemize(fn) for fn in edfImageList], []):
        print elem.key
    print(edfReader)

if __name__ == '__main__':
    #unitTest_InputReader()
    unitTest_RawReader()
