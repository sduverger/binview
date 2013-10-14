#!/usr/bin/env python

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

import sys, array

class File(object):
    def __init__(self, name):
        self.name = name
        self.fd = open(name)
        self.data = self.fd.read()

    def close(self):
        self.fd.close()

class RenderArea(QtGui.QWidget):
    def __init__(self, name, file, act):
        super(RenderArea, self).__init__()
        self.setWindowTitle(name)
        self.file = file
        self.act = act
        self.preCalc()

    def preCalc(self):
        pass

    def render(self):
        pass

    def show(self):
        self.parentWidget().setMinimumSize(10,10)
        self.parentWidget().resize(640, 480)
        super(RenderArea, self).show()
        self.render() #now visible

    def update(self, file):
        self.file = file
        self.preCalc()
        self.render()

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        sRect = QtCore.QRect(0, 0, self.image.width(), self.height())
        dRect = QtCore.QRect(0, 0, self.width(), self.height())
        qp.drawImage(dRect, self.image, sRect)
        qp.end()

    def closeEvent(self, e):
        e.ignore()
        self.act.setChecked(False)

# BytePlot:
# . byte value is color (grey scale)
# . bytes order from binary gives coordinates
class BytePlot(RenderArea):
    def __init__(self, file, act):
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]
        super(BytePlot, self).__init__("Byte Plot", file, act)

    def render(self):
        w = self.width()
        h = len(self.file.data)/self.width()
        if len(self.file.data) % self.width() != 0:
            h += 1

        self.image = QtGui.QImage(self.file.data, w, h, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)

    def resizeEvent(self, e):
        if self.isVisible():
            self.render()

# DigraphPlot:
# . takes 2 bytes, 1st is X, 2nd is Y, color is fixed
# . for file size > 64KB, entropy may lead to a white 256x256 square
class DigraphPlot(RenderArea):
    def __init__(self, file, act):
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]
        super(DigraphPlot, self).__init__("Digraph Plot", file, act)

    def preCalc(self):
        ln = len(self.file.data)
        if ln % 2 != 0:
            ln -= 1

        self.pixels = array.array('B', 256*256*'\x00')

        for i in xrange(0,ln-1):
            x = ord(self.file.data[i])
            y = ord(self.file.data[i+1])
            self.pixels[x+y*256] = 255

        self.image = QtGui.QImage(self.pixels.tostring(), 256, 256, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)


# File Slider
class Slider(QtGui.QSlider):
    def __init__(self, file, act):
        super(Slider, self).__init__(QtCore.Qt.Horizontal)
        self.setWindowTitle("File Slider")
        self.file = file
        self.act = act
        self.valueChanged.connect(self.moved)

    def moved(self, value):
        print value

class BinView(QtGui.QMainWindow):
    def __init__(self):
        super(BinView, self).__init__()
        self.file = None

        self.initMain()
        self.initMdi()
        self.initMenu()
        self.info("ready")

    def initMain(self):
        self.setGeometry(0, 0, 640, 480)
        self.setWindowTitle("BinView")

    def initMdi(self):
        self.mdi = QtGui.QMdiArea()
        self.setCentralWidget(self.mdi)
        self.mdi.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdi.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

    def initViewAct(self, cls, name, shortcut):
        act = QtGui.QAction(name, self)
        act.setCheckable(True)
        act.setEnabled(False)
        act.setShortcuts(QtGui.QKeySequence(shortcut))
        act.toggled.connect(self.viewMode)
        act.cls = cls
        act.widget = None
        self.viewActs[cls] = act
        self.viewMenu.addAction(act)

    def initMenu(self):
        self.fileMenu = self.menuBar().addMenu("&File")

        self.openAct = QtGui.QAction("&Open", self)
        self.openAct.setShortcuts(QtGui.QKeySequence("Ctrl+o"))
        self.openAct.triggered.connect(self.openFile)
        self.fileMenu.addAction(self.openAct)

        self.exitAct = QtGui.QAction("&Exit", self)
        self.exitAct.setShortcuts(QtGui.QKeySequence("Ctrl+q"))
        self.exitAct.triggered.connect(self.terminate)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewActs = {}
        self.initViewAct(Slider, "&File slider", "Ctrl+s")
        self.initViewAct(BytePlot, "&Byte plot", "Ctrl+b")
        self.initViewAct(DigraphPlot, "&Digraph plot", "Ctrl+d")

    def info(self, msg):
        self.statusBar().showMessage(msg)

    def openFile(self):
        self.info("opening file")
        name = QtGui.QFileDialog.getOpenFileName(self)
        if not name:
            self.info("ready")
            return

        if self.file is not None:
            self.file.close()

        self.file = File(name)
        noview = True
        for cls,act in self.viewActs.iteritems():
            if not act.isEnabled():
                act.setEnabled(True)
            if act.widget is not None:
                act.widget.update(self.file)
            if act.isChecked():
                noview = False

        if noview: # default view
            self.viewActs[BytePlot].setChecked(True)

        self.info("loaded %s" % (self.file.name))

    def viewMode(self):
        act = self.sender()
        if act.isChecked():
            if act.widget is None:
                act.widget = act.cls(self.file, act)
                act.widget.setParent(self.mdi.addSubWindow(act.widget))
                act.widget.show()
            else:
                act.widget.parentWidget().show()
        elif act.widget is not None:
            act.widget.parentWidget().hide()

    def terminate(self):
        if self.file is not None:
            self.file.close()

        QtGui.QApplication.quit()

##
## main
##
app = QtGui.QApplication(sys.argv)
binview = BinView()
binview.show()
sys.exit(app.exec_())
