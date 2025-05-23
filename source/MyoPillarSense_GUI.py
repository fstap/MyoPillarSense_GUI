from __future__ import annotations
from typing import *
import sys
import os
from PyQt6 import QtWidgets, uic, QtCore
from matplotlib.backends.qt_compat import QtCore, QtWidgets
# from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qtagg import FigureCanvas
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import serial
import time
import sys
from datetime import datetime
import csv
import serial.tools.list_ports
import os
import requests
from gui import Ui_main


class ApplicationWindow(QtWidgets.QMainWindow,Ui_main):
    
    def __init__(self):
        super().__init__()
        Ui_main.__init__(self)
        self.setupUi(self)
        self.version = 0.1
        self.ser = None
        self.check_version()
        self.start_timer()
        self.measuring = 0
        self.timedMeasuring = 0
        self.versLbl.setText(f"Version: {self.version}")
        self.measBtn.clicked.connect(self.measBtn_click)
        self.saveBtn.clicked.connect(self.saveBtn_click)
        self.savePathBtn.clicked.connect(self.savePathBtn_click)
        self.timedMeasBtn.clicked.connect(self.timedMeasBtn_click)
        self.ch1Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=1, parent=self)
        self.ch2Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=2, parent=self)
        self.ch3Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=3, parent=self)
        self.ch4Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=4, parent=self)
        self.ch5Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=5, parent=self)
        self.ch6Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=6, parent=self)
        self.ch7Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=7, parent=self)
        self.ch8Fig = FastDrawingCanvas(x_len=1000, y_range=[0, 4100], interval=0.1,channel=8, parent=self)
        self.chList = [self.ch1Fig,self.ch2Fig,self.ch3Fig,self.ch4Fig,self.ch5Fig,self.ch6Fig,self.ch7Fig,self.ch8Fig]
        self.chGrid.addWidget(self.ch1Fig, 0, 0)
        self.chGrid.addWidget(self.ch2Fig, 0, 1)
        self.chGrid.addWidget(self.ch3Fig, 0, 2)
        self.chGrid.addWidget(self.ch4Fig, 0, 3)
        self.chGrid.addWidget(self.ch5Fig, 1, 0)
        self.chGrid.addWidget(self.ch6Fig, 1, 1)
        self.chGrid.addWidget(self.ch7Fig, 1, 2)
        self.chGrid.addWidget(self.ch8Fig, 1, 3)
        self.save_path = os.getcwd()
        self.saveText.setPlainText(self.save_path )
        # # 3. Show
        self.show()
        return
    
    def check_version(self):  
        try:
            url = "https://github.com/fstap/MyoPillarSense_GUI/raw/refs/heads/main/VERSION"
            response = requests.get(url)
            if response.status_code == 200:
                if response.text == f"{self.version}":
                    print("Newest version installed.")
                else:
                    print("Update available.")
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
                    msg.setText("There is a new version available: {response.text}. Please visit https://github.com/fstap/MyoPillarSense_GUI to download the newest version.")
                    msg.setWindowTitle("Update available")
                    msg.exec()
        except:
            print("No internet connection.")
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText("Update check failed, no internet available.")
            msg.setWindowTitle("Update check failed")
            msg.exec()


    def timedMeasBtn_click(self):
        if self.timedMeasuring == 0:
            time = self.hrsTedit.time()
            seconds = time.hour() * 3600 + time.minute() * 60 + time.second()
            
            timeMnts = self.mntsTedit.time()
            secondsMnts = timeMnts.minute() * 60 + timeMnts.second()
            
            if not seconds > secondsMnts:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
                msg.setText("The repeating interval must be larger than the measurement length.")
                msg.setWindowTitle("Error")
                msg.exec()
                return
            
            self.timedMeasuring = 1
            self.timedMeasBtn.setText("Stop timed measurement")
            self.measLbl.setText("Timed measurement running.")
            self.saveBtn.setEnabled(False)
            self.measBtn.setEnabled(False)
            self.aimedStartTimer = QtCore.QTimer(self)
            self.aimedStartTimer.timeout.connect(self.aimedStartTimer_tick)        
            self.aimedStartTimer.start(1000)
        else:
            self.timedMeasuring = 0
            self.timedMeasBtn.setText("Start timed measurement")
            self.measLbl.setText("No measurement running.")
            self.saveBtn.setEnabled(False)
            self.measBtn.setEnabled(True)
            self.end_measurement()
            try:
                self.mntsTimer.stop()
            except:
                pass
            try:
                self.hrsTimer.stop()
            except:
                pass
            self.aimedStartTimer.stop()            
    
    def aimedStartTimer_tick(self):
        current_time = QtCore.QTime.currentTime()
        aimedStartTime = self.fromTedit.time()
        if current_time.hour() == aimedStartTime.hour() and current_time.minute() == aimedStartTime.minute():
            time = self.hrsTedit.time()
            seconds = time.hour() * 3600 + time.minute() * 60 + time.second()
            self.hrsTimer = QtCore.QTimer(self)
            self.hrsTimer.timeout.connect(self.hrsTimer_tick)        
            self.hrsTimer.start(seconds*1000)
            self.aimedStartTimer.stop()
            self.hrsTimer_tick()
    
    def hrsTimer_tick(self):
        self.mntsTimer = QtCore.QTimer(self)
        self.mntsTimer.timeout.connect(self.mntsTimer_tick)        
        time = self.mntsTedit.time()
        seconds = time.minute() * 60 + time.second()
        self.start_measurement()
        self.mntsTimer.start(seconds*1000)
        
    def mntsTimer_tick(self):
        self.end_measurement()
        self.saveBtn_click()
        self.mntsTimer.stop()
    
    def savePathBtn_click(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            selected_path = dialog.selectedFiles()[0]
            self.save_path = selected_path
            self.saveText.setPlainText(selected_path)
        
    def saveBtn_click(self):
        #using csv instead of pandas to reduce the filesize of the compiled .exe
        headers = []
        columns = []
        for fig in self.chList:
            headers.append(f"CH{fig.channel}X")
            headers.append(f"CH{fig.channel}Y")
            columns.append(list(fig.xbuf))
            columns.append(list(fig.ybuf))
        
        max_len = max(len(col) for col in columns)
        
        for i, col in enumerate(columns):
            if len(col) < max_len:
                columns[i] = col + [''] * (max_len - len(col))
        
        rows = zip(*columns)
        
        now = datetime.now()
        folder = f"{self.save_path}/{now.strftime('%m%d%Y')}"
        os.makedirs(folder, exist_ok=True)
        filename = f"{folder}/MyoPillarSense_data_{now.strftime('%H_%M_%S')}.csv"

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
                
    def measBtn_click(self):
        if self.measuring == 1:
            self.saveBtn.setEnabled(True)
            self.timedMeasBtn.setEnabled(True)
            self.measLbl.setText("No measurement running.")
            self.end_measurement()
        else:
            self.saveBtn.setEnabled(False)
            self.timedMeasBtn.setEnabled(False)
            self.measLbl.setText("Manual measurement running.")
            self.start_measurement()
    
    def end_measurement(self):
        self.measuring = 0
        self.runningLbl.setText("Waiting.")
        self.measBtn.setText("Start Measurement")
    
    def clear_canvas(self):
        for fig in self.chList:
            fig._clear_canvas_()
    
    def start_measurement(self):
        start_time = time.time()
        for fig in self.chList:
            fig.start_time = start_time
        self.measuring = 1
        self.clear_canvas()
        self.runningLbl.setText("Measuring.")
        self.measBtn.setText("Stop Measurement")
    
    def start_timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.scan_com_ports)
        self.timer.start(1000)
        
    def scan_com_ports(self):
        if self.ser == None:
            ports = serial.tools.list_ports.comports()
            self.ser = None
            for port in ports:
                if "1337:0161" in port.hwid:
                    print(f"ICMOS device found on {port.device}")
                    self.ser = serial.Serial(port.device, 9600, timeout=1)  
                    self.usbLabel.setText(f"Connected on {port.device}.")
                    self.measBtn.setEnabled(True)
        else:
            ports = serial.tools.list_ports.comports()
            ICMOS_cnt = 0
            for port in ports:
                if "1337" in port.hwid:
                    ICMOS_cnt = 1
                    self.usbLabel.setText(f"Connected on {port.device}.")
            if ICMOS_cnt == 0:
                    self.ser = None
                    self.usbLabel.setText(f"No device connected.")
                    self.measBtn.setEnabled(False)
                    self.measBtn.setText("Start Measurement")
                
                    
    def get_next_datapoint(self,channel):
        if not self.ser == None and self.measuring == 1:
            if self.ser.is_open:
                self.ser.reset_output_buffer()
                self.ser.reset_input_buffer()
                line = self.ser.readline().decode('ascii', errors='ignore').strip()
                if line:
                    split_lines = line.split(",")
                    return float(split_lines[channel-1])
            else:
                return None
        else:
            return None

