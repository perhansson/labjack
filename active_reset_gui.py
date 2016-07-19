"""
@author phansson
"""

import sys
import argparse
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from MainWindow import MainWindow
from Reader import U12Reader, U12Data, DataReader

def get_args():
    parser = argparse.ArgumentParser('CDMS Active Reset GUI.')
    parser.add_argument('--debug',action='store_true',help='debug toggle')
    parser.add_argument('--go',action='store_true',help='start')
    args = parser.parse_args()
    print( args )
    return args


def main():

    # create the Qapp
    app = QApplication(sys.argv)

    # data object
    data = U12Data()
    
    # create the reader thread from the U12
    reader = U12Reader(data)

    # create the independent data cruncher
    data_reader = DataReader(data)
    
    

    #### create the main GUI
    form = MainWindow(parent=None, debug=args.debug)

    form.connect(data_reader, SIGNAL('new_data'), form.new_data)
    form.connect(form, SIGNAL('acqState'),reader.set_state)
    form.connect(form, SIGNAL('quit'),reader.quit)
    form.connect(form, SIGNAL('quit'),data_reader.quit)
    
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
