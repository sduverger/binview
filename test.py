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

        self.modes = {"bytePlot":[self.preBytePlot,self.bytePlot,self],
                      "digraphByte":[self.preDigraphByte,self.digraphByte,self],
                      "digraphWord":[self.preDigraphWord,self.digraphWord,self]
                      }

        self.mode = "bytePlot"
        #self.mode = "digraphByte"
        #self.mode = "digraphWord"

        self.modes[self.mode][0]()
        self.modes[self.mode][1]()

    def initUI(self):
        QtGui.QWidget.__init__(self)
        QtGui.QShortcut(QtGui.QKeySequence("Esc"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("q"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+q"), self, self.terminate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+c"), self, self.terminate)

    # BytePlot:
    # each byte from data is a color (grey scale)
    # order of bytes into the binary gives coordinates
    def preBytePlot(self):
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]

    def bytePlot(self):
        w = self.width()
        h = len(self.data)/self.width()
        if len(self.data) % self.width() != 0:
            h += 1

        self.image = QtGui.QImage(self.data, w, h, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)

    # Digraph:
    # takes 2 bytes, 1st is X, 2nd is Y, color is fixed
    def preDigraphByte(self):
        w = 2**8
        h = 2**8
        self.image = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)

        ln = len(self.data)
        if ln % 2 != 0:
            ln -= 1
        self.points = []
        # for i in xrange(0,ln,2):
        #     x = ord(self.data[i])
        #     y = ord(self.data[i+1])
        #     self.points.append((x,y))

        for i in xrange(0,ln-1):
            x = ord(self.data[i])
            y = ord(self.data[i+1])
            self.points.append((x,y))


    def digraphByte(self): #limited to 64KB files
        self.image.fill(0)
        c = QtGui.qRgb(255,255,255)
        for x,y in self.points:
            self.image.setPixel(x,y,c)

    # Digraph:
    # takes 4 bytes, b1<<8|b2 is X,  b3<<8|b4 is Y, color is fixed
    def preDigraphWord(self):
        self.xmax = self.ymax = 0
        self.points = []
        for i in xrange(0,len(self.data),4):
            x = ord(self.data[i])<<8|ord(self.data[i+1])
            y = ord(self.data[i+2])<<8|ord(self.data[i+3])
            self.points.append((x,y))
            if x > self.xmax:
                self.xmax = x
            if y > self.ymax:
                self.ymax = y
        print "precomputed xmax %d ymax %d" % (self.xmax, self.ymax)

    def digraphWord(self): #limited to 4GB files
        w = self.xmax
        h = self.ymax
        c = QtGui.qRgb(255,255,255)
        # self.image = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)
        # for x,y in self.points:
        #     self.image.setPixel(x,y,c)

    def resizeEvent(self, e):
        if self.mode == "bytePlot":
            self.modes[self.mode][1]()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        sRect = QtCore.QRect(0, 0, self.image.width(), self.height())
        dRect = QtCore.QRect(0, 0, self.width(), self.height())
        qp.drawImage(dRect, self.image, sRect)
        qp.end()

    def terminate(self):
        QtGui.QApplication.quit()

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
