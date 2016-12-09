import sys
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui import MyCheckBox
import time
#import numpy as np
#import matplotlib.pyplot as plt
#from pix_threading import MyQThread


class MainWindow(QMainWindow):

    #__datadir = os.environ['DATADIR']
    # signals
    do0_on = pyqtSignal()
    do0_off = pyqtSignal()
    do1_on = pyqtSignal()
    do1_off = pyqtSignal()
    ai_channels_name = {0:'OUT',1:'UNDEF.',2:'OUT_BUF',3:'UNDEF.',4:'QRST_T-',5:'QGSET',6:'UNDEF.',7:'UNDEF.'}
    ao_channels_name = {0:'QRST_T-',1:'QGSET'}
    do_channels_name = {0:'CALIB',1:'QRST_T+'}
    
    def __init__(self, parent=None, debug=False, ai_channels=range(8)):
        QMainWindow.__init__(self, parent)

        self.setWindowTitle(self.get_window_title())

        self.debug = debug
        #plt.ion()

        self.ai_channels = ai_channels
        
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

        # storage for analog in values
        self.textbox_ai = {}

        # storage for analog out buttons
        self.buttons_ao = {}
        self.textbox_ao = {}

        # storage for digital output
        self.checkboxes_do = {}
        
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
        """Create some informatiopn on the processed frames of the system."""

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


  




    def get_ai_widget(self, id, title=None):
        """Get a horizontal box widget for a given analog input channel."""
        label = 'AI' + str(id)
        textbox = QLineEdit()
        textbox.setMinimumWidth(80)
        textbox.setMaximumWidth(80)
        hbox = QHBoxLayout()
        if title:
            hbox.addWidget(QLabel(title + '(' + label + ')'))
        else:
            hbox.addWidget(QLabel(label))
        hbox.addWidget(textbox)

        # save as membe to access later
        self.textbox_ai[label] = textbox

        return hbox


    def on_ao0_set(self):
        self.emit(SIGNAL('new_ao'), 0, float(self.textbox_ao['AO0'].text()))

    def on_ao1_set(self):
        self.emit(SIGNAL('new_ao'), 1, float(self.textbox_ao['AO1'].text()))


    def set_do0_on(self):
        self.do0_on.emit()
    def set_do0_off(self):
        self.do0_off.emit()
    def set_do1_on(self):
        self.do1_on.emit()
    def set_do1_off(self):
        self.do1_off.emit()
        
    def get_ao_widget(self, id, title=None):
        """Get a horizontal box widget for a given analog output channel."""
        label = 'AO' + str(id)
        textbox = QLineEdit()
        textbox.setMinimumWidth(80)
        textbox.setMaximumWidth(80)
        hbox = QHBoxLayout()
        if title:
            hbox.addWidget(QLabel(title + '(' + label + ')'))
        else:
            hbox.addWidget(QLabel(label))
        hbox.addWidget(textbox)
        button = QPushButton("Set")
        # use signals instead at some point
        #ao_signal = pyqtSignal(int, float)
        if id == 0:
            self.connect(button, SIGNAL('clicked()'), self.on_ao0_set)
        else:            
            self.connect(button, SIGNAL('clicked()'), self.on_ao1_set)
        hbox.addWidget(button)
        self.buttons_ao[label] = button
        self.textbox_ao[label] = textbox
        return hbox


    def get_do_widget(self, id, title=None):
        """Get a horizontal box widget for a given digital output channel."""
        label = 'DO' + str(id)
        textbox = QLineEdit()
        textbox.setMinimumWidth(80)
        textbox.setMaximumWidth(80)        
        #wgt.setStyleSheet("background-color: rgb(0, 0, 0);\n")
        cb = MyCheckBox()
        cb.setParent(self.main_frame)
        if id == 0:
            cb.checked_signal.connect(self.do0_on)
            cb.unchecked_signal.connect(self.do0_off)
        else:
            cb.checked_signal.connect(self.do1_on)
            cb.unchecked_signal.connect(self.do1_off)        
        #wgt.resize(200,100)
        #wgt.show()
        hbox = QHBoxLayout()
        if title:
            hbox.addWidget(QLabel(title + '(' + label + ')'))
        else:
            hbox.addWidget(QLabel(label))
        hbox.addWidget(cb)
        self.checkboxes_do[label] = cb
        return hbox

    
    
        
    def create_ai_view(self, vbox):
        """Creates analog input boxes."""
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(QLabel('Analog Input Channel Monitoring'))
        hbox_1.addStretch(1)
        vbox.addLayout(hbox_1)
        
        
        for i in self.ai_channels:
            hb = self.get_ai_widget(i,self.ai_channels_name[i])
            vbox.addLayout(hb)
    

    def create_ao_view(self, vbox):
        """Creates analog output boxes and buttons."""
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(QLabel('Analog Output Channels'))
        hbox_1.addStretch(2)
        vbox.addLayout(hbox_1)
        
        for i in range(2):
            hb = self.get_ao_widget(i, self.ao_channels_name[i])
            vbox.addLayout(hb)


    def create_do_view(self, vbox):
        """Creates digital output boxes and buttons."""
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(QLabel('Digital Output Channels'))
        hbox_1.addStretch(1)
        vbox.addLayout(hbox_1)
        
        for i in range(2):
            hb = self.get_do_widget(i, self.do_channels_name[i])
            vbox.addLayout(hb)



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
        #self.create_options_view(vbox)

        self.create_ai_view(vbox)

        self.create_ao_view(vbox)

        self.create_do_view(vbox)

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

        #print('new_data ' + str(data_flag) + ' ' + str(data) )

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
        """Update data field."""
        for name, l in d.iteritems():
            if name in self.textbox_ai:
                self.textbox_ai[name].setText(  '{0:.4f}V'.format(l['voltage']) )
    
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
