import sys
import os
import time
import copy

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import u12

class U12Data(QObject):
    """Base class for data from U12."""
    def __init__(self):
        QObject.__init__(self)
        self.mutex = QMutex()
        self.data = None
        self.data_flag = 0

    def set_data(self,value):
        self.mutex.lock()
        # clear data: affect all references
        if self.data != None:
            del self.data[:]
        self.data = value
        self.data_flag += 1
        self.mutex.unlock()

    def get_data(self):
        return copy.deepcopy(self.data)

class Reader(QThread):
    """ Base class for reading data"""
    debug = False
    def __init__(self, data, parent=None):
        QThread.__init__(self, parent)
        self.state = 'Stopped'
        self.n = 0
        self.data = data
    
    def set_state(self, s):
        self.state = s

    def on_quit(self):
        self.quit_thread()
    

        
        
class U12Reader(Reader):
    """Read U12 data."""    
    def __init__(self, data, parent=None):
        Reader.__init__(self, data, parent)

        # start the thread
        self.start()
        
    def run(self):
        """Read data."""

        print('U12Reader run ' + str(self.thread))
        
        # number of reads
        n = 0

        device = u12.U12()


        while True:

            # wait until state is correct
            if self.state != 'Running':
                #if Reader.debug:
                print('U12Reader thread waiting')
                self.sleep(1)
                continue

            # read
            res_list = []
            res_list.append( device.eAnalogIn(0) )
            res_list.append( device.eAnalogIn(1) )

            print('U12Reader send ' + str(len(res_list)) + ' data total sent ' + str(n) + ' (' + str(res_list) + ')')


            # update data object
            self.data.set_data(res_list)



            # reset data list
            #del res_list[:]
            

            #update counter
            n += 1



class DataReader(QThread):
    """ Base class for reading data"""
    debug = False
    def __init__(self, data, parent=None):
        QThread.__init__(self, parent)    
        self.start()
        self.data = data

    def on_quit(self):
        self.quit()
            
    def run(self):
        """Read data and emit it."""

        print('DataReader run ' + str(self.thread))
        
        n = 0
        i = 0

        while True:

            print('DataReader last flag emitted ' + str(i) + ' total ' + str(n))

            self.data.mutex.lock()
            if self.data.data_flag != i:
                # new data, emit it
                d = self.data.get_data()
                print('emit ' + str(len(d)) + '  data: ' + str(d))
                self.emit( SIGNAL('new_data'), self.data.data_flag, d )
                # update flag
                i = self.data.data_flag
                n += 1
            self.data.mutex.unlock()
            # sleep a little
            self.sleep(1)                

            
