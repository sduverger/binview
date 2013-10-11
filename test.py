#!/usr/bin/env python

import struct, sys, random
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

class View(QtGui.QWidget):
    def __init__(self, data):
        super(View, self).__init__()
        self.data = data
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]
        self.initUI()

    def initUI(self):
        QtGui.QWidget.__init__(self)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("q"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+q"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+c"), self, self.terminate)

        self.setGeometry(0, 0, 640, 480)
        self.setWindowTitle('BinView')

    def BytePlot(self):
        w = self.width()
        h = len(self.data)/self.width()
        if len(self.data) % self.width() != 0:
            h += 1

        self.image = QtGui.QImage(self.data, w, h, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)

    def digraph(self):
        w = 256
        h = 256
        c = QtGui.qRgb(255,255,255)
        self.image = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)
        for i in xrange(0,len(self.data),2):
            x = ord(self.data[i])
            y = ord(self.data[i+1])
            self.image.setPixel(x,y,c)

    def resizeEvent(self, e):
        #self.BytePlot()
        self.digraph()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        sRect = QtCore.QRect(0, 0, self.image.width(), self.height())
        dRect = QtCore.QRect(0, 0, self.width(), self.height())
        qp.drawImage(dRect, self.image, sRect)
        qp.end()

    def terminate(self):
        QtGui.QApplication.quit()



##
## main
##
if len(sys.argv) != 2:
    print "need file"
    sys.exit(1)

fd = open(sys.argv[1])
data = fd.read()
fd.close()
app = QtGui.QApplication(sys.argv)
view = View(data)
view.show()
sys.exit(app.exec_()) 
