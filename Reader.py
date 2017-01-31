import sys
import os
import time
import copy
import random

import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ReaderError(Exception):
    """Base class for exceptions in the LabJack interface."""
    pass


class AnalogOutputError(ReaderError):
    """Exception raised for errors related to the analog output of the LabJack.

    Attributes:
       args --- argument
    """
    def __init__(self, args):
        self.args = args



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
        #if self.data != None:
            # this doesn't work for dict: del self.data[:]
        self.data = value
        self.data_flag += 1
        self.mutex.unlock()

    def get_data(self):
        return copy.deepcopy(self.data)

class Reader(QThread):
    """ Base class for reading data"""
    debug = False
    def __init__(self, device, data, parent=None):
        QThread.__init__(self, parent)
        self.state = 'Stopped'
        self.n = 0
        self.device = device
        self.data = data
    
    def set_state(self, s):
        self.state = s

    def on_quit(self):
        self.quit_thread()
    
        
class U12Reader(Reader):
    """Read U12 data."""
    
    def __init__(self, device, data, parent=None):
        Reader.__init__(self, device, data, parent)

        # define which channels are used
        self.ai_channels = [0,2,4,5]
        
        # start the thread
        self.start()
    
    def run(self):
        """Read data."""

        print('U12Reader run ' + str(self.thread))
        
        # number of reads
        n = 0

        while True:

            # wait until state is correct
            if self.state != 'Running':
                #if Reader.debug:
                print('U12Reader thread waiting')
                self.sleep(1)
                continue

            result_ao = self.read_ao(differential=True)

            #print('AO res:')
            #print(result_ao)
            
            # update data object
            self.data.set_data(result_ao)

            #update counter
            n += 1


    def read_ao(self, differential=True):
        """Read analog input.
        
        Args:
            differential: do a differential reading
            gain: only applicable for differential readout.
        
        Returns: dictionary of the analig voltages.
        
        """
        res = {}
        
        if not differential:
            for i in self.ai_channels:
                res['AI' + str(i)] = self.device.eAnalogIn(i)['voltage']
        else:

            r = self.device.rawAISample()
            
            for i in self.ai_channels:

                d = None
                # differential only for AI0-AI3  channels
                if i< 3:
                    name_even_ch = 'Channel' + str(i)
                    name_odd_ch = 'Channel' + str(i+1)
                    if name_even_ch not in r:
                        s = name_even_ch + ' not in AISample: ' + str(r)
                        raise AnalogOutputError(s)
                    if name_odd_ch not in r:
                        raise AnalogOutputError(name_odd_ch  + ' not in AISample: ' + str(r))
                    d = r[name_even_ch] - r[name_odd_ch]

                else:
                    try:
                        d = self.device.eAnalogIn(i)['voltage']
                    except IndexError:
                        print('failed on i=' + str(i) + ' rawAISamples: ' + str(r) )
                
                    
                
                res['AI' + str(i)] = d
        
        return res
    
    
    def set_ao(self, ch, d):
        """Set analog output value.
        
        Args:
            ch (int): Channel id (0-1)
            d (float): analog value to be set.
        
        Returns:
        
        """
        print('U12Reader set_ana ' + str(ch) + ' ' + str(d))

        if ch == 0:
            self.device.eAnalogOut(demo=0, analogOut0=d, analogOut1=-1.0)  
        elif ch == 1:
            self.device.eAnalogOut(demo=0, analogOut0=-1.0, analogOut1=d)  
        else:
            raise AnalogOutputError('Channel name is invalid: ' + str(id))

    def set_do0_on(self):
        """Set digital channel 0 ON."""
        self.device.eDigitalOut(channel=0,writeD=1,state=1)
        print('set_do0_on')

    def set_do1_on(self):
        """Set digital channel 1 ON."""
        self.device.eDigitalOut(channel=1,writeD=1,state=1)
        print('set_do1_on')

    def set_do0_off(self):
        """Set digital channel 0 OFF."""
        self.device.eDigitalOut(channel=0,writeD=1,state=0)
        print('set_do0_off')

    def set_do1_off(self):
        """Set digital channel 1 OFF."""
        self.device.eDigitalOut(channel=1,writeD=1,state=0)
        print('set_do1_off')


            
    


class DataReader(QThread):
    """ Base class for reading data"""
    debug = False
    def __init__(self, data, parent=None, sleep_nsec=1.0):
        QThread.__init__(self, parent)    
        self.start()
        self.data = data
        self.sleep_time = sleep_nsec

    def on_quit(self):
        self.quit()
            
    def run(self):
        """Read data and emit it."""

        print('DataReader run ' + str(self.thread))
        
        n = 0
        i = 0

        time_now = time.time()
        time_last = time_now
        dt = 0.
        
        while True:

            # timing stuff
            time_now = time.time()
            dt += time_now - time_last
            time_last = time_now
            # print some timing stuff
            if n % 50 == 0:
                dt /= 50.0
                # fraction of the sleep time we get a delay
                dead_time = (dt/self.sleep_time -1.0)*100
            
                print('DataReader last flag emitted ' + str(i) + ' total ' + str(n) + ' dt ' + str(dt) + ' dead ' + '{0:.2f}%'.format(dead_time))

                # reset
                dt = 0.

            self.data.mutex.lock()
            if self.data.data_flag != i:
                # new data, emit it
                d = self.data.get_data()
                #print('emit ' + str(len(d)) + '  data: ' + str(d))
                self.emit( SIGNAL('new_data'), self.data.data_flag, d )
                # update flag
                i = self.data.data_flag
                n += 1
            self.data.mutex.unlock()
            # sleep a little
            time.sleep(self.sleep_time)
            #self.sleep(self.sleep_time)



class U12SimDevice(object):
    """Output sim data."""
    def __init__(self):
        self.eAnalogInVal = [0.,0.]
        self.update()

    def update(self):
        for i in range(len(self.eAnalogInVal)):
            v = random.random()
            print('update x ' + str(self.eAnalogInVal[i]) + ' -> ' + str(v))
            self.eAnalogInVal[i] = v
            print('updated x ' + str(self.eAnalogInVal[i]) + ' ' + str(self.eAnalogInVal[0]) + ',' + str(self.eAnalogInVal[1]))
    
    def eAnalogIn(self,i):
        return self.eAnalogInVal[i]

class U12SimReader(U12Reader):
    """Simulate U12 data."""    
    def __init__(self, data, parent=None):
        Reader.__init__(self, U12SimDevice(), data, parent)

        # start the thread
        self.start()
        

    def run(self):
        """Read data."""

        print('U12Reader run ' + str(self.thread))
        
        # number of reads
        n = 0

        #device = U12SimDevice()


        while True:

            # wait until state is correct
            if self.state != 'Running':
                #if Reader.debug:
                print('U12Reader thread waiting')
                self.sleep(1)
                continue
            else:
                self.sleep(1)
            
            # read
            #res_list = []
            #res_list.append( {'anaIn0':self.device.eAnalogIn(0)} )
            #res_list.append( {'anaIn1':self.device.eAnalogIn(1)} )
            res_list = {'anaIn0':self.device.eAnalogIn(0), 'anaIn1':self.device.eAnalogIn(1)}

            print('U12Reader send ' + str(len(res_list)) + ' data total sent ' + str(n) + ' (' + str(res_list) + ')')


            # update data object
            self.data.set_data(res_list)



            # reset data list
            #del res_list[:]
            

            #update counter
            n += 1

            # udpate device
            self.device.update()
