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
from RixsTool.widgets import ProjectView

__author__ = "Tonn Rueter - ESRF Data Analysis Unit"

from RixsTool.Utils import unique as RixsUtilsUnique
#from RixsTool.Datahandling import RixsProject
from RixsTool.Project import RixsProject
from PyMca5.PyMcaGui import PyMcaQt as qt
from os.path import normpath as OsPathNormpath

DEBUG = 0


class ProjectModel(RixsProject, qt.QAbstractItemModel):
    __doc__ = """
    Tree model with :class:`datahandling.RixsProject` as underlying data structure. Implementation of
    the interface of :class:`QAbstractItemModel`.
    """

    def __init__(self, parent=None):
        """
        :param parent: Parent widget
        :type parent: QAbstractItemView
        """
        RixsProject.__init__(self)
        qt.QAbstractItemModel.__init__(self, parent)

    def removeContainer(self, modelIndex):
        if not modelIndex.isValid():
            print('Index is invalid')
            return
        container = self.containerAt(modelIndex)
        parentIndex = self.parent(modelIndex)

        self.beginRemoveRows(parentIndex, container.childNumber(), container.childNumber())

        #if container.childCount():
        #    print('Has children')
        #    # Child count is nonzero
        #    for child in container.children:
        #        del(child)

        #parentContainer = self.containerAt(parentIndex)
        #idx = container.childNumber()
        #del(parentContainer.children[idx])

        RixsProject.removeContainer(self, container.label)
        self.endRemoveRows()

    def addItem(self, item):
        """
        :param item:
        :type item:
        """
        if DEBUG >= 1:
            print('### ProjectModel.addItem -- called ###')
        try:
            container = RixsProject.addItem(self, item)
        except ValueError as error:
            # Catch ValueError from base class method RixsProject.addItem
            # caused by unknown item type (must be ScanItem, ImageItem, ...)
            if DEBUG >= 1:
                print(error)
            return False

        modelIndex = self.createIndex(container.childNumber(), 0, container)
        parentIndex = self.parent(modelIndex)
        self.beginInsertRows(parentIndex, container.childNumber(), container.childNumber())
        self.endInsertRows()
        return True

    def addGroup(self, label, node=None):
        """
        :param item:
        :type item:
        """
        if DEBUG >= 1:
            print('### ProjectModel.addGroup -- called ###')
        try:
            container = RixsProject.addGroup(self, label, node)
        except ValueError as error:
            # Catch ValueError from base class method RixsProject.addGroup
            # caused by already present label
            if DEBUG >= 1:
                print(error)
            return False

        # TODO: calling self.createIndex creates RuntimeError! W\o calling it, the method works though..
        #modelIndex = self.createIndex(container.childNumber(), 0, container)
        #parentIndex = self.parent(modelIndex)
        #self.beginInsertRows(parentIndex, container.childNumber(), container.childNumber())
        #self.endInsertRows()
        return True

    def containerAt(self, modelIndex):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :returns: ItemContainer instance at modelIndex.
        :rtype: ItemContainer
        """
        if modelIndex.isValid():
            item = modelIndex.internalPointer()
            if item:
                return item
        return self.projectRoot

    def data(self, modelIndex, role=qt.Qt.DisplayRole):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex
        :param role: Determines which data is extracted from the container
        :type role: Qt.ItemDataRole (int)
        :returns: Requested data or None
        :rtype: str, QSize, None, ...
        """
        if not modelIndex.isValid():
            return None
        container = self.containerAt(modelIndex)
        if role == qt.Qt.DisplayRole:
            if not container.hasItem():
                if modelIndex.column():
                    # Not in the 0-th column..
                    return ''
                return str(container.label)
            return str(container.data(modelIndex.column()))

    def setData(self, modelIndex, value, role=qt.Qt.DisplayRole):
        """
        :param modelIndex:
        :type modelIndex: QModelIndex
        :param role:
        :type role: Qt.ItemDataRole (int)

        Changes the attributes of a :class:`ItemContainer`
        """
        container = self.containerAt(modelIndex)
        if not container.hasItem():
            # Only ItemContainers that contain DataItem can be changed
            return False
        if role == qt.Qt.DisplayRole:
            if not modelIndex.column():
                # Not the 0-th column, change key!
                return False
            container.label = str(value) # TODO: Changes label but not item key...
        self.dataChanged.emit(modelIndex, modelIndex)

    def headerData(self, section, orientation, role=qt.Qt.DisplayRole):
        """
        :param section: Header column
        :type section: int
        :param orientation: Determines if header is vertical or horizontal
        :type orientation: Qt.Orientation (int)
        :param role: Determines return type
        :type role: Qt.ItemDataRole (int)
        :returns: Requested information or None
        :rtype: str, QSize, None, ...
        """
        if section < 0 or self.columnCount() <= section:
            return None
        if role == qt.Qt.DisplayRole:
            headerItem = self.projectRoot._data
            return headerItem[section].upper()
        else:
            return None

    def rowCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex

        Number of children under the given model index

        :returns: Number of rows
        :rtype: int
        """
        parent = self.containerAt(parentIndex)
        return parent.childCount()

    def columnCount(self, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param modelIndex: Model index of a container in the model
        :type modelIndex: QModelIndex

        Number of columns of a given model index. Each column displays an information about the model index.

        :returns: Number of columns (i.e. attributes) shown
        :rtype: int
        """
        parent = self.containerAt(parentIndex)
        return parent.columnCount()

    def flags(self, modelIndex):
        """
        :param modelIndex: (QModelIndex) Model index of a container in the model

        Determines what the item stored under models can be used for and how it is displayed.

        :returns: Flag indicating how the view can interact with the model
        :rtype: Qt.ItemFlag
        """
        if modelIndex.isValid():
            return qt.Qt.ItemIsEditable | qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable
        else:
            return 0

    def index(self, row, col, parentIndex=qt.QModelIndex(), *args, **kwargs):
        """
        :param row: (int) Row in the table of parentIndex
        :param col: (int) Column in the table of parentIndex
        :param parentIndex: (QModelIndex) Determines the table

        Methods creates a model index under which a particular item in the underlying datastructure
        can be accessed by the view.

        :returns: (Possibly invalid) model index of a container in the model. Invalid model indexes refer to the root
        :rtype: QModelIndex
        """
        if parentIndex.isValid() and parentIndex.column() > 0:
            return qt.QModelIndex()
        parent = self.containerAt(parentIndex)
        try:
            child = parent.children[row]
        except IndexError:
            return qt.QModelIndex()
        if child:
            return self.createIndex(row, col, child)
        else:
            return qt.QModelIndex()

    def parent(self, modelIndex=qt.QModelIndex()):
        """
        :param modelIndex: (QModelIndex) Model index of a container in the model

        Methods creates a model index under which the parent of a particular item in the underlying datastructure can
        be accessed by the view.

        :returns: (Possibly invalid) model index of the parent container. Invalid model indexes refer to the root
        :rtype: QModelIndex
        """
        if not modelIndex.isValid():
            return qt.QModelIndex()

        child = self.containerAt(modelIndex)
        #print('ProjectView.parent -- type(child):', type(child), hasattr(child, 'parent'))
        parentContainer = child.parent

        if parentContainer == self.projectRoot:
            return qt.QModelIndex()

        return self.createIndex(parentContainer.childNumber(), 0, parentContainer)

    def addFileInfoList(self, fileInfoList):
        if DEBUG >= 1:
            print('ProjectView.addFileInfoList -- received fileInfoList (len: %d)' % len(fileInfoList))
        itemList = []
        for info in fileInfoList:
            absFilePath = OsPathNormpath(str(info.canonicalFilePath()))
            #self.read(absFilePath)
            itemList += RixsProject.read(self, absFilePath)
        for item in itemList:
            self.addItem(item)