class FastDrawingCanvas(FigureCanvas):

    def __init__(self, *args, x_len:int, y_range:List, interval:int, channel:int, parent, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parent = parent
        self._x_len_ = x_len
        self._y_range_ = y_range
        self.start_time = 0
        self._x_ = list(range(0, x_len))
        self._y_ = [0] * x_len
        self.ybuf = []
        self.xbuf = []
        self._ax_ = self.figure.subplots()
        self._ax_.set_ylim(ymin=self._y_range_[0], ymax=self._y_range_[1]) # added
        self._line_, = self._ax_.plot(self._x_, self._y_)                  # added
        self.draw()                                                        # added
        self._timer_ = self.new_timer(interval, [(self._update_canvas_, (), {})])
        self._timer_.start()
        self.channel=channel
        self._ax_.set_title(f"Channel {self.channel}")
        return
    def _clear_canvas_(self) -> None:
        self._x_ = list(range(0, self._x_len_))
        self._y_ = [0] * self._x_len_
        self.ybuf.clear()
        self.xbuf.clear()
        
    def _update_canvas_(self) -> None:
        try:
            data = round(self.parent.get_next_datapoint(self.channel), 2)
            self._y_.append(data)
            self._y_ = self._y_[-self._x_len_:]
            self._line_.set_ydata(self._y_)
            self._ax_.draw_artist(self._ax_.patch)
            self._ax_.draw_artist(self._line_)
            self.update()
            self.ybuf.append(data)
            self.xbuf.append(time.time()-self.start_time)
            self.flush_events()
        except:
            pass
        return

if __name__ == "__main__":
    #os.environ["QT_SCALE_FACTOR"] = "1"
    #os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "Floor" 
    #os.environ["QT_FONT_DPI"] = "96"
    sys.argv += ['-platform', 'windows:darkmode=1']
    qapp = QtWidgets.QApplication(sys.argv)
    qapp.setStyle("fusion")
    app = ApplicationWindow()
    qapp.exec()
