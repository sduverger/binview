#!/usr/bin/env python

import struct, sys, random
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

class View(QtGui.QWidget):
    def __init__(self, data):
        super(View, self).__init__()
        self.data = data
        self.initUI()

    def initUI(self):
        QtGui.QWidget.__init__(self)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.terminate)
        self.setGeometry(0, 0, 640, 480)
        self.setWindowTitle('BinView')

    def BytePlot(self):
        w = self.width()
        h = len(self.data)/self.width()
        if len(self.data) % self.width() != 0:
            h += 1

        self.image = QtGui.QImage(self.data, w, h, QtGui.QImage.Format_Indexed8)
        #self.image.setColorTable(range(256))
        for i in range(256):
            self.image.setColor(i, QtGui.qRgb(i,i,i))

    def resizeEvent(self, e):
        self.BytePlot()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        sRect = QtCore.QRect(0, 0, self.image.width(), self.height())
        dRect = QtCore.QRect(0, 0, self.width(), self.height())
        qp.drawImage(dRect, self.image, sRect)
        qp.end()

    def terminate(self):
        QtGui.QApplication.quit()

## main
if len(sys.argv) != 2:
    print "need file"
    sys.exit(1)

fd = open(sys.argv[1])
data = fd.read()
fd.close()
app = QtGui.QApplication(sys.argv)
View(data).show()
sys.exit(app.exec_()) 
