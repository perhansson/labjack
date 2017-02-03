import sys
import threading
import time
from PyQt4.QtCore import *

def logthread(caller):
    print('%-25s: %s, %s,' % (caller, threading.current_thread().name,
                              threading.current_thread().ident))





class MyQThread(QThread):
    """Only needed for Qt 4.6"""
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
    def start(self):
        QThread.start(self)
    def run(self):
        QThread.run(self)




class OpWorker(QThread):

    def __init__(self, function, out_target, step=0.01):
        super(OpWorker, self).__init__()
        logthread('OpWorker.__init__')
        self.function = function
        self.out_target = out_target
        self.data = None
        self.flag = 0
        self.f = None
        self.running = False
        self.step = step

    def process(self):
        finished = False

        if self.flag == 1 and self.running:

            qgset = self.data['AI5']
            out = self.data['AI0']

            logthread('OpWorker.process new data QGSET ' + str(qgset) + ' OUT ' + str(out))

            s = 'OP TIME ' + str(time.time()) + ' QGSET ' + '{0:.4f}'.format(qgset) + ' OUT ' + '{0:.4f}'.format(out)
            print(s)
            self.f.write(s + '\n')

            adiff = abs(self.out_target - out)
            if adiff < 0.1:
                self.emit(SIGNAL('opw_finished'))
                finished = True
            diff = self.out_target - out
            print('diff ' + str(diff))
            if diff > 0:
                self.emit(SIGNAL('opw_update'), self.step)
            elif diff < 0:
                self.emit(SIGNAL('opw_update'), -self.step)

            self.flag = 0

        return finished
    
    def new_data(self, data_flag, data):
        logthread('OpWorker.new_data')
        self.data = data
        self.flag = 1
        return

    def run(self):
        logthread('OpWorker.run')
        self.running = True
        self.f = open('op.txt', 'wb')
        finished = False
        while not finished:
            finished = self.process()
            time.sleep(5)
    
    def quit(self):
        self.running = False
        if self.f != None and not self.f.closed:
            self.f.close()
        super(OpWorker, self).quit()
    
    
            
