#!/usr/bin/python3
# -*- coding: utf-8 -*-
from level10m import *

import sys, os, re, json
from PyQt4 import QtGui, QtCore, Qt


from xdg.BaseDirectory import *


buttonList = (
    ("Left Button", 0x0E),
    ("Right Button", 0x0F),
    ("Whell", 0x10),
    ("A Button", 0x12),
    ("B Button", 0x11),
    ("C Button", 0x16),
    ("D Button", 0x15),
    ("Left", 0x13),
    ("Right", 0x14),
    ("Up", 0x17),
    ("Down", 0x18)
)

colorList = (
    QtGui.QColor("#F12020"), # red
    QtGui.QColor("#25B221"),  # verde scuro
    QtGui.QColor("#94CE21"), # giallo
    QtGui.QColor("#0030DE"), # Blu
    QtGui.QColor("#9B33BC"), # viola
    QtGui.QColor("#295DAD"), # blue chiaro
    QtGui.QColor("#7FA5B0") # verde acqua
)

class dpiSlider(QtGui.QWidget):

    def __init__(self, profile, level, m10, parent=None):
        super(dpiSlider, self).__init__(parent)

        self.m10 = m10
        self.level = level
        self.profile = profile
        self.__oldvalue = 0

        vbox = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel()
        self.vslider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.radio = QtGui.QRadioButton()

        self.label.setText("8200")

        vbox.addWidget(self.label)
        vbox.addWidget(self.vslider)
        vbox.addWidget(self.radio)
        self.setLayout( vbox )

        self.vslider.setRange(1, 164)


        self.vslider.valueChanged[int].connect(self.slider_value_onchange)
        self.parent().parent().trigger.connect(self.apply_value)

        currentValueX, currentValueY = list(self.m10.get_dpi_value(self.profile, self.level))
        self.vslider.setValue(currentValueX)
        self.__oldvalue = currentValueX


    def slider_value_onchange(self):
        self.label.setText(str(50*self.vslider.value()))


    def apply_value(self, value):
        xy = self.vslider.value()
        if xy is not self.__oldvalue:
            self.__oldvalue = xy
            self.m10.set_dpi_value(self.profile, self.level, xy, xy)


class mouseButton(QtGui.QWidget):
    def __init__(self, profile, buttonIndex, buttonName, m10, parent=None):
        super(mouseButton, self).__init__(parent)

        self.m10 = m10
        self.profile = profile
        self.buttonIndex = buttonIndex
        self.__oldvalue = -1

        hbox = QtGui.QHBoxLayout()
        self.label = QtGui.QLabel()
        self.combo = QtGui.QComboBox()

        for action in predef_assign:
            self.combo.addItem(action[1])

        self.label.setText(buttonName) #buttonName

        # disable the macro set
        self.combo.model().item(13).setEnabled(False)
        self.combo.model().item(13).setForeground(QtGui.QColor('grey'))

        hbox.addWidget(self.label)
        hbox.addWidget(self.combo)
        self.setLayout( hbox )

        currentFunctionIndex = self.m10.get_button_assign(self.profile, self.buttonIndex)
        self.combo.setCurrentIndex(currentFunctionIndex)
        self.__oldvalue = currentFunctionIndex

        self.parent().parent().trigger.connect(self.apply_value)

    def apply_value(self, value):
        currentFunctionIndex = self.combo.currentIndex()
        if currentFunctionIndex is not self.__oldvalue:
            self.__oldvalue = currentFunctionIndex

            self.m10.set_button(self.profile, self.buttonIndex, predef_assign[currentFunctionIndex][0])


class colorPick(QtGui.QGroupBox):
    def __init__(self, profile, lightIndex, lightName, m10, parent=None):
        super(colorPick, self).__init__(parent)
        self.m10 = m10
        self.profile = profile
        self.lightIndex = lightIndex

        self.__oldvalue = lightIndex

        self.setTitle(lightName)


        lightValue = self.m10.getLight(self.profile, self.lightIndex)

        vbox= QtGui.QVBoxLayout()

        self.combo = QtGui.QComboBox()
        model = self.combo.model()

        for color in colorList:
            item = QtGui.QStandardItem("")
            item.setBackground(color)
            model.appendRow(item)

        self.combo.currentIndexChanged[int].connect(self.combo_onchange)
        self.combo.setCurrentIndex(lightValue[0]-1)
        self.combo.setStyleSheet('QComboBox:focus {background-color: rgb' + str(colorList[lightValue[0]-1].getRgb()) + '; border: none;outline: none;}\
        QComboBox {background-color: rgb' + str(colorList[lightValue[0]-1].getRgb()) + '; border: none;outline: none;}')


        self.offState = QtGui.QRadioButton("Off")
        self.steadyState = QtGui.QRadioButton("Steady")
        self.pulseState = QtGui.QRadioButton("Pulse")
        self.battleState = QtGui.QRadioButton("Battle")

        if lightValue[1] == 0:
            self.offState.setChecked(True);
        elif lightValue[1] == 1:
            self.steadyState.setChecked(True);
        elif lightValue[1] == 2:
            self.pulseState.setChecked(True);
        elif lightValue[1] == 3:
            self.battleState.setChecked(True);

        vbox.addWidget(self.combo)
        vbox.addWidget(self.offState)
        vbox.addWidget(self.steadyState)
        vbox.addWidget(self.pulseState)
        vbox.addWidget(self.battleState)
        self.setLayout( vbox )


    def apply_value(self, value):
        effect = -1
        if self.offState.isChecked() == True:
            effect = 0
        elif self.steadyState.isChecked() == True:
            effect = 1
        elif self.pulseState.isChecked() == True:
            effect = 2
        elif self.battleState.isChecked() == True:
            effect = 3
        color = self.combo.currentIndex()

        if [color, effect] is not self.__oldvalue:
            self.__oldvalue = [color, effect]
            self.m10.setLight(self.profile, self.lightIndex, color, effect)


    def combo_onchange(self):
        index = self.combo.currentIndex()
        self.combo.setStyleSheet('QComboBox:focus {background-color: rgb' + str(colorList[index].getRgb()) + '; border: none;outline: none;}\
        QComboBox {background-color: rgb' + str(colorList[index].getRgb()) + '; border: none;outline: none;}')

