#!/usr/bin/python

import sys
import os
import time
import datetime
import numpy as np
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from util import MyQThread
#from PyQt4.QtCore import QThread
from util import logthread


class PlotWorker(QObject):

    def __init__(self, name, parent = None, n_integrate = 1, converter_fnc = None ):    
        super(PlotWorker, self).__init__()
        self.exiting = False
        self.name = name
        self.n_integrate = n_integrate
        self.n = 0
        self.converter_fnc = converter_fnc
        #self.start()


    def set_integration(self,n):
        self.n_integrate = n
    
    #def __del__(self):    
    #    self.exiting = True
    #    self.wait()

    def new_data(self,frame_id, data):
        """Abstract function"""
        print('abstract new_data function called!')

    def clear_data(self):
        """Abstract function to reset data in the widgets"""
        #print('abstract clear_data function called!')

        

class PlotWidget(QWidget):

    def __init__(self, name, parent=None, show=False, n_integrate=1):
        QWidget.__init__(self,parent)
        self.name = name
        self.set_geometry()
        #self.create_menu()
        self.create_main()        
        self.n = 0
        self.t0sum = 0
        self.debug = False
        self.x_label = ''
        self.y_label = ''
        self.title = self.name 
        self.txt = None
        self.txt_integration = None
        self.thread = MyQThread()
        #self.thread = QThread()
        self.thread.start()
        self.worker = None
        
        if show:
            self.show()
    

    def closeEvent(self, event):
        #self.emit(SIGNAL('on_quit'), self.name)
        print('[PlotWidget] : \"' + self.name + '\" closeEvent')
        self.thread.quit()
        can_exit = self.thread.wait(1000)        
        #can_exit = True
        if can_exit:
            print('[PlotWidget] : \"' + self.name + '\" thread quit successfully')            
            event.accept()
        else:
            print('[PlotWidget] : \"' + self.name + '\" thread quit timed out')
            self.thread.terminate()
            can_exit = self.thread.wait(1000)        
            if can_exit:
                print('[PlotWidget] : \"' + self.name + '\" thread terminated successfully')            
                event.accept()
            else:
                print('[PlotWidget] : ERROR \"' + self.name + '\" thread failed to die')
                #event.ignore()
    

    def set_integration_text(self):
        self.txt_integration = self.ax.text(0.1,0.9,'{0} frames integrated'.format(self.worker.n_integrate),transform=self.ax.transAxes)
    
    
    def set_x_label(self,s):
        self.x_label = s

    def set_y_label(self,s):
        self.y_label = s

    def set_title(self, s):
        self.title = s

    def set_integration(self,n):
        logthread('[PlotWidget]: set_integration to ' + str(n))
        if self.worker != None:
            self.worker.set_integration( n )
        self.set_integration_text()
    
    def set_geometry(self):
        self.setGeometry(10,10,500,500)
        self.setWindowTitle( self.name )

    def clear_figure(self):
        """Clear figure and it's axes"""
        # clear figure with all it's axes
        self.fig.clear()
        # set axes to none to force it to redraw on next call
        self.ax = None
    

    def on_scale_slider(self, value):
        """Set new axis limits and clear the figure so that it get's updated on next call. 

        Ignore value and which wone that sent the update.
        """

        #print('[PlotWidget] : \"' + self.name + '\" on_scale_slider')
        if self.slider_zscale_min.value() < self.slider_zscale_max.value():
            self.zscale_min = self.slider_zscale_min.value()
            self.zscale_max = self.slider_zscale_max.value()
            self.textbox_zscale_min.setText(str(self.zscale_min))
            self.textbox_zscale_max.setText(str(self.zscale_max))

            self.clear_figure()
        
        else:
            print('[PlotWidget] : \"' + self.name + '\" WARNING z-scale is undefined min= ' + str(self.slider_zscale_min.value()) + ' max=' + str(self.slider_zscale_max.value()))


    def on_scale_text(self):
        """Set new axis limits and clear the figure so that it get's updated on next call. 
        """

        #print('[PlotWidget] : \"' + self.name + '\" on_scale_text')
        if int(self.textbox_zscale_min.text()) < int(self.textbox_zscale_max.text()):
            self.zscale_min = int(self.textbox_zscale_min.text())
            self.zscale_max = int(self.textbox_zscale_max.text())
            self.slider_zscale_min.setValue(self.zscale_min)
            self.slider_zscale_max.setValue(self.zscale_min)

            self.clear_figure()
        
        else:
            print('[PlotWidget] : \"' + self.name + '\" WARNING z-scale is undefined min= ' + str(self.slider_zscale_min.value()) + ' max=' + str(self.slider_zscale_max.value()))

        

    
    def create_menu(self):        

        self.file_menu = self.menuBar().addMenu("&File")
        
        load_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        
        quit_action = self.create_action("&Quit",
            shortcut="Ctrl+Q", slot=self.close, 
            tip="Close the application")
        
        self.add_actions(self.file_menu, (quit_action,load_file_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About this thing')
        
        self.add_actions(self.help_menu, (about_action,))



    def create_zscale(self):
        """Abstract function"""
        return None
    


    def create_main(self):

        # main vertical layout
        vbox  = QVBoxLayout()

        # canvas horizontal layout
        hbox = QHBoxLayout()

        # create plot canvas
        #self.dpi = 100
        #self.fig = plt.Figure(figsize=(20, 20), dpi=150)
        self.fig = plt.Figure() #figsize=(10, 5), dpi=150)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.ax = None #self.fig.add_subplot(111)        
        self.img = None


        vbox_canvas = QVBoxLayout()
        vbox_canvas.addWidget( self.canvas )

        # Create the navigation toolbar, tied to the canvas        
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        
        vbox_canvas.addWidget( self.mpl_toolbar )

        hbox.addLayout( vbox_canvas)

        vbox_zscale = self.create_zscale()
        
        if vbox_zscale != None:
            hbox.addLayout(vbox_zscale)
        
        vbox.addLayout(hbox)



        # create quit button
        #self.quit_button = QPushButton(self)
        #self.quit_button.setText('Close')
        #self.quit_button.clicked.connect(self.on_quit)
        #hbox = QHBoxLayout()
        #hbox.addWidget( self.quit_button )
        #hbox.addStretch(2)
        #vbox.addLayout( hbox )

        self.setLayout( vbox )





class StripWorker(PlotWorker):

    def __init__(self, name, parent = None, n_integrate = 1, max_hist=100, converter_fnc=None):    
        PlotWorker.__init__(self, name, parent, n_integrate, converter_fnc)
        logthread('StripWorker.__init__')
        self.y = [] 
        for i in range(max_hist):
            self.y.append(0)
        self.max_hist = max_hist

    def new_data(self, frame_id ,data):
        """Process the data and send to GUI when done."""

        if frame_id % 500 == 0:
            logthread('StripWorker.new_data')

        # look for data using name
        # I think the keys are QStrings so cant search normally
        for k,v in data.iteritems():
            if k == self.name:
                self.y.pop(0)
                if self.converter_fnc != None:
                    v = self.converter_fnc(v)
                self.y.append(v)
                self.n += 1
        
        if self.n >= self.n_integrate:
            self.emit(SIGNAL('data'), frame_id, self.y)
            self.n = 0
        #logthread('new_data DONE')

    def clear_data(self):
        """Reset data in the widgets"""
        self.y = []


class StripWidget(PlotWidget):

    def __init__(self, name, parent=None, show=False, n_integrate = 1, max_hist=100, converter_fnc=None):
        PlotWidget.__init__(self,name, parent, show)
        logthread('StripWidget.__init__')
        self.d = None
        self.name = name
        self.worker = StripWorker(self.name, parent, n_integrate, max_hist, converter_fnc)
        self.worker.moveToThread( self.thread )
        self.connect(self.worker, SIGNAL('data'), self.on_draw)
        self.x = [] 
        for i in range(max_hist):
            self.x.append(i)

    def on_draw(self, frame_id, y):

        if frame_id % 500 == 0:
            logthread('StripWidget.on_draw')
        
        t0 = time.time()
        if self.ax == None:
            self.ax = self.fig.add_subplot(111)
            self.ax.set_autoscale_on(True)
            #print('x = ' + str(len(self.x)) + '  y = ' + str(len(y))) 
            self.img, = self.ax.plot(self.x, y)
            self.ax.set_xlabel(self.x_label, fontsize=14, color='black')
            self.ax.set_ylabel(self.y_label, fontsize=14, color='black')
            self.set_integration_text()

        else:
            self.img.set_ydata(y)
            self.ax.relim()
            self.ax.autoscale_view(True, True, True)
            #self.ax.hist(self.x, bins=self.bins, facecolor='red', alpha=0.75)
        self.ax.set_title(self.title + ' id ' + str(frame_id) + ' ('+ str(self.n) + ' frames)')
        self.canvas.draw()
        self.n += 1

        dt = time.time() - t0
        self.t0sum += dt
        if self.n % 100 == 0:
            logthread('StripWidget on_draw {0} frames with {1} sec/image'.format(self.n, self.t0sum/50.))
            self.t0sum = 0.
    
