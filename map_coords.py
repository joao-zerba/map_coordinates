from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from PIL import Image

import csv, os

# Joao Paulo Castro Zerba 06 Jan 2023
# in case table is too large change the statement self.tableWidget.setMinimumSize(900,400)

class MapCoordsApp(qtw.QWidget):
    def __init__(self):
        super(MapCoordsApp, self).__init__()
        self.setWindowTitle("Coordinates GUI")
        self.setWindowIcon(qtg.QIcon('coords_map_gui.png'))
        # adding a base layout to this class
        self.layout_base = qtw.QHBoxLayout(self)
        self.sublayout = qtw.QVBoxLayout()
        self.button_sublayout = qtw.QVBoxLayout()
        
        self.plotwid()
        self.setup_db()
        self.setup_buttons()
        self.setup_connections()
        self.setup_table()

    def setup_db(self):

        # set up list of scatter objs and table dictionary, this last is not used for now
        self.scats_list = []#list of scat objects to apply the remove
        self.table_dict = {}#table dict ("deprecated")

    #setup buttons and other qtws
    def setup_buttons(self):

        self.layout_base.addLayout(self.button_sublayout)
        # setup buttons
        self.btn_load = qtw.QPushButton('Load Image', self)
        self.btn_save = qtw.QPushButton('Save Table', self)
        self.button_sublayout.addWidget(self.btn_load, alignment=qtc.Qt.AlignTop)
        self.button_sublayout.addWidget(self.btn_save, alignment=qtc.Qt.AlignTop)
        # setup combobox 
        self.label_combo = qtw.QLabel('Set Resolution (μm/px)', alignment=qtc.Qt.AlignCenter)
        self.button_sublayout.addWidget(self.label_combo, alignment=qtc.Qt.AlignTop)
        self.combo = qtw.QComboBox()
        self.combo.addItems(['6.3x = 1.19 μm/px', '10x = 0.76 μm/px', '20x = 0.620 μm/px', '40x = 0.193 μm/px'])
        self.button_sublayout.addWidget(self.combo, alignment=qtc.Qt.AlignTop)
        # setup labels and offsets
        self.label_xoff = qtw.QLabel('X-Offset (μm)', alignment=qtc.Qt.AlignCenter)
        self.button_sublayout.addWidget(self.label_xoff, alignment=qtc.Qt.AlignTop)
        self.xline_offsset = qtw.QLineEdit("0", self)
        self.button_sublayout.addWidget(self.xline_offsset, alignment=qtc.Qt.AlignTop)
        self.label_yoff = qtw.QLabel('Y-Offset (μm)', alignment=qtc.Qt.AlignCenter)
        self.button_sublayout.addWidget(self.label_yoff, alignment=qtc.Qt.AlignTop)
        self.yline_offsset = qtw.QLineEdit("0", self)
        self.button_sublayout.addWidget(self.yline_offsset, alignment=qtc.Qt.AlignTop)
        # stretching layout contents
        self.button_sublayout.addStretch()# to force the buttons to keep on top

    def setup_table(self):
        self.createTable()
        self.layout_base.addWidget(self.tableWidget)

    def setup_connections(self):
        # button connections
        self.btn_load.clicked.connect(self.handleOpenFig)
        self.btn_save.clicked.connect(self.handleSave)
        # line edit connections
        self.xline_offsset.returnPressed.connect(self.offset_update)
        self.yline_offsset.returnPressed.connect(self.offset_update)
        # combobox connections
        self.combo.activated[str].connect(self.offset_update)
        # mpl canvas connections
        self.can.mpl_connect("button_press_event", self.plot1)

    def offset_update(self):
        # checking entry for xoffset line
        try:
            xvalue = float(self.xline_offsset.text())
        except:
            if self.xline_offsset.text() == '':
                xvalue = 0
                self.xline_offsset.setText("0")
            else:
                print('Enter numerical value only in x-offset.')#TODO call a popup
                xvalue = 0
                self.xline_offsset.setText("0")
                self.attention_numerical_popup()
        # checking entry for yoffset line
        try:
            yvalue = float(self.yline_offsset.text())
        except:
            if self.yline_offsset.text() == '':
                yvalue = 0
                self.yline_offsset.setText("0")
            else:
                print('Enter numerical value only in y-offset.')#TODO call a popup
                yvalue = 0
                self.yline_offsset.setText("0")
                self.attention_numerical_popup()

        resolution = self.combo.currentText()
        res_index = self.combo.currentIndex()

        # print('resolution chosen is {}'.format(resolution))
        resolution_list = [1.19, 0.76, 0.620, 0.193]#same order as the chosen combobox index
        res = resolution_list[res_index]
        # print('resolution chosen is {}'.format(res))

        rows = self.tableWidget.rowCount()
        for i in range(rows):

            x1 = float(self.tableWidget.item(i, 0).text())
            y1 = float(self.tableWidget.item(i, 1).text())

            self.tableWidget.setItem(i,2,qtw.QTableWidgetItem(str(round((x1)*res + xvalue, 4))))
            self.tableWidget.setItem(i,3,qtw.QTableWidgetItem(str(round((y1)*res + yvalue, 4))))

    def plotwid(self):
        # creating fig with toolbar and adding it in a sub Vbox layout inside the parent base layout
        fig = Figure(figsize=(50, 50))
        self.can = FigureCanvasQTAgg(fig)
        self.toolbar = NavigationToolbar2QT(self.can, self)
        self.sublayout.addWidget(self.toolbar)
        self.sublayout.addWidget(self.can)
        self.layout_base.addLayout(self.sublayout)

    def plot_loaded_img(self,path_img):#TODO TIF
        loaded_img = plt.imread(path_img)
        self.ax.set_title(path_img,fontsize=30)
        self.ax.tick_params(axis='both',labelsize=20)
        self.ax.imshow(loaded_img)

    def on_press(self, event):
        # print(event.xdata, event.ydata)
        pass

    def keyPressEvent(self, event):#keyboard shortcuts 
        if event.key() == qtc.Qt.Key_1: self.plot1()
        elif event.key() == qtc.Qt.Key_2: self.plot2()
        elif event.key() == qtc.Qt.Key_3: self.plot_scatter()

    def plot1(self, event):
        self.plot_points(event)


    def plot_points(self, event):
        try:#if there is an image loaded
            if event.inaxes == self.ax:#Inside the plot area
                # if event.button == 1:#LEFT button
                if event.dblclick and event.button == 1:
                    x1, y1 = event.xdata, event.ydata
                    self.scat = self.ax.scatter(event.xdata, event.ydata, color='red')
                    self.can.draw()#this avoids the scatter point not to appear only when the cursor moves
                    #print(x1,y1)
                    #print(event.button)
                    self.scats_list.append(self.scat)
                    self.update_table("include",*[x1, y1])
                    self.offset_update()
                
                elif event.button == 3:
                    self.scats_list[-1].remove()
                    del self.scats_list[-1]

                    self.can.draw()
                    self.update_table("remove")
        except:
            qtw.QMessageBox.information(self, 'Image missing', 'Please load the image first.')

    def update_table(self, cond, *args):
        if args:
            #print('aqui')
            x1,y1 = args

        if cond == "include":

            #dict
            table_len = len(self.table_dict)
            new_entry = {table_len:[x1,y1]}
            self.table_dict.update(new_entry)

            #widget
            self.tableWidget.insertRow(table_len)
            self.tableWidget.setItem(table_len,0,qtw.QTableWidgetItem(str(round(x1,4))))#.setTextAlignment(qtc.Qt.AlignHCenter)
            self.tableWidget.setItem(table_len,1,qtw.QTableWidgetItem(str(round(y1,4))))


            xvalue = float(self.xline_offsset.text())#offset
            yvalue = float(self.yline_offsset.text())#offset
            rows = self.tableWidget.rowCount()

            self.tableWidget.setItem(table_len,2,qtw.QTableWidgetItem(str(round(x1 + xvalue,4))))
            self.tableWidget.setItem(table_len,3,qtw.QTableWidgetItem(str(round(y1 + yvalue,4))))

        if cond == "remove":

            table_len = len(self.table_dict)
            #dict
            del self.table_dict[table_len-1]

            #widget
            self.tableWidget.removeRow(table_len-1)

    def createTable(self):
        self.tableWidget = qtw.QTableWidget()
        self.tableWidget.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
        #self.tableWidget.setEditTriggers(qtw.QAbstractItemView.EditTrigger.NoEditTriggers)#newpyqt5

        #Row count
        #self.tableWidget.setRowCount(4)

        #Column count
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(['img x-coord (px)', 'img y-coord (px)', 'bl x-coord (μm)', 'bl y-coord (μm)'])

        #Size
        self.tableWidget.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
        self.tableWidget.setMinimumSize(900,400)

        self.tableWidget.verticalHeader().setVisible(False)

        #Table will fit the screen horizontally
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            qtw.QHeaderView.Stretch)

    def handleSave(self):
        path, ok = qtw.QFileDialog.getSaveFileName(
            self, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if ok:
            columns = range(self.tableWidget.columnCount())
            header = [self.tableWidget.horizontalHeaderItem(column).text()
                      for column in columns]
            with open(path, 'w') as csvfile:
                writer = csv.writer(
                    csvfile, dialect='excel', lineterminator='\n')
                writer.writerow(header)
                for row in range(self.tableWidget.rowCount()):
                    writer.writerow(
                        self.tableWidget.item(row, column).text()
                        for column in columns)

    def handleOpenFig(self):
        path, ok = qtw.QFileDialog.getOpenFileName(
            self, 'Open TIF', os.getenv('HOME'), 'TIF(*.TIF)')
        self.file_basename = os.path.basename(path)

        if ok:

            self.tableWidget.setRowCount(0)
            for i in range(len(self.scats_list)):
                self.scats_list[-1].remove()
                del self.scats_list[-1]

            # self.can.draw()
            self.scats_list = []#list of scat objects to apply the remove
            self.table_dict = {}

            self.reploting(path)

    def reploting(self,path):
        # set up figure axis

        try:
            self.ax.clear()
        except:
            # in case it is the first loaded image ...
            self.ax = self.can.figure.add_subplot(111) 
        
        self.ax.set_title(self.file_basename,fontsize=30)
        self.ax.tick_params(axis='both',labelsize=20)

        #loaded_img = plt.imread(path)
        loaded_img = self.load_Image(path)
        self.ax.imshow(loaded_img)
        self.can.draw()

    def load_Image(self, path):
        im = Image.open(path)#it can open tif
        return im

    def attention_numerical_popup(self):
            msgBox = qtw.QMessageBox()
            msgBox.warning(self, 'Information',"Use only numerical characters. Use '.' instead of ',' for decimal places.")

    def closeEvent(self, QcloseEvent):
        ans = qtw.QMessageBox.question(self, 'Confirm Close', 'Are you sure you want to close?',\
            qtw.QMessageBox.Yes | qtw.QMessageBox.No, qtw.QMessageBox.No)
        if ans ==qtw.QMessageBox.Yes:
            QcloseEvent.accept()
        else:
            QcloseEvent.ignore()

if __name__ == '__main__':
    app = qtw.QApplication([])
    qt_app = MapCoordsApp()
    qt_app.show()
    app.exec_()