class profileTab(QtGui.QWidget):
    """docstring for """
    def __init__(self, profile, m10, parent=None):
        super(profileTab, self).__init__(parent)

        self.profile = profile
        self.m10 = m10
        self.m10.open()

        self.buttonCollection = []
        self.dpiCollection = []

        self.grid = QtGui.QHBoxLayout()
        self.setLayout(self.grid)

        ####################
        # Buttons
        ####################
        buttonContainer = QtGui.QVBoxLayout()
        buttonGroupBox = QtGui.QGroupBox("Buttons")
        buttonGroupBox.setLayout(buttonContainer)

        for buttonIndex, buttonName in enumerate(buttonList):
            self.buttonCollection.append(mouseButton(self.profile, buttonName[1], buttonName[0], self.m10, self))
            buttonContainer.addWidget(self.buttonCollection[buttonIndex])

        self.grid.addWidget(buttonGroupBox)

        ####################
        #   Dpi
        ####################
        dpiContainer = QtGui.QHBoxLayout()
        dpiGroupBox = QtGui.QGroupBox("Dpi")
        # dpiGroupBox.setAlignment(QtCore.Qt.AlignLeft)
        dpiGroupBox.setLayout(dpiContainer)
        # dpiGroupBox.setStyleSheet("QGroupBox::title{subcontrol-origin: margin;}")


        for level in range(0,4):
            self.dpiCollection.append(dpiSlider(self.profile, level, self.m10, self))
            dpiContainer.addWidget(self.dpiCollection[level])

        self.grid.addWidget(dpiGroupBox)


        #############
        colorVbox = QtGui.QVBoxLayout()
        # colorGroupBox = QtGui.QGroupBox("Lights")
        # colorGroupBox.setLayout(colorVbox)

        colorSx = colorPick(self.profile, 0, "Sx", self.m10, self)
        colorVbox.addWidget(colorSx)
        colorWheel = colorPick(self.profile, 1, "wheel", self.m10, self)
        colorVbox.addWidget(colorWheel)
        colorLogo = colorPick(self.profile, 2, "Logo", self.m10, self)
        colorVbox.addWidget(colorLogo)

        self.grid.addLayout(colorVbox)



        self.m10.close()

class maccgui(QtGui.QMainWindow):
    trigger = QtCore.pyqtSignal(str)

    def __init__(self):
        super(maccgui, self).__init__()
        self.initUI()

    def closeEvent(self,event):
        self.m10.close()

    def initUI(self):

        self.profileTabs = []
        self.m10 = level10_usb()


        tabWidget = QtGui.QTabWidget()

        profile0_tab = profileTab(0, self.m10, self)
        profile1_tab = profileTab(1, self.m10, self)
        profile2_tab = profileTab(2, self.m10, self)
        profile3_tab = profileTab(3, self.m10, self)
        profile4_tab = profileTab(4, self.m10, self)

        tabWidget.addTab(profile0_tab, "Profile 1")
        tabWidget.addTab(profile1_tab, "Profile 2")
        tabWidget.addTab(profile2_tab, "Profile 3")
        tabWidget.addTab(profile3_tab, "Profile 4")
        tabWidget.addTab(profile4_tab, "Profile 5")



        #
        #   Finish
        #


        _widget = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout(_widget)
        self.setCentralWidget(_widget)
        vbox.addWidget(tabWidget)

        applyBtn = QtGui.QPushButton(self)
        applyBtn.setIcon(self.style().standardIcon(QtGui.QStyle.SP_DialogApplyButton))
        applyBtn.setIconSize(QtCore.QSize(24,24))
        applyBtn.setMaximumSize(QtCore.QSize(32,32))
        applyBtn.setToolTip('Load profile')
        applyBtn.clicked.connect(self.load_profile)

        vbox.addWidget(applyBtn)

        # self.setGeometry(300, 300, 500, 770)
        self.setGeometry(300, 300, 500, 170)
        self.setWindowTitle('Thermaltake Level10 M Gui')
        self.show()

    def load_profile(self):
        print("commit")
        self.trigger.emit("xx")
        self.m10.commitChanges()

def main():
    app = QtGui.QApplication(sys.argv)
    ex = maccgui()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
