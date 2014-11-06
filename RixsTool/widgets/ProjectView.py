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
# Imports for GUI
from PyMca5.PyMcaGui import PyMcaQt as qt

from RixsTool.Utils import unique as RixsUtilsUnique
from RixsTool.widgets.ContextMenu import ProjectContextMenu, RemoveAction, RemoveItemAction, RemoveContainerAction,\
    ShowAction, ExpandAction, RenameAction
from RixsTool.Project import ItemContainer

DEBUG = 0


class ProjectView(qt.QTreeView):
    showSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None):
        super(ProjectView, self).__init__(parent)
        # TODO: Check if project is instance of RixsProject
        #self.project = project
        self.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        #self.customContextMenuRequested.connect(self.contextMenuRequest)

    def _emitShowSignal(self, containerList):
        """
        :param list containerList: Contains items selected in the view

        Filters the containers in container list for such that contain a :py:class::`DataItem.DataItem` and emits
        a list of references to the items.
        """
        itemList = [ItemContainer.item(container) for container in filter(ItemContainer.hasItem, containerList)]
        for item in itemList:
            print('%s: %s %s' % (item.key(), str(item.shape()), type(item.array)))
        self.showSignal.emit(itemList)

    def selectedContainers(self):
        if DEBUG >= 1:
            print('ProjectView.selectedItems -- called')
        model = self.model()
        if not model:
            if DEBUG >= 1:
                print('ProjectView.contextMenuEvent -- Model is none. Abort')
            return []

        modelIndexList = self.selectedIndexes()
        RixsUtilsUnique(modelIndexList, "row")
        return [model.containerAt(idx) for idx in modelIndexList]

    def selectedItems(self):
        return [container.item() for container in self.selectedContainers() if container.hasItem()]

    def contextMenuEvent(self, event):
        if DEBUG >= 1:
            print('ProjectView.contextMenuEvent -- called')
        model = self.model()
        if not model:
            if DEBUG >= 1:
                print('ProjectView.contextMenuEvent -- Model is none. Abort')
            return

        modelIndexList = self.selectedIndexes()
        RixsUtilsUnique(modelIndexList, "row")
        containerList = [model.containerAt(idx) for idx in modelIndexList]
        if DEBUG >= 1:
            print('ProjectView.contextMenuEvent -- Received %d element(s)' % len(modelIndexList))
            for idx in modelIndexList:
                print('\t%d %d' % (idx.row(), idx.column()))

        menu = ProjectContextMenu()
        if not any([container.hasItem() for container in containerList]):
            # No DataItem in selection, deactivate actions aimt at DataItems
            for action in menu.actionList:
                if isinstance(action, ShowAction) or isinstance(action, RemoveItemAction):
                    action.setEnabled(False)
        else:
            #if not any([container.childCount() for container in containerList]):
            # No containers in selection, deactivate actions aimt at containers
            for action in menu.actionList:
                if isinstance(action, ExpandAction)\
                        or isinstance(action, RemoveContainerAction)\
                        or isinstance(action, RenameAction):
                    action.setEnabled(False)
        menu.build()
        action = menu.exec_(event.globalPos())

        if DEBUG >= 1:
            print("ProjectView.contextMenuEvent -- received action '%s'" % str(type(action)))
        if isinstance(action, RemoveAction):
            if DEBUG >= 1:
                print("\tRemoving item(s)")
            for idx in modelIndexList:
                model.removeContainer(idx)
        elif isinstance(action, ShowAction):
            self._emitShowSignal(containerList)
        elif isinstance(action, RenameAction):
            # TODO: Call visualization here
            pass
        elif isinstance(action, ExpandAction):
            for modelIndex in modelIndexList:
                self.expand(modelIndex)
        else:
            return


class DummyNotifier(qt.QObject):
    def signalReceived(self, val=None):
        print('DummyNotifier.signal received -- kw:\n', str(val))


if __name__ == '__main__':
    from RixsTool.widgets.Models import ProjectModel

    directory = '/home/truter/lab/mock_folder'
    proj = ProjectModel()
    proj.crawl(directory)

    app = qt.QApplication([])
    #win = BandPassFilterWindow()
    #win = FileSystemBrowser()
    win = ProjectView()
    win.setModel(proj)

    notifier = DummyNotifier()
    if isinstance(win, ProjectView):
        win.showSignal.connect(notifier.signalReceived)
    win.show()
    app.exec_()
