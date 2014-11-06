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

from PyMca5.PyMcaGui import PyMcaQt as qt

__doc__ = """Module provides actions and context menus for views. Based on the abstract base class
:py:class:`AbstractAction`, the actions remain empty child classes. This procedure allows to distinguish
them later on in a clear and concise manner by using the isinstance(..) builtin method.

The context menus are composed of the aforementioned actions and define the way a user can act upon the contents
of a view.
"""


#
# AbstractContextMenu class
#
class AbstractAction(qt.QAction):
    __doc__ = """Base class for actions"""

    def __init__(self, icon=None, text=None, parent=None):
        self.__icon = icon
        self.__text = text
        if icon and text:
            super(AbstractAction, self).__init__(icon, text, parent)
        elif text:
            super(AbstractAction, self).__init__(text, parent)
        else:
            super(AbstractAction, self).__init__(parent)


#
# Actions concerning the Project View
#
class RemoveAction(AbstractAction):
    pass


class RemoveItemAction(RemoveAction):
    pass


class RemoveContainerAction(RemoveAction):
    pass


class ShowAction(AbstractAction):
    pass


class ExpandAction(AbstractAction):
    pass


class RenameAction(AbstractAction):
    pass


#
# Actions concerning the FileSystemBrowser
#
class AddFilesAction(AbstractAction):
    pass


#
# AbstractContextMenu class
#
class AbstractContextMenu(qt.QMenu):
    __doc__ = """Base class for context menus"""

    def __init__(self, parent=None):
        super(AbstractContextMenu, self).__init__()
        self.actionList = []

    def build(self):
        """
        Adds the actions in actionList to the context menu. String '<sep>' in actionList indicates a seperator.

        Elements in actionList must be either:
        - str: indicates separator
        - QAction
        - 3-Tuple: (text, QObject receiver, str member)
        """
        self.clear()
        for action in self.actionList:
            if isinstance(action, str):
                self.addSeparator()
            elif isinstance(action, tuple):
                text = action[0]
                receiver = action[1]
                function = action[2]
                self.addAction(text, receiver, function)
            elif isinstance(action, qt.QAction):
                self.addAction(action)
            else:
                raise ValueError("ProjectContextMenu.build -- unknown type '%s' in actionList"%str(type(action)))


#
# ContextMenus concerning the ProjectView
#
class ProjectContextMenu(AbstractContextMenu):
    def __init__(self, parent=None):
        super(ProjectContextMenu, self).__init__(parent)

        showItemAction = ShowAction(
            None,
            'Show item in native format',
            self
        )

        removeItemAction = RemoveItemAction(
            qt.QIcon(':/minus.ico'),
            'Remove item from project',
            self
        )

        renameContainerAction = RenameAction(
            None,
            'Rename group',
            self
        )

        expandContainerAction = ExpandAction(
            None,
            'Expand groups',
            self
        )

        removeContainerAction = RemoveContainerAction(
            qt.QIcon(qt.QPixmap(':/minus.ico')),
            'Disband group',
            self
        )

        self.actionList = [
            showItemAction,
            removeItemAction,
            'seperator',
            renameContainerAction,
            expandContainerAction,
            removeContainerAction
        ]


#
# ContextMenus concerning the FileSystemBrowser
#
class FileContextMenu(AbstractContextMenu):
    def __init__(self, parent=None):
        super(FileContextMenu, self).__init__(parent)

        addToProjectAction = AddFilesAction(
            qt.QIcon(qt.QPixmap(':/plus.ico')),
            'Add files to project',
            self
        )

        self.actionList = [
            addToProjectAction
        ]


if __name__ == '__main__':
    pass