class QDirListModel(qt.QAbstractListModel):
    def __init__(self, parent=None):
        super(QDirListModel, self).__init__(parent)
        self.__directoryList = []

    def __getitem__(self, idx):
        """
        :param idx: Return idx-th element in the model
        :type idx: int
        """
        return self.__directoryList[idx]

    def flags(self, modelIndex):
        if modelIndex.isValid():
            return qt.Qt.ItemIsSelectable | qt.Qt.ItemIsEditable | qt.Qt.ItemIsEnabled
        else:
            if DEBUG >= 1:
                print('QDirListModel.flags -- received invalid modelIndex')
            return 0

    def __len__(self):
        return len(self.__directoryList)

    def rowCount(self, modelIndex = qt.QModelIndex()):
        return len(self.__directoryList)

    def insertDirs(self, row, directoryList):
        """
        :param row: Determines after which row the items are inserted
        :type row: int
        :param directoryList: Carries the new legend information
        :type directoryList: list of either strings or QDirs
        """
        modelIndex = self.createIndex(row,  0)
        count = len(directoryList)
        qt.QAbstractListModel.beginInsertRows(self,
                                              modelIndex,
                                              row,
                                              row+count)
        head = self.__directoryList[0:row]
        tail = self.__directoryList[row:]
        new  = [qt.QDir()] * count
        for idx, elem in enumerate(directoryList):
            if isinstance(elem, str):
                newDir = qt.QDir(elem)
            elif isinstance(elem, qt.QDir):
                # Call copy ctor
                newDir = qt.QDir(elem)
            else:
                if DEBUG >= 1:
                    print('QDirListModel.insertDirs -- Element %d: Neither instance of str nor QDir'%idx)
                continue
            new[idx] = newDir
        self.__directoryList = head + new + tail
        # Reduce self.__directoryList to unique elements..
        RixsUtilsUnique(self.__directoryList, 'absolutePath')
        qt.QAbstractListModel.endInsertRows(self)
        return True

    def insertRows(self, row, count, modelIndex=qt.QModelIndex()):
        raise NotImplementedError('Use LegendModel.insertLegendList instead')

    def removeDirs(self, row, count, modelIndex=qt.QModelIndex()):
        length = len(self.__directoryList)
        if length == 0:
            # Nothing to do..
            return True
        if row < 0 or row >= length:
            raise IndexError('Index out of range -- ' +
                             'idx: %d, len: %d' % (row, length))
        if count == 0:
            return False
        qt.QAbstractListModel.beginRemoveRows(self,
                                              modelIndex,
                                              row,
                                              row+count)
        del(self.__directoryList[row:row+count])
        qt.QAbstractListModel.endRemoveRows(self)
        return True

    def removeRows(self, row, count, modelIndex = qt.QModelIndex()):
        raise NotImplementedError('QDirListModel.removeRows -- Not implemented, use QDirListModel.removeDirs instead')

    def data(self, modelIndex, role):
        if modelIndex.isValid():
            idx = modelIndex.row()
        else:
            if DEBUG >= 1:
                print('WorkingDirModel.data -- received invalid index')
            return None
        if idx >= len(self.__directoryList):
            raise IndexError('WorkingDirModel.data -- list index out of range')

        qdir = self.__directoryList[idx]
        if role == qt.Qt.DisplayRole:
            dirPath = qdir.absolutePath()
            return qt.QDir.toNativeSeparators(dirPath)
        else:
            return None


