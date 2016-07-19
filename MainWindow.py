import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import time
#import numpy as np
#import matplotlib.pyplot as plt
#from pix_threading import MyQThread


class MainWindow(QMainWindow):

    #__datadir = os.environ['DATADIR']

    def __init__(self, parent=None, debug=False):
        QMainWindow.__init__(self, parent)

        self.setWindowTitle(self.get_window_title())

        self.debug = debug
        #plt.ion()

        # run state 
        self.run_state = 'Undefined'

        # Selected ASIC
        # -1 if all of them
        self.select_asic = -1

        # timers
        self.t0_frame = None
        self.t0_frame_diff = -1.0
        
        # counters
        self.nframes = 0

        # GUI stuff        
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

    def get_window_title(self):
        return 'Active Reset GUI'

    def on_about(self):
        msg = """ Active Reset GUI."""
        QMessageBox.about(self, "About the app", msg.strip())
    

    def create_stat_view(self, vbox):
        
        vbox.addWidget(QLabel('Processing statistics:'))
        hbox = QHBoxLayout()
        #hbox.addWidget(QLabel('Processing stats:'))

        #self.form_layout_stat = QFormLayout()
        # id
        textbox_frameid_label = QLabel('ID:')
        self.textbox_frameid = QLineEdit()
        self.textbox_frameid.setMinimumWidth(50)
        self.textbox_frameid.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_frameid_label, self.textbox_frameid)
        hbox.addWidget(textbox_frameid_label)
        hbox.addWidget(self.textbox_frameid)

        # rate
        textbox_framerate_label = QLabel('Rate:')
        self.textbox_framerate = QLineEdit()
        self.textbox_framerate.setMinimumWidth(50)
        self.textbox_framerate.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_framerate_label, self.textbox_framerate)
        hbox.addWidget(textbox_framerate_label)
        hbox.addWidget(self.textbox_framerate)
        
        # processed
        textbox_frameprocessed_label = QLabel('# processed:')
        self.textbox_frameprocessed = QLineEdit()
        self.textbox_frameprocessed.setMinimumWidth(50)
        self.textbox_frameprocessed.setMaximumWidth(50)        
        #self.form_layout_stat.addRow( textbox_frameprocessed_label, self.textbox_frameprocessed)
        hbox.addWidget(textbox_frameprocessed_label)
        hbox.addWidget(self.textbox_frameprocessed)

        #vbox.addLayout(self.form_layout_stat)
        vbox.addLayout(hbox)


    def create_matrix_view(self, vbox):
        
        vbox.addWidget(QLabel('Analog:'))
        #hbox = QHBoxLayout()
        #hbox.addWidget(QLabel('Processing stats:'))

        self.form_layout = QFormLayout()
        self.textbox_ai = {}
        for i in range(2):
            textbox_ai0_label = QLabel('AI' + str(i) + ':')
            textbox_ai0 = QLineEdit()
            textbox_ai0.setMinimumWidth(80)
            textbox_ai0.setMaximumWidth(80)
            self.textbox_ai[i] = textbox_ai0
            self.form_layout.addRow( textbox_ai0_label, textbox_ai0)
        vbox.addLayout(self.form_layout)
        #vbox.addLayout(hbox)


    def create_options_view(self,vbox):
        """Add options to form."""
                
        textbox_select_asic_label = QLabel('Select something (0-3):')
        self.combo_select_asic = QComboBox(self)
        for i in range(-1,4):
            if i == -1:                
                self.combo_select_asic.addItem("ALL")
            else:
                self.combo_select_asic.addItem(str(i))
        self.combo_select_asic.setCurrentIndex(self.select_asic + 1)
        #self.combo_select_asic.currentIndexChanged['QString'].connect(self.on_select_asic)

      
        self.form_layout = QFormLayout()
        self.form_layout.addRow(textbox_select_asic_label, self.combo_select_asic)
        vbox.addLayout( self.form_layout )
    
    def create_main_frame(self):
        """This is the main widget."""

        self.main_frame = QWidget()

        # main vertical layot
        vbox = QVBoxLayout()

        # add stat box
        self.create_stat_view(vbox)

        # add control
        hbox_cntrl = QHBoxLayout()
        self.acq_button_start = QPushButton("Start")
        self.connect(self.acq_button_start, SIGNAL('clicked()'), self.on_acq_start)
        hbox_cntrl.addWidget( self.acq_button_start)
        self.acq_button_stop = QPushButton("Stop")
        self.connect(self.acq_button_stop, SIGNAL('clicked()'), self.on_acq_stop)
        hbox_cntrl.addWidget( self.acq_button_stop)
        vbox.addLayout( hbox_cntrl )

        # add options
        self.create_options_view(vbox)

        self.create_matrix_view(vbox)

        # add plots
        #self.create_plots_view(vbox)

        hbox_quit = QHBoxLayout()
        self.quit_button = QPushButton("&Quit")
        self.quit_button.clicked.connect(self.on_quit)
        hbox_quit.addStretch(2)
        hbox_quit.addWidget( self.quit_button)                                    
        vbox.addLayout( hbox_quit )

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)


    def create_menu(self):        

        self.file_menu = self.menuBar().addMenu("&File")
        
        load_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        
        quit_action = self.create_action("&Quit",
            shortcut="Ctrl+Q", slot=self.close, 
            tip="Close the application")
        
        #self.add_actions(self.file_menu, 
        #    (load_file_action, None, quit_action))
        
        self.add_actions(self.file_menu, (quit_action,load_file_action))

        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About this thing')
        
        self.add_actions(self.help_menu, (about_action,))


    def create_status_bar(self):
        self.status_text = QString('Run status: ' + self.run_state)
        #self.statusBar().addWidget(self.status_text, 1)
        self.statusBar().showMessage(self.status_text, 0)


    def set_data(self,data):
        self.data = data
    
    
    def new_data(self,data_flag, data):
        """ Receives new data"""

        print('new_data ' + str(data_flag) + ' ' + str(data) )

        # timer
        t_now = int(round(time.time() * 1000))
        if self.t0_frame == None:
            self.t0_frame = t_now
            self.t0_frame_diff = -1
        else:
            self.t0_frame_diff = t_now - self.t0_frame
            self.t0_frame = t_now


        #QApplication.processEvents()

        # calculate the rate
        if self.t0_frame_diff == 0:
            rate = -1
        else :
            rate = 1000.0/float(self.t0_frame_diff)

        # update stat counters
        self.updateStats(data_flag, rate, self.nframes)

        # update ai
        self.updateAI(data)


        
        self.nframes += 1

        #QApplication.processEvents()
    


    def updateStats(self, i, rate, n):
        """Update stat boxes."""
        self.textbox_frameid.setText(str(i))
        self.textbox_framerate.setText('{0:.1f}Hz'.format(rate))
        self.textbox_frameprocessed.setText(str(self.nframes))

    def updateAI(self, d):
        """Update ana."""
        for l in range(len(d)):
            print(l)
            tb = self.textbox_ai[l]
            v = d[l]['voltage']
            print(v)
            tb.setText( '{0:.4f}V'.format(v) )
    
        
    def set_state(self,state_str):
        self.run_state = state_str
        self.statusBar().showMessage('Run status: ' + self.run_state)
        self.emit(SIGNAL('acqState'), state_str)

    def on_acq_start(self):
        """Start the acquisition of data"""
        self.set_state('Running')

    def on_acq_stop(self):
        """Stop the acquisition of data"""
        self.set_state('Stopped')
        
    def closeEvent(self, event):
        """Close the GUI."""
        can_exit = True
        self.on_quit()
        if can_exit:
            event.accept()
        else:
            event.ignore()

    def on_quit(self):
        """Quit the main window."""
        print('[MainWindow]: on_quit')        
        print('[MainWindow]: kill thread')        
        self.emit(SIGNAL('quit'))
        self.close()
    


    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
