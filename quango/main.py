#  -*- coding: utf-8 -*-
# *****************************************************************************
# MLZ library of Tango servers
# Copyright (c) 2015 by the authors, see LICENSE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Module authors:
#   Georg Brandl <g.brandl@fz-juelich.de>
#
# *****************************************************************************

from PyQt4.QtCore import QByteArray, QSettings, pyqtSignature as qtsig
from PyQt4.QtGui import QMainWindow, QMessageBox, QTreeWidgetItem, QColor, \
    QBrush, QIcon

import PyTango

import quango.res
from quango.utils import loadUi, parseTangoHost


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        loadUi(self, 'main.ui')
        settings = QSettings()
        self.splitter.restoreState(settings.value('split', b'', QByteArray))
        self.tree.header().restoreState(settings.value('header', b'', QByteArray))

        self._tangoHosts = {}

        self.addTangoHost('localhost:10000')

    def closeEvent(self, event):
        settings = QSettings()
        settings.setValue('split', self.splitter.saveState())
        settings.setValue('header', self.tree.header().saveState())
        return QMainWindow.closeEvent(self, event)

    @qtsig('')
    def on_actionQuit_triggered(self):
        self.close()

    @qtsig('')
    def on_actionAbout_triggered(self):
        QMessageBox.information(self, 'About',
                                'Quango, a generic Tango device client\n\n'
                                '(c) 2015 MLZ instrument control')

    @qtsig('')
    def on_actionAbout_Qt_triggered(self):
        QMessageBox.aboutQt(self, 'About Qt')

    def on_tree_itemClicked(self, item, _col):
        pass

    def addTangoHost(self, host):
        host, port = parseTangoHost(host).split(':')

        db = PyTango.Database(host, port)

        hostitem = QTreeWidgetItem()
        hostitem.setIcon(0, QIcon(':/server.png'))
        hostitem.setText(0, host)

        hostinfo = {}
        devices = {}

        # get a list of all devices
        for server in db.get_server_list():
            hostinfo[server] = {}
            devclslist = db.get_device_class_list(server)
            for i in xrange(0, len(devclslist), 2):
                devname, devcls = devclslist[i:i + 2]
                devinfo = db.get_device_info(devname)
                hostinfo[devname] = [server, devcls, devinfo]

                domain, family, member = devname.split('/')
                devices.setdefault(domain, {}).setdefault(family, set()).add(member)

        # create tree widget items for the devices
        for domain in sorted(devices):
            domainitem = QTreeWidgetItem([domain, ''])
            domainitem.setIcon(0, QIcon(':/folder.png'))
            for family in sorted(devices[domain]):
                familyitem = QTreeWidgetItem([family, ''])
                familyitem.setIcon(0, QIcon(':/folder.png'))
                for member in sorted(devices[domain][family]):
                    devname = domain + '/' + family + '/' + member
                    devitem = QTreeWidgetItem([member, hostinfo[devname][0]])
                    devitem.setIcon(0, QIcon(':/plug.png'))
                    if not hostinfo[devname][2].exported:
                        devitem.setForeground(0, QBrush(QColor('#666666')))
                    familyitem.addChild(devitem)
                domainitem.addChild(familyitem)
            hostitem.addChild(domainitem)

        self.tree.addTopLevelItem(hostitem)
        hostitem.setExpanded(True)

        self._tangoHosts[host] = hostinfo