def unitTest_QDirListModel():
    inp = ['foo/dir', 'bar\\dir', 'baz']
    listModel = QDirListModel()
    listModel.insertDirs(0, inp)

    print('datahandling.unitTest_QDirListModel -- Input string list:', str(inp))

    first = (len(listModel) == 3) and (listModel.rowCount() == 3)
    second, third = True, True
    for idx in range(len(listModel)):
        modelIndex = listModel.createIndex(idx, 0)
        displayRole = listModel.data(modelIndex, qt.Qt.DisplayRole)
        flag = listModel.flags(modelIndex)
        qdir = listModel[idx]

        second &= isinstance(displayRole, str)
        third  &= isinstance(qdir, qt.QDir)

        print('\t%d: %s\t%s\t%s\t%s'%\
              (idx, str(displayRole), type(displayRole), int(flag), str(qdir)))

    if first and second and third:
        print('datahandling.unitTest_QDirListModel -- Success')
        return True
    else:
        print('datahandling.unitTest_QDirListModel -- Failure')
        return False


def unitTest_ProjectModel():
    class DummyNotifier(qt.QObject):
        def signalReceived(self, val0=None, val1=None):
            print('DummyNotifier.signal received -- kw:\n', str(val0), str(val1))
    dummy = DummyNotifier()

    #directory = r'C:\Users\tonn\lab\mockFolder'  # On windows
    #directory = '/Users/tonn/DATA/rixs_data/'  # On mac
    directory = '/home/truter/lab/mock_folder'  # On linkarkouli
    project = ProjectModel()
    project.dataChanged.connect(dummy.signalReceived)

    #for result in osWalk(directory):
    #    currentPath = result[0]
    #    files = result[2]
    #    for ffile in files:
    #        root, ext = osPathSplitext(ffile)
    #        filename = currentPath + osPathSep + ffile
    #        #if ext.replace('.', '') == project.EDF_TYPE:
    #        if ext.replace('.', '') == IODict.EDF_TYPE:
    #            print('Found edf-File:')
    #            llist = project.read(filename)
    #            for item in llist:
    #                project.addItem(item)

    project.crawl(directory)

    app = qt.QApplication([])
    view = ProjectView.ProjectView()
    #model = QContainerTreeModel(project.projectRoot, win)
    #win.setModel(model)
    view.setModel(project)

    removeButton = qt.QPushButton("Remove something")
    #removeButton.clicked.connect(view.removeLastItem)

    layout = qt.QVBoxLayout()
    layout.addWidget(removeButton)
    layout.addWidget(view)

    win = qt.QWidget()
    win.setLayout(layout)

    win.show()
    app.exec_()


if __name__ == '__main__':
    #unitTest_QDirListModel()
    unitTest_ProjectModel()
