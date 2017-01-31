"""
@author phansson
"""

import sys
import argparse
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from MainWindow import MainWindow
from Reader import U12Reader, U12Data, DataReader, U12SimReader

import u12

def get_args():
    parser = argparse.ArgumentParser('CDMS Active Reset GUI.')
    parser.add_argument('--debug',action='store_true',help='debug toggle')
    parser.add_argument('--go',action='store_true',help='start')
    parser.add_argument('--sleep', '-s', type=float, default=1.0, help='Sleep time for data reader.')
    args = parser.parse_args()
    print( args )
    return args


def main():

    # create the Qapp
    app = QApplication(sys.argv)

    # Create the device
    device = u12.U12()
    
    # data object
    data = U12Data()
    
    # create the reader thread
    u12Reader = U12Reader(device, data)
    #u12Reader = U12SimReader(data)

    # create the independent data cruncher
    data_reader = DataReader(data, sleep_nsec=args.sleep)
    
    

    #### create the main GUI
    form = MainWindow(parent=None, debug=args.debug, ai_channels=u12Reader.ai_channels)

    # connections
    form.connect(data_reader, SIGNAL('new_data'), form.new_data)
    form.connect(form, SIGNAL('acqState'),u12Reader.set_state)
    form.connect(form, SIGNAL('quit'),u12Reader.quit)
    form.connect(form, SIGNAL('quit'),data_reader.quit)
    form.connect(form, SIGNAL('new_ao'), u12Reader.set_ao)
    form.do0_on.connect(u12Reader.set_do0_on)
    form.do0_off.connect(u12Reader.set_do0_off)
    form.do1_on.connect(u12Reader.set_do1_on)
    form.do1_off.connect(u12Reader.set_do1_off)

    
    # show the form
    form.show()

    # start the acquizition of frame (should go into GUI button I guess)

    if args.go:
        form.set_state('Running')
    

    print ('[active_reset_gui]: main thread ' , app.instance().thread())


    # run the app
    sys.exit( app.exec_() )


if __name__ == "__main__":
    print ('Just Go')

    args = get_args()
    
    main()
