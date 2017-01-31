import sys
import os
import re
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui import MyCheckBox
import time
#import numpy as np
#import matplotlib.pyplot as plt
#from pix_threading import MyQThread
from plot_widgets import StripWidget, OpWorker, MyQThread, logthread
import active_reset_preamp as preamp

class MainWindow(QMainWindow):

    #__datadir = os.environ['DATADIR']
    # signals
    do0_on = pyqtSignal()
    do0_off = pyqtSignal()
    do1_on = pyqtSignal()
    do1_off = pyqtSignal()

    #NOTE that I'm using QRST_T- converter for QRST_T+.
    ai_channels_name = {0:'OUT',1:'UNDEF.',2:'OUT_BUF',3:'UNDEF.',4:'QRST_T+',5:'QGSET',6:'UNDEF.',7:'UNDEF.'}
    ai_channels_converters = {0:preamp.unit, 1:preamp.unit, 2:preamp.unit, 3:preamp.unit, 4:preamp.qrst_tm, 5:preamp.qgset, 6:preamp.unit, 7:preamp.unit }
    ao_channels_name = {0:'QRST_T+',1:'QGSET'}
    ao_channels_converters = {0:preamp.qrst_tm_ao,1:preamp.qgset_ao}
    ao_channels_unconverters = {0:preamp.qrst_tm,1:preamp.qgset}
    do_channels_name = {0:'CALIB',1:'QRST_T+'}

    CONVERT_AI = True
    
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

        self.plot_widgets = []

        # threads
        self.opwThread = None
        




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


        button = QPushButton("&Strip chart " + label)
        button.clicked.connect(self.on_ai_plot_widget)
        
        hbox.addWidget(button)

        self.textbox_ai[label] = textbox

        return hbox


    def on_ai_plot_widget(self):

        sending_button = self.sender()
        #name = sending_button.objectName()
        name = sending_button.text()
        m = re.match('.*\s(AI\d).*',name)
        if m != None:
            name = m.group(1)
            m = re.match('.*AI(\d).*',name)
            w = StripWidget(name, parent=None, show=True, n_integrate=1, max_hist=100, converter_fnc=self.ai_channels_converters[int(m.group(1))])
            QObject.connect(self, SIGNAL('new_data'),w.worker.new_data)
            #QObject.connect(self, SIGNAL('quit'),w.worker.close)
            self.plot_widgets.append(w)
        else:
            print('on_ai_plot_widget name:\"' + name + '\" is not a valid AI name?')
    
    
    def on_ao0_set(self):        
        y = float(self.textbox_ao['AO0'].text())
        x = self.ao_channels_converters[0](y)
        if x > 5.0:
            x = 5.0
        elif x < 0.0:
            x = 0.0
        print('ao0 val ' + str(y) + '   conv_val ' + str(x))
        self.emit(SIGNAL('new_ao'), 0, x)

    def on_ao1_set(self):
        y = float(self.textbox_ao['AO1'].text())
        x = self.ao_channels_converters[1](y)
        if x > 5.0:
            x = 5.0
        elif x < 0.0:
            x = 0.0
        print('ao1 val ' + str(y) + '   conv_val ' + str(x))
        self.emit(SIGNAL('new_ao'), 1, x)


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
            hbox.addWidget(QLabel(title + ' (' + label + ') [V]'))
        else:
            hbox.addWidget(QLabel(label))
        hbox.addWidget(textbox)
        button = QPushButton("Set")
        # use signals instead at some point
        #ao_signal = pyqtSignal(int, float)
        if id == 0:      
            self.connect(button, SIGNAL('clicked()'), self.on_ao0_set)
            textbox.returnPressed.connect(self.on_ao0_set)            
        else:            
            self.connect(button, SIGNAL('clicked()'), self.on_ao1_set)
            textbox.returnPressed.connect(self.on_ao1_set)
        hbox.addWidget(button)
        self.buttons_ao[label] = button
        self.textbox_ao[label] = textbox

        return hbox



    def update_ao_text(self):
        """ Update the analog output text based on the measured values."""
        # use the name to find the input channel
        for i,n_ao in self.ao_channels_name.iteritems():
            for k,n in self.ai_channels_name.iteritems():
                if n == n_ao:
                    v = float(self.textbox_ai['AI'+str(k)].text())
                    if self.CONVERT_AI:
                        # nothing to do, already converted
                        uv = v
                    else:
                        uv = self.ao_channels_unconverters[i](v) # = {0:preamp.unit,1:preamp.qgset}
                    self.textbox_ao['AO' + str(i)].setText(str('{0:.4f}'.format(uv)))
                    #print('found channel ' + n + ' k ' + str(k) + ' v ' + str(v) + ' uv ' + str(uv))
    

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
        hbox_1.addStretch(2)
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


    def create_script_view(self, vbox):
        """Creates digital output boxes and buttons."""
        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(QLabel('Scripts'))
        hbox_1.addStretch(2)
        vbox.addLayout(hbox_1)

        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(QLabel('Find O.P.'))
        self.op_button = QPushButton("&Find OP")
        self.op_button.clicked.connect(self.on_op)
        hbox_2.addWidget( self.op_button)                                    
        self.op_button_quit = QPushButton("&Quit OP")
        self.op_button_quit.clicked.connect(self.on_op_quit)
        hbox_2.addWidget( self.op_button_quit)                                    
        vbox.addLayout( hbox_2 )



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

        #self.create_do_view(vbox)

        self.create_script_view(vbox)

        
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

        # if it's the first one, update output text boxes
        if self.nframes < 5:
            self.update_ao_text()
        
        
        # send data to plot widgets
        self.emit(SIGNAL('new_data'), data_flag, data)

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
                uv = l
                # check if we are convertering these or not
                if self.CONVERT_AI:
                    #print('convert ' + name)
                    # find channel name to be used for look up
                    m = re.match('.*AI(\d).*',name)
                    if m != None:                        
                        uv = self.ai_channels_converters[int(m.group(1))](l) 
                        #print('convert ' + str(l) + ' to ' + str(uv) + ' for ' + name)
                self.textbox_ai[name].setText(  '{0:.4f}'.format(uv) )



    def opw_test(self, data):
        logthread('mainwin.opw_test ' + str(data))
    
                
    def on_op(self):
        """Attempt to find operating point."""
        # reset QGSET
        self.textbox_ao['AO1'].setText('-0.5')
        self.on_ao1_set()
        # set QRST_T+ to a large value to ensure switch will be closed
        self.textbox_ao['AO0'].setText('0.5')
        self.on_ao0_set()

        logthread('on_op')

        
        self.opwThread = OpWorker(self.opw_test, 1.3)
        
        
        #self.opwThread = MyQThread()
        self.opwThread.start()

        #self.opw = OpWorker(self.opw_test, 1.3)
        self.connect(self, SIGNAL('new_data'), self.opwThread.new_data)
        self.connect(self.opwThread, SIGNAL('opw_update'),self.opw_update)
        self.connect(self.opwThread, SIGNAL('opw_finished'),self.opw_finished)
        #self.opw.moveToThread( self.opwThread )        

    def opw_finished(self):
        print("WHAAAAT")
        self.disconnect(self.opw, SIGNAL('new_data'), self.opw.new_data)
        self.opwThread.quit()

    def opw_update(self, value):
        print("opw_update " + str(value))
        v = float(self.textbox_ai['AI5'].text())        
        v_updated = v + value
        print("opw_update v  " + str(v) + ' to ' + str(v_updated))        
        self.textbox_ao['AO1'].setText('{0:f}'.format(v_updated))
        self.on_ao1_set()


    def on_op_quit(self):
        self.disconnect(self, SIGNAL('new_data'), self.opwThread.new_data)
        self.opwThread.quit()
        can_exit = self.opwThread.wait(1000)        
        #can_exit = True
        if can_exit:
            print('[op] : thread quit successfully')            
        else:
            print('[op] :  thread quit timed out')
            self.opwThread.terminate()
            can_exit = self.opwThread.wait(1000)        
            if can_exit:
                print('[op] :  thread terminated successfully')            
            else:
                print('[PlotWidget] : ERROR  thread failed to die')
                #event.ignore()
    
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
        for w in self.plot_widgets:
            w.close()
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
