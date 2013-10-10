#!/usr/bin/env python

import struct, sys, random
from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

class Editor(QtGui.QWidget):
    def __init__(self, data):
        super(Editor, self).__init__()
        self.data = data
        self.initUI()

    def initUI(self):
        QtGui.QWidget.__init__(self)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.terminate)

        self.width = 640
        self.height = 480

        self.setGeometry(0, 0, self.width, self.height)
        self.setWindowTitle('Editor App')
        self.setWindowIcon(QtGui.QIcon('e.png'))

        self.BytePlot()

    def BytePlot(self):
        w = self.width
        h = len(self.data)/self.width
        if len(self.data) % self.width != 0:
            h += 1
        self.image = QtGui.QImage(w,h, QtGui.QImage.Format_RGB32)
        print "image size = %d | W %d H %d" % (len(self.data), self.image.width(), self.image.height())
        x,y = 0,0
        for b in self.data:
            r,g,b = ord(b),ord(b),ord(b)
            #r,g,b = random.randrange(256),random.randrange(256),random.randrange(256)
            if x >= self.image.width():
                x = 0
                y += 1
            self.image.setPixel(x,y,QtGui.qRgb(r,g,b))
            x += 1

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        sRect = QtCore.QRect(0, 0, self.image.width(), self.height)
        dRect = QtCore.QRect(0, 0, self.width, self.height)
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
file = Editor(data)
file.show()
sys.exit(app.exec_()) 
