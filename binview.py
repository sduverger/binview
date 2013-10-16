#!/usr/bin/env python

from PyQt4 import Qt
from PyQt4 import QtGui
from PyQt4 import QtCore

import sys, os, mmap, array

class File(object):
    def __init__(self, name):
        self.name = name
        self.fd = open(name)
        self.size = os.stat(name).st_size
        self.offset = 0
        self.data = mmap.mmap(self.fd.fileno(), self.size, mmap.MAP_PRIVATE, mmap.PROT_READ)
        print "loaded file size %d" % self.size
        self.views = []

    #XXX: mutex
    def updateOffset(self, value):
        if value < self.size:
            self.offset = value
            print "updated file offset %d" % self.offset

        for v in self.views:
            print "file offset changed, calling update view"
            v.fileOffsetUpdated()

    def registerView(self, f):
        self.views.append(f)

    def close(self):
        self.fd.close()

class RenderArea(QtGui.QWidget):
    def __init__(self, parent, name, file, act):
        super(RenderArea, self).__init__(parent)
        self.setWindowTitle(name)
        self.parentWidget().resize(270, 360)
        self.file = file
        self.act = act
        self.need_update = True
        self.preCalc()

    def preCalc(self):
        if self.need_update:
            self.need_update = False

    def render(self):
        if self.need_update:
            self.preCalc()

    def show(self):
        super(RenderArea, self).show()
        self.render()

    def fileUpdated(self, file):
        self.file = file
        self.file.registerView(self)
        self.fileOffsetUpdated()

    def fileOffsetUpdated(self):
        print self,"fileOffsetUpdated"
        self.need_update = True
        if self.isVisible():
            self.render()
            self.repaint()

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
    def __init__(self, parent, file, act):
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]
        super(BytePlot, self).__init__(parent, "Byte Plot", file, act)
        self.file.registerView(self)

    def render(self):
        super(BytePlot, self).render()
        print "requested W*H %d %d" % (self.width(), self.height())
        self.w = min(self.width(),  self.file.size - self.file.offset)
        self.h = max(min(self.height(), (self.file.size - self.file.offset)/self.w), 1)
        print "effective W*H %d %d" % (self.w, self.h)
        self.s = self.file.offset
        self.e = self.file.offset+self.w*self.h
        print "offsets %d - %d" % (self.s,self.e)

        self.image = QtGui.QImage(self.file.data[self.s:self.e], \
                                      self.w, self.h, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)

    def resizeEvent(self, e):
        if self.isVisible():
            self.render()

# DigraphPlot:
# . takes 2 bytes, 1st is X, 2nd is Y, color is fixed
# . for file size > 64KB, entropy may lead to a white 256x256 image
class DigraphPlot(RenderArea):
    def __init__(self, parent, file, act):
        self.grey_palette = [QtGui.qRgb(i,i,i) for i in range(256)]
        super(DigraphPlot, self).__init__(parent, "Digraph Plot", file, act)
        self.file.registerView(self)

    def preCalc(self):
        super(DigraphPlot, self).preCalc()
        ln = min(65536, self.file.size - self.file.offset)
        if ln%2 != 0:
            ln -= 1

        self.pixels = array.array('B', 65536*'\x00')

        for i in xrange(0,ln-1):
            x = ord(self.file.data[self.file.offset+i])
            y = ord(self.file.data[self.file.offset+i+1])
            self.pixels[x+y*256] = 255

        self.image = QtGui.QImage(self.pixels.tostring(), 256, 256, QtGui.QImage.Format_Indexed8)
        self.image.setColorTable(self.grey_palette)


# File Slider
class Slider(QtGui.QWidget):
    def __init__(self, parent, file, act):
        super(Slider, self).__init__(parent)
        self.setWindowTitle("File Slider")
        self.file = file
        self.act = act
        self.layout = QtGui.QVBoxLayout()

        self.label = QtGui.QLabel(self.renderText(0), self)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.layout.addWidget(self.label)

        self.cursor = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.cursor.setRange(0, self.file.size)
        self.layout.addWidget(self.cursor)

        self.gbox = QtGui.QGroupBox()
        self.glayout = QtGui.QHBoxLayout()
        self.gtxt = QtGui.QLineEdit()
        self.gtxt.returnPressed.connect(self.gotoOffset)
        self.goto = QtGui.QPushButton("&Goto")
        self.goto.clicked.connect(self.gotoOffset)
        self.glayout.addWidget(self.gtxt)
        self.glayout.addWidget(self.goto)
        self.gbox.setLayout(self.glayout)
        self.layout.addWidget(self.gbox)

        self.bstate = 0
        self.bbox = QtGui.QGroupBox()
        self.blayout = QtGui.QHBoxLayout()
        self.play = QtGui.QPushButton("&Play")
        self.play.clicked.connect(self.playClicked)
        self.blayout.addWidget(self.play)
        self.stop = QtGui.QPushButton("&Stop")
        self.stop.clicked.connect(self.stopClicked)
        self.blayout.addWidget(self.stop)
        self.bbox.setLayout(self.blayout)
        self.layout.addWidget(self.bbox)

        self.setLayout(self.layout)
        self.cursor.valueChanged.connect(self.moved)

    def gotoOffset(self):
        txt = str(self.gtxt.text())
        if txt.startswith("0x"):
            base=16
        else:
            base=10
        value = int(txt,base)
        if value >= 0 and value <= self.file.size:
            self.moved(value)

    def playClicked(self):
        if self.bstate == 1: #paused
            self.bstate = 2
            self.play.setText("&Play")
        else: #played
            self.play.setText("&Pause")
            self.bstate = 1

    def stopClicked(self):
        if self.bstate == 0:
            return
        self.bstate = 0
        self.play.setText("&Play")

    def renderText(self, value):
        return "<code><center><b>%d</b></center>0x%x<br>&nbsp;&nbsp;%x</code>" % (value,value,value)

    def moved(self, value):
        self.label.setText(self.renderText(value))
        self.file.updateOffset(value)

    def fileUpdated(self, file):
        self.file = file
        self.cursor.setRange(0, self.file.size)
        self.setSlider(self.file.offset)

    def setSlider(self, value):
        self.cursor.setSliderPosition(value)
        self.label.setText(self.renderText(value))

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
                act.widget.fileUpdated(self.file)
            if act.isChecked():
                noview = False

        if noview: # default view
            self.viewActs[BytePlot].setChecked(True)

        self.info("loaded %s" % (self.file.name))

    def viewMode(self):
        act = self.sender()
        if act.isChecked():
            if act.widget is None:
                subwin = QtGui.QMdiSubWindow()
                act.widget = act.cls(subwin, self.file, act)
                subwin.setWidget(act.widget)
                self.mdi.addSubWindow(subwin)
                act.widget.show()
            else:
                act.widget.parentWidget().show()
                act.widget.show()
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
