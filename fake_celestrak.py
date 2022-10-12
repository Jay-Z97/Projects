from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QHBoxLayout, QGroupBox, QVBoxLayout, QLineEdit)
from PyQt5.QtGui import *

import sys
import matplotlib
import random
matplotlib.use('Qt5Agg')
import matplotlib.image as mpimg
from skyfield.api import Loader, EarthSatellite, load, wgs84
import datetime as dt
from urllib.request import urlopen

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, QTime, Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=1700, height=900, dpi=1):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class ProgramWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)


        self.now = dt.datetime.utcnow()
        self.active_sats_list = []
        self.all_sats_list = ['X2','X4','X6','X7','X8','X9','X11','X12','X13','X14','X15','X16','X17','X18','X19','X20','X24']
        self.currentTime = dt.datetime(year=self.now.year, month = self.now.month, day =self.now.day, hour =self.now.hour, minute=self.now.minute, second=self.now.second)
        self.displayTxtTime = self.currentTime.strftime("%H:%M:%S")
        self.displayTxtDate = self.currentTime.strftime("%d.%m.%Y")
        self.setup_main_window()
        self.set_window_layout()
    
        stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        satellites = load.tle_file(stations_url)
        #print('Loaded', len(satellites), 'satellites')
        by_name = {sat.name: sat for sat in satellites}
        self.ts = load.timescale()

        self.sat = []
        i=0
        for sat in self.all_sats_list:
            self.sat.append(by_name['ICEYE-'+sat])
            print(self.sat[i])
            i=i+1


        self.update_plot()

        self.show()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.timeout.connect(self.update_time_label)
        self.setTimeButton.clicked.connect(self.setTimeButton_on_click)
        self.stopTimeButton.clicked.connect(self.stopTimeButton_on_click)
        self.setCurrentTimeButton.clicked.connect(self.setCurrentTimeButton_on_click)
        self.setDateButton.clicked.connect(self.setDateButton_on_click)
        self.timer.start()


    def setTimeButton_on_click(self):
        textboxValue = self.textboxTime.text()
        self.currentTime = dt.datetime(year=self.now.year, month = self.now.month, day = self.now.day, hour =int(textboxValue[0:2]), minute=int(textboxValue[3:5]),second=int(textboxValue[6:8]))
        
    def setDateButton_on_click(self):
        textboxValue = self.textboxDate.text()
        self.currentTime = dt.datetime(year=int(textboxValue[6:]), month =int(textboxValue[3:5]), day =int(textboxValue[0:2]), hour =self.now.hour, minute=self.now.minute, second=self.now.second)
        
    def setCurrentTimeButton_on_click(self):
        self.now = dt.datetime.utcnow()
        self.currentTime = dt.datetime(year=self.now.year, month = self.now.month, day = self.now.day, hour =self.now.hour, minute=self.now.minute, second=self.now.second)
        

    def stopTimeButton_on_click(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()

    def addSatellite(self, number, button):
        if button.isChecked():
            self.active_sats_list.append(number)
        else:
            self.active_sats_list.remove(number)
        #print(self.active_sats_list)




    def setup_main_window(self):
        self.centralwidget = QWidget()
        self.setCentralWidget(self.centralwidget)
        self.resize( 1900, 1000  )
        self.setWindowTitle( "Fake Celestrak" )




    def update_time_label(self):

        self.currentTime = self.currentTime + dt.timedelta(seconds=1)
        self.displayTxtTime = self.currentTime.strftime("%H:%M:%S")
        self.displayTxtDate = self.currentTime.strftime("%d.%m.%Y")
        self.lblTime.setText(self.displayTxtTime)
        self.lblDate.setText(self.displayTxtDate)
        self.lblTime.setGeometry(200, 150, 100, 40)


    def update_plot(self):

        self.canvas.axes.cla()  # Clear the canvas.
        
        self.position = []
        
        for j in self.active_sats_list:
            cols = []
            for i in range(94):
                t = self.ts.utc(self.currentTime.year, self.currentTime.month, self.currentTime.day, self.currentTime.hour, self.currentTime.minute+i-47, self.currentTime.second)
                cols.append(self.sat[j].at(t))
            self.position.append(cols)



        self.canvas.axes.plot([-110, -40],[-10,10],'red')
        self.canvas.axes.plot([-40, 40],[10,-40],'red')
        self.canvas.axes.plot([40, -60],[-40,-50],'red')
        self.canvas.axes.plot([-60, -110],[-50,-10],'red')
        self.canvas.axes.text(-95, -11, "SAA", color="red", size =13)

        x = 0
        for j in self.active_sats_list:


            for i in range(1,94):
                lat, lon = wgs84.latlon_of(self.position[x][i-1])
                lat1, lon1 = wgs84.latlon_of(self.position[x][i])

                if(lon1.degrees<lon.degrees):
                    self.canvas.axes.plot([lon.degrees, lon1.degrees],[lat.degrees,lat1.degrees],'blue')
                else:
                    self.canvas.axes.plot([lon.degrees+360, lon1.degrees],[lat.degrees,lat1.degrees],'blue')
                    self.canvas.axes.plot([lon.degrees, lon1.degrees-360],[lat.degrees,lat1.degrees],'blue')
            

            #Getting precise position
            t = self.ts.utc(self.currentTime.year, self.currentTime.month, self.currentTime.day, self.currentTime.hour, self.currentTime.minute, self.currentTime.second)
            t0 = self.ts.utc(self.currentTime.year, self.currentTime.month, self.currentTime.day, self.currentTime.hour, self.currentTime.minute, self.currentTime.second-5)
            lat, lon = wgs84.latlon_of(self.sat[j].at(t0))
            lat1, lon1 = wgs84.latlon_of(self.sat[j].at(t))
            self.canvas.axes.text(lon.degrees-8.5, lat.degrees-4.5, self.all_sats_list[j], color="white", size =12)
            if(lon1.degrees<lon.degrees):
                self.canvas.axes.plot([lon.degrees, lon1.degrees],[lat.degrees,lat1.degrees],'white')
            else:
                self.canvas.axes.plot([lon.degrees+360, lon1.degrees],[lat.degrees,lat1.degrees],'white')
                self.canvas.axes.plot([lon.degrees, lon1.degrees-360],[lat.degrees,lat1.degrees],'white')

            x = x+1
        
        # Trigger the canvas to update and redraw.
        background = mpimg.imread('HQmap.jpg')
        self.canvas.axes.imshow(background, extent=[-180, 180, -90, 90])#, aspect='auto', cmap='gray')


        self.canvas.draw()



    def set_window_layout(self):
        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.canvas = MplCanvas(self, width=200, height=100, dpi=100)
        self.canvas.axes.set_xlim([-180, 180])
        self.canvas.axes.set_ylim([-90, 90])
        background = mpimg.imread('HQmap.jpg')
        self.canvas.axes.imshow(background, extent=[-180, 180, -90, 90])#, aspect='auto', cmap='gray')


        self.horizontalLayout = QHBoxLayout(self.centralwidget) 
        self.horizontalLayout.addWidget( self.canvas )

        self.horizontalGroupBox = QGroupBox( "Control panel                " )
        self.horizontalLayout.addWidget( self.horizontalGroupBox )

        self.main_vertical_layout = QVBoxLayout()
        self.horizontalGroupBox.setLayout( self.main_vertical_layout )
        self.lblDate = QLabel(self.displayTxtDate)
        self.lblDate.setFont(QFont('Arial', 20))
        self.lblTime = QLabel(self.displayTxtTime)
        self.lblTime.setFont(QFont('Arial', 20))
        self.textboxTime = QLineEdit(self)
        self.setTimeButton = QPushButton('Change time \n HH:MM:SS', self)    
        self.stopTimeButton = QPushButton('Stop/Start time',self)
        self.setCurrentTimeButton = QPushButton('Set Current Time', self)    
        self.textboxDate = QLineEdit(self)
        self.setDateButton = QPushButton('Change date \n DD:MM:YYYY', self)



        self.main_vertical_layout.addStretch(0)
        self.main_vertical_layout.addWidget(self.lblDate )
        self.main_vertical_layout.addWidget(self.lblTime )
        self.main_vertical_layout.addWidget(self.textboxTime )
        self.main_vertical_layout.addWidget(self.setTimeButton)
        self.main_vertical_layout.addWidget(self.setCurrentTimeButton)
        self.main_vertical_layout.addWidget(self.stopTimeButton)
        self.main_vertical_layout.addWidget(self.textboxDate )
        self.main_vertical_layout.addWidget(self.setDateButton)
        self.main_vertical_layout.addStretch(1)

        self.X2=QPushButton('ICEYE-X2', self)
        self.X2.setCheckable(True)
        self.X2.clicked.connect(lambda ch: self.addSatellite(0,self.X2))
        self.main_vertical_layout.addWidget(self.X2)

        self.X4=QPushButton('ICEYE-X4', self)
        self.X4.setCheckable(True)
        self.X4.clicked.connect(lambda ch: self.addSatellite(1,self.X4))
        self.main_vertical_layout.addWidget(self.X4)

        self.X6=QPushButton('ICEYE-X6', self)
        self.X6.setCheckable(True)
        self.X6.clicked.connect(lambda ch: self.addSatellite(2,self.X6))
        self.main_vertical_layout.addWidget(self.X6)

        self.X7=QPushButton('ICEYE-X7', self)
        self.X7.setCheckable(True)
        self.X7.clicked.connect(lambda ch: self.addSatellite(3,self.X7))
        self.main_vertical_layout.addWidget(self.X7)

        self.X8=QPushButton('ICEYE-X8', self)
        self.X8.setCheckable(True)
        self.X8.clicked.connect(lambda ch: self.addSatellite(4,self.X8))
        self.main_vertical_layout.addWidget(self.X8)

        self.X9=QPushButton('ICEYE-X9', self)
        self.X9.setCheckable(True)
        self.X9.clicked.connect(lambda ch: self.addSatellite(5,self.X9))
        self.main_vertical_layout.addWidget(self.X9)

        self.X11=QPushButton('ICEYE-X11', self)
        self.X11.setCheckable(True)
        self.X11.clicked.connect(lambda ch: self.addSatellite(6,self.X11))
        self.main_vertical_layout.addWidget(self.X11)

        self.X12=QPushButton('ICEYE-X12', self)
        self.X12.setCheckable(True)
        self.X12.clicked.connect(lambda ch: self.addSatellite(7,self.X12))
        self.main_vertical_layout.addWidget(self.X12)
        
        self.X13=QPushButton('ICEYE-X13', self)
        self.X13.setCheckable(True)
        self.X13.clicked.connect(lambda ch: self.addSatellite(8,self.X13))
        self.main_vertical_layout.addWidget(self.X13)
        
        self.X14=QPushButton('ICEYE-X14', self)
        self.X14.setCheckable(True)
        self.X14.clicked.connect(lambda ch: self.addSatellite(9,self.X14))
        self.main_vertical_layout.addWidget(self.X14)
        
        self.X15=QPushButton('ICEYE-X15', self)
        self.X15.setCheckable(True)
        self.X15.clicked.connect(lambda ch: self.addSatellite(10,self.X15))
        self.main_vertical_layout.addWidget(self.X15)

        self.X16=QPushButton('ICEYE-X16', self)
        self.X16.setCheckable(True)
        self.X16.clicked.connect(lambda ch: self.addSatellite(11,self.X16))
        self.main_vertical_layout.addWidget(self.X16)
        
        self.X17=QPushButton('ICEYE-X17', self)
        self.X17.setCheckable(True)
        self.X17.clicked.connect(lambda ch: self.addSatellite(12,self.X17))
        self.main_vertical_layout.addWidget(self.X17)
        
        self.X18=QPushButton('ICEYE-X18', self)
        self.X18.setCheckable(True)
        self.X18.clicked.connect(lambda ch: self.addSatellite(13,self.X18))
        self.main_vertical_layout.addWidget(self.X18)
        
        self.X19=QPushButton('ICEYE-X19', self)
        self.X19.setCheckable(True)
        self.X19.clicked.connect(lambda ch: self.addSatellite(14,self.X19))
        self.main_vertical_layout.addWidget(self.X19)
        
        self.X20=QPushButton('ICEYE-X20', self)
        self.X20.setCheckable(True)
        self.X20.clicked.connect(lambda ch: self.addSatellite(15,self.X20))
        self.main_vertical_layout.addWidget(self.X20)

        self.X24=QPushButton('ICEYE-X24', self)
        self.X24.setCheckable(True)
        self.X24.clicked.connect(lambda ch: self.addSatellite(16,self.X24))
        self.main_vertical_layout.addWidget(self.X24)


        


def main():
    app = QApplication(sys.argv)
    programWindow = ProgramWindow()

    programWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
