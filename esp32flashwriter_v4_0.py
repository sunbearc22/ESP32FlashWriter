#!/usr/bin/env python3

'''A GUI to detect ESP32 devices and write firmware to the ESP32 flash.

Repository: https://github.com/sunbearc22/ESP32FlashWriter

Tested on:
   tkinter -- v8.6  -- GUI development
   esptool -- v2.6  -- Espressif software to communicate and instruct esp32 device
   pyserial-- v3.4  -- Comincate with serial port
   Ubuntu  -- 16.04 -- OS

Acknowledgements:
- icon images from https://www.iconfinder.com/
- Like to thank Angus Gratton at https://github.com/projectgus for advices on
  handling issues related to esptool.py. 

Author: sunbear.c22@gmail.com
Date  : 2019-02-28
'''

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import tkinter.messagebox as tkMessageBox

import serial.tools.list_ports
import esptool
import os
from pprint import pprint
from serial.serialutil import SerialException, portNotOpenError
from termios import error as TerminosError



class App(ttk.Frame):

    def __init__( self, master=None, *args, **kw ):
        super().__init__( master,style='App.TFrame')
        #Attributes
        self.master = master
        self.style = None
        self.fonts = { 'default':('Times New Roman','12','normal'),
                       'header' :('Times New Roman','14','bold'),
                       'header1':('Times New Roman','12','normal','underline'),
                       'data'   :('Times New Roman','10','normal') }
        self._set_style()
        self._create_widgets()


    def _set_style( self ):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure( '.', cap=tk.ROUND, join=tk.ROUND, font=self.fonts['default'] )
        self.style.configure( 'App.TFrame',  )

        self.style.configure( 'TLabelframe',  )
        self.style.configure( 'header.TLabel', font=self.fonts['header'], anchor='w' )
        self.style.configure( 'header1.TLabel', font=self.fonts['header1'] )
        self.style.configure( 'detect.TLabel', font=self.fonts['default'], foreground='black' )
        self.style.configure( 'data.TLabel', font=self.fonts['data'] )
        self.style.configure( 'bytes.TLabel', font=self.fonts['default'], anchor='center' )
        self.style.configure( 'device.TButton', padding=0, relief='flat', borderwidth=0 )
        self.style.configure( 'find.TButton', padding=0, relief='flat', borderwidth=0 )
        self.style.configure( 'write.TLabel', font=self.fonts['default'], foreground='black' )


    def _create_widgets( self ):
        self.columnconfigure( 1, weight=1 )
        
        self.device = ESP32Device( self, self.style, self.fonts )
        self.flashfirmware = FlashFirmware( self, self.device, self.style,
                                             self.fonts )
        self.device.grid(        row=0, column=0, padx=10, pady=[10,5], sticky='we' )
        self.flashfirmware.grid( row=1, column=0, padx=10, pady=[5,10], sticky='we' )

        
    def ask_quit( self ):
        '''Confirmation to quit application.'''
        if tkMessageBox.askokcancel( "Quit","Quit ESP32 SPI Flash Writer?" ):
            self.device.shutdown() #Close port of serial.Serial() instance if exist.
            self.master.destroy() #Destroy the Tk Window instance.



class ESP32Device(ttk.Labelframe):
    '''GUI to create and monitor serial connection to ESP32 device.'''
    
    MSG0  = 'Please connect ESP32 and select Port.'
    MSG1  = 'ESP32 is used by another application.'
    MSG2  = 'Fail to Connect.'
    MSG2a = 'Fail to Connect. Try another Baud and select Port.'
    MSG3  = 'Connected: No Chip description.'
    
    BAUD  = [ 9600,11520,38400,115200,230400,921600 ]


    def __init__( self, master=None, style=None, fonts=None, *args, **kw ):
        super().__init__( master, *args, **kw )
        #Attributes
        self.master = master
        self.fonts = fonts
        self.style = style
        self.esp = None         #Selected esp32 device
        self.ports = None       #ttk.Combobox hosting detected serial devices
        self.bauds = None       #ttk.Combobox hosting known esp32 bauds
        self.connecting = False #Toggled True when connecting to esp32 else False
        self.status       = tk.StringVar( value=ESP32Device.MSG0 )
        self.mac          = tk.StringVar( value='' )
        self.features     = tk.StringVar( value='' )
        self.manufacturer = tk.StringVar( value='' )
        self.device       = tk.StringVar( value='' )
        self.flashsize    = tk.StringVar( value='' )
        self.port         = tk.StringVar( value='-- please select --' )
        self.baud         = tk.IntVar( value=esptool.ESPLoader.ESP_ROM_BAUD )
        self.pic_reset = tk.PhotoImage( file='./icon/iconfinder_Reset_40005a.png' )
        self._status_color = 'black'
        
        #Methods Initialized
        self._create_widgets()
        self._connect_esp()
        

    def _create_widgets( self ):
        print( '\ndef _create_widgets( self ):' )
        default = self.fonts['default']
        
        lb_title       = ttk.Label( self, text='ESP32 Device', style='header.TLabel' )
        lb_detect      = ttk.Label( self, textvariable=self.status, width=40, style='detect.TLabel')
        lb_mac         = ttk.Label( self, textvariable=self.mac, width=40, )
        lb_feature     = ttk.Label( self, textvariable=self.features, width=70, style='data.TLabel' )
        lb_manufacturer= ttk.Label( self, textvariable=self.manufacturer, width=70, style='data.TLabel' )
        lb_device      = ttk.Label( self, textvariable=self.device, width=70, style='data.TLabel' )
        lb_flashsize   = ttk.Label( self, textvariable=self.flashsize, width=70, style='data.TLabel' )
        lb_port   = ttk.Label( self, text='Port', style='header1.TLabel' )
        lb_baud   = ttk.Label( self, text='Baud', style='header1.TLabel' )

        self['labelwidget'] = lb_title

        self.ports = ttk.Combobox( self, state="readonly",
                                   textvariable=self.port, width=15,
                                   postcommand=self._list_ports,
                                   font=default, justify='center' ) #font of Entry
        self.ports.option_add('*TCombobox*Listbox.Font', default) #font of dropdown list
        self.ports.option_add('*TCombobox*Listbox.Justify', 'center') #font of dropdown list
        self.ports.bind('<<ComboboxSelected>>', self._connect_esp)
        self.ports.bind('<KeyPress-Return>', self._invoke_ports)

        vcmd = ( self.register( self._validate_baud ), '%S' )
        self.bauds = ttk.Combobox( self, takefocus=True, #state="readonly",
                                   value=ESP32Device.BAUD, textvariable=self.baud,
                                   width=9, font=default, justify='center',  #font of Entry
                                   validate='key', validatecommand=vcmd ) 
        self.bauds.option_add('*TCombobox*Listbox.Font', default) #font of dropdown list
        self.bauds['state'] = 'disable'
        self.bauds.bind('<<ComboboxSelected>>', self._format_baud)
        self.bauds.bind('<KeyPress-Return>', self._invoke_bauds)

        baud_reset = ttk.Button( self, text='Reset', width=5, image=self.pic_reset,
                                 style='device.TButton', command=self._reset_baud )
        baud_reset.bind('<KeyPress-Return>', self._reset_baud)
        
        
        lb_detect.grid( row=1, column=0, padx=10, pady=[0,0], sticky='ew',  )
        lb_mac.grid(         row=2, column=0, padx=10, pady=[0,0], sticky='ew',  )
        lb_feature.grid(     row=3, column=0, padx=10, pady=[0,0], sticky='ew', columnspan=4  )
        lb_manufacturer.grid(row=4, column=0, padx=10, pady=[0,0], sticky='ew', columnspan=4  )
        lb_device.grid(      row=5, column=0, padx=10, pady=[0,0], sticky='ew', columnspan=4  )
        lb_flashsize.grid(   row=6, column=0, padx=10, pady=[0,10], sticky='ew', columnspan=4  )
        lb_port.grid(        row=0, column=1, )
        lb_baud.grid(        row=0, column=2, )
        self.ports.grid( row=1, column=1, padx=[0,0],  pady=[0,0], ipady=4 )
        self.bauds.grid( row=1, column=2, padx=[10,0], pady=[0,0], ipady=4 )
        baud_reset.grid( row=1, column=3, padx=[2,10], pady=[0,0])


    #PostCommand:
    def _list_ports( self ):
        print( '\ndef _list_ports( self ):' )
        devices = [ port.device for port in serial.tools.list_ports.grep('ttyUSB') ]
        # In module "serial.tools.list_ports", its .grep() method returns 
        #  an iterable of its ListPortInfo class object
        if devices: #Update Combobox's dropdown list values
            self.ports['values'] = sorted( devices )
            self.bauds['state'] = 'normal'
        else:
            self.ports['values'] = 'None_Found'
            self.bauds['state'] = 'disable'
        

    #Event Handlers:
    def _invoke_ports( self, event ):
        self._list_ports()
        self.ports.event_generate('<Down>')
        
        
    def _invoke_bauds( self, event ):
        self.bauds.event_generate('<Down>')
        
        
    def _reset_baud( self, event=None ):
        self.baud.set( esptool.ESPLoader.ESP_ROM_BAUD )


    def _format_baud( self, event=None ):
        print( '\ndef _format_baud( self, event=None ):' )
        self.bauds.selection_clear()

        
    def _connect_esp( self, event=None):
        '''Connect to ESP32. Parent method.

        self.connecting=True  when connecting, .
        self.connecting=False when connected or when connection fails.'''
        self._sop_for_connecting()

        ports = self.ports['values']; print("ports =", ports)
        port = self.port.get(); print("port =", port) 
        if not ports:
            #No port detected
            self._sop_for_not_connected()
            self.status.set( ESP32Device.MSG0 ) 
        elif 'None_Found' not in ports : 
            #Port(s) detected
            portIsBusy = self._port_is_busy( port )
            if not portIsBusy:           
                #Selected port can be used, connect to it.
                self._monitor_esp_connection()
                self._create_esp_connection()
                self.connecting = False
            else:
                #Selected port is used by other apps(don't use it)
                self.esp = None
                self.connecting = False
                self.status.set( ESP32Device.MSG1 )
        else:
            self._sop_for_not_connected()
            self.status.set( ESP32Device.MSG0 )
            self.connecting = False


    #Methods:
    def _sop_for_not_connected( self ):
        self.esp = None
        self.connecting = False
        self.port.set( '-- please select --' )
        self.ports.selection_clear()
        self.mac.set( '' )
        self.features.set( '' )
        self.manufacturer.set( '' )
        self.device.set( '' )
        self.flashsize.set( '' )


    def _sop_for_connecting( self ):
        self.connecting = True
        self.status.set( 'Connecting.....' )
        self.ports.selection_clear()
        self.mac.set( '' )
        self.features.set( '' )
        self.manufacturer.set( '' )
        self.device.set( '' )
        self.flashsize.set( '' )
        self.update_idletasks()
        

    def _port_is_busy( self, port):
        #Check if picocom is using the port
        portname = os.path.basename( port )
        linux_lock = "/var/lock/"
        files = os.listdir( linux_lock )       
        for file in files:
           filename = os.path.basename( file )
           if portname in filename:
               print('picocom is using port')
               return True

        #Todo: Need a more general algorithim to determine wheater the port is
        #      used by other applications.

        print('device is available.')
        return False #port is not busy
             

    def _create_esp_connection( self ):
        '''Connect to ESP32. Child method.

        Need to indicate self.connecting=False when self.esp.connect() encounter
        an exception. No need to update self.connecting=True when connected
        as it is done Parent method.'''
        port = self.port.get()
        try:
            baud = self.baud.get()
        except tk.TclError as err:
            baud = esptool.ESPLoader.ESP_ROM_BAUD
            self.baud.set( baud )
            self.bauds.update_idletasks()
        
        try:
            self.esp = esptool.ESP32ROM( port, baud, #trace_enabled=True,
                                         )
            #Created attributes:
            # self.esp._port - Is an instance of serial.Serial() or a compatible object
            #                  see https://pythonhosted.org/pyserial/pyserial_api.html?highlight=setdtr#serial.Serial
            #                - It will close the defined serial port when self.esp._port is freed, i.e.
            #                  when tk.Tk() instance is destroyed. 
            #                - set self.esp._port.baud
            # self.esp._slip_reader   - Is a generator to read SLIP packets from the
            #                           defined serial port in self.esp._port.
            # self.esp._trace_enabled - Denotes wheather tracing is activated.
            #                           For debugging. Default value is "False"
            # self.esp._last_trace    - stores time.time()
            self.esp.connect()
        except (esptool.FatalError, OSError) as err:
            self.esp = None
            self.connecting = False
            if "Failed to connect to ESP32: Timed out waiting for packet header" in err.__str__():
                self.status.set( ESP32Device.MSG2a ) #Fail to Connect. Try another Baud value.
            else:
                self.status.set( ESP32Device.MSG2 ) #Fail to Connect.
                raise err
        except SerialException as err:
            self.esp = None
            self.connecting = False
            print( "{} ESP32 device is busy".format( port ) )
            self.status.set( ESP32Device.MSG1 )
            raise err
        else:
            print( 'esp created & connected esp' )
            pprint( self.esp.__dict__ )


    def _monitor_esp_connection(self):
        '''Get ESP32 chip description, features, manufacturer, device and flashsize.

        Thereafter, initiate after() method to check if serial connection continues
        or is broken using self._connected= True or False, respectively.

        Parent method to self._check_connection() method.'''
                                        
        def get_info():
            mac = self.esp.read_mac()
            mac = ':'.join( format(x,'02x') for x in mac )
            # '02x' means use at least 2 digits with zeros to pad to length,
            #       and x means lower-case hexadecimal.

            features = self.esp.get_chip_features()
            features = ', '.join(features)
            
            flash_id = self.esp.flash_id()
            manufacturer = '{:02x}'.format(flash_id & 0xff)
            
            flid_lowbyte = (flash_id >> 16) & 0xFF
            device = '{:02x}{:02x}'.format( (flash_id >> 8) & 0xff, flid_lowbyte )
            
            flashsize = esptool.DETECTED_FLASH_SIZES.get( flid_lowbyte, "Unknown")
            flashsize = '{}'.format( '4MB' if flashsize == "Unknown" else flashsize )

            return mac, features, manufacturer, device, flashsize

        if 'blue' in self._status_color:
            self._status_color = 'black'
            self.style.configure( 'detect.TLabel', foreground='black' )
        elif 'black' in self._status_color:
            self._status_color = 'blue'
            self.style.configure( 'detect.TLabel', foreground='blue' )
        self.update_idletasks()
                
        if not self.connecting:
            if self.esp:
                print('Connected')
                try: 
                    chip_type = self.esp.get_chip_description()
                except esptool.FatalError:
                    # Connected: No Chip description.
                    status = ESP32Device.MSG3
                else:
                    # Connected: Have Chip description.
                    status = 'Connected: {}.'.format( chip_type )                   
                    self.status.set( status )
                    mac, features, manufacturer, device, flashsize = get_info()
                    self.mac.set('{:19}{}{}'.format('','Mac: ',mac) )
                    self.features.set('{:25}{}{}'.format('','Features: ',features) )
                    self.manufacturer.set('{:25}{}{}'.format('','Manufacturer: ',manufacturer) )
                    self.device.set('{:25}{}{}'.format('','Device: ',device) )
                    self.flashsize.set('{:25}{}{}'.format('','Flash size: ', flashsize) )
                    self._connected = True
                    self._check_connection() # Check esp32 device is connected every 1s.
                #print( status )
                self.connected = True
            else:
                print( 'Fail to Connect.' )
                print( 'self.status.get() = ', self.status.get() )
                self.connected = False
        else:
            print('Connecting')
            self.after(500, self._monitor_esp_connection) # Call this method after 500 ms.


    def _check_connection( self ):
        '''Check ESP32 connectio is ok or broken. 

        If connection is broken, i.e. result in exception, update self._connected=False.
        Child method of _monitor_esp_connection.'''
        if self._connected:
            try:
                self.esp.flush_input()
            except SerialException as err:
                self._connected = False
                print( 'SerialException: ', err )
                self.after( 500, self._check_connection ) # Check connection every 500ms.
            except TerminosError as err:
                self._connected = False
                print( 'termios.error: ', err )
                self.after( 500, self._check_connection ) # Check connection every 500ms.
            except TypeError as err:
                self._connected = False
                self.esp._port.close()
                print( 'TypeError: ', err )
                self.after( 500, self._check_connection ) # Check connection every 500ms.
            else:
                #Some data was received
                self.after( 2000, self._check_connection ) # Check connection every 5s.
        else:
            self._sop_for_not_connected()


    def _validate_baud( self, S ):
        # %S = the text string being inserted or deleted, if any
        # Only digit entries are valid.
        if S.isdigit():
            return True
        else:
            self.bell()
            return False


    def shutdown( self ):
        '''Close ESP32 device port.'''
        if self.esp:
            self.esp._port.__del__() # Close serial port when serial.Serial() instance is freed
            #self.esp._port.close() # Close serial port immediately.



class FlashFirmware(ttk.Labelframe):

    def __init__( self, master, device, style=None, fonts=None, *args, **kw ):
        super().__init__( master, *args, **kw )
        #Attributes
        self.master = master
        self.device = device # an instance of ESP32Device()
        self.style = style
        self.fonts = fonts
        self._filename = tk.StringVar()
        self._filebasename = tk.StringVar()
        self._address = tk.StringVar()
        self._size = tk.IntVar()
        self._erase_all = tk.IntVar()
        self.status = tk.StringVar()
        self.pic_folder = tk.PhotoImage( file='./icon/iconfinder_folder_299060_x28a.png' )
        self.args = None
        self._canwrite = True
        #Methods Initialized
        self._create_widgets()
        

    def _create_widgets( self ):
        default = self.fonts['default']

        lb_title = ttk.Label( self, text='Flash Firmware', style='header.TLabel' )
        self['labelwidget'] = lb_title

        #Row0
        lb_source = ttk.Label( self, text='Source', style='header1.TLabel' )
        lb_byte   = ttk.Label( self, text='Bytes', style='header1.TLabel' )
        lb_offset = ttk.Label( self, text='Flash Offset', style='header1.TLabel' )
        lb_erase  = ttk.Label( self, text='Erase Entire Flash', style='header1.TLabel' )
        #Row1
        source = ttk.Entry( self, textvariable=self._filebasename, font=default,
                            width=36, state="readonly", takefocus=False,
                            justify='center' )
        find = ttk.Button( self, text='...', width=2, command=self._get_sources,
                           image=self.pic_folder, style='find.TButton' )
        find.bind( '<KeyPress-Return>', self._get_sources )
        byte = ttk.Label( self, textvariable=self._size, width=9,
                          style='bytes.TLabel' )
        offset = ttk.Entry( self, textvariable=self._address, font=default,
                            width=9, justify='center' )
        self._address.set('0x1000')
        self._yes = ttk.Radiobutton( self, text='Yes', value=True, variable=self._erase_all )
        self._no  = ttk.Radiobutton( self, text='No', value=False, variable=self._erase_all )
        self._yes.bind( '<KeyPress-Return>', self._set_erase_all )
        self._no.bind( '<KeyPress-Return>', self._set_erase_all )
        
        #Row2
        self._write = ttk.Button( self, text='WRITE', command=self._write_flash )
        lb_detect = ttk.Label( self, textvariable=self.status, width=40,
                               style='write.TLabel')
        
        # Position widgets 
        lb_source.grid( row=0, column=0, padx=[10, 0], pady=[10,0], )
        lb_byte.grid(   row=0, column=2, padx=[10, 0], pady=[10,0], )
        lb_offset.grid( row=0, column=3, padx=[10, 0], pady=[10,0], )
        lb_erase.grid(  row=0, column=4, padx=[10,10], pady=[10,0], columnspan=2 )
        source.grid(    row=1, column=0, padx=[10,0], pady=[5,0], ipady=3 )
        find.grid(      row=1, column=1, padx=[ 2,0], pady=[5,0], )
        byte.grid(      row=1, column=2, padx=[10,0], pady=[5,0], )
        offset.grid(    row=1, column=3, padx=[10,0], pady=[5,0], ipady=3 )
        self._yes.grid( row=1, column=4, padx=[ 5,0],)
        self._no.grid(  row=1, column=5, ) 
        self._write.grid(row=2, column=3, padx=10, pady=[10,10], columnspan=3, sticky='nsew', )
        lb_detect.grid( row=2, column=0, padx=10, pady=[10,10], columnspan=3, sticky='nsew', )

       

    #### Widget Methods
    def _get_sources( self, event=None ):
        filename = filedialog.askopenfilename(
            #defaultextension='bin',
            filetypes=[('bin','*.bin'),('py','*.py'), ('all files','*.*')],
            title='Select Firmware' )
        if filename:
            self._filename.set( filename )
            self._filebasename.set( os.path.basename( filename ) )
            self._size.set( self._get_file_size( filename ) )
        else:
            self._filename.set( '' )
            self._filebasename.set( os.path.basename( '' ) )
            self._size.set( 0 )
            

    def _get_file_size( self, file ):
        try:
            size = os.path.getsize( file )
        except ValueError:
            size = 0
        return size


    def _set_erase_all( self, event ):
        if event.widget is self._yes:
            if self._erase_all.get():
                self._erase_all.set( value=False )
            else:
                self._erase_all.set( value=True )
        elif event.widget is self._no:
            if self._erase_all.get():
                self._erase_all.set( value=False )
            else:
                self._erase_all.set( value=True )


    def update_status( self, msg ):
        self.status.set(msg)
        self.update_idletasks()


    #### Commands
    def _write_flash( self ):
        #1.Setup widgets
        self._status_color = 'blue'
        self.style.configure( 'write.TLabel', foreground='blue' )
        self._write['state'] = 'disable'
        self.update_status('Preprocessing....')

        #2. Create agrs
        if not self._create_args():
            print( "\nFlashFirmware: Failed to create args." )
        
        #3. Setup esp
        args = self.args
        if not self.device.esp:
            self.device._connect_esp()
            esp = self.device.esp
        else:
            esp = self.device.esp
            esp.flush_input()
            #esp.connect()
            #esp._slip_reader = esptool.slip_reader(esp._port, esp.trace)

        if not args.no_stub:
            print('if not args.no_stub:')
            esp = esp.run_stub()

        if args.baud != esptool.ESPLoader.ESP_ROM_BAUD:
            try:
                esp.change_baud(args.baud)
            except NotImplementedInROMError:
                print("WARNING: ROM doesn't support changing baud rate. Keeping initial baud rate %d" % initial_baud)

        # override common SPI flash parameter stuff if configured to do so
        if hasattr(args, "spi_connection") and args.spi_connection is not None:
            if esp.CHIP_NAME != "ESP32":
                raise FatalError("Chip %s does not support --spi-connection option." % esp.CHIP_NAME)
            print("Configuring SPI flash mode...")
            esp.flash_spi_attach(args.spi_connection)
        elif args.no_stub:
            print("Enabling default SPI flash mode...")
            # ROM loader doesn't enable flash unless we explicitly do it
            esp.flash_spi_attach(0)

        if hasattr(args, "flash_size"):
            print("Configuring flash size...")
            esptool.detect_flash_size(esp, args)
            esp.flash_set_parameters( esptool.flash_size_bytes(args.flash_size) )

        print('\nargs = ')
        pprint( args.__dict__ )
        print('\nesp = ')
        pprint( esp.__dict__ )
        print('\nesp._port = ')
        pprint( esp._port.__dict__ )

        #4. Start writing
        self._writing = True
        self._completed = False
        self.update_status('Writing....')
        try:
            esptool.write_flash( esp, args )
        except esptool.FatalError:
            raise
        else:
            print('Hard resetting via RTS pin...')
            esp.hard_reset()
        finally:
            try:  # Clean up AddrFilenamePairAction files
                for address, argfile in args.addr_filename:
                    argfile.close()
            except AttributeError:
                pass

        #esp._port.close()

        #5. Post writing setups
        self.update_status('Written Firmware to Flash.')
        self._writing = False
        self._completed = True
        self._write['state'] = 'normal'


    #### Command Methods
    def _create_args(self):
        self.update_status('Preprocessing: args....')
        
        self.args = Args()
        self.args.chip = 'esp32'
        self.args.no_stub = False

        self.args.baud = self.device.baud.get()
        if not self.args.baud:
            self.update_status( "Can't write: No Baud." )
            return False
 
        self.args.port = self.device.port.get()
        if not self.args.port or self.args.port=='-- please select --':
            self.update_status( "Can't write: No Port." )
            return False

        if not self._set_args_flash_size():
            self.update_status( "Can't write: No Flash size." )
            return False

        if not self._set_args_addr_filename():
            self.update_status( "Can't write: No Offset/Source." )
            return False

        self._set_args_erase_all()
        return True


    def _set_args_flash_size( self ):
        for key in esptool.ESP32ROM.FLASH_SIZES:
            if key in self.device.flashsize.get():
                self.args.flash_size = key
        if self.args.flash_size == 'detect':
            print( "Invalid flash size used." )
            return False
        else:
            return True


    def _set_args_addr_filename( self ):
        '''Convert addr, filename from a tuple of string & string to a tuple of
        integer and open file.'''
        self.args.addr_filename = []
        try:
            addr = self._address.get()
            addr = int( addr, 16 )
        except ValueError as err:
            #addr is not a hexidecimal 
            return False
        else:
            try:
                filename = self._filename.get()
                filename = open(filename,'rb+')
            except IOError as err:
                #Error open filename
                return False
            else:
                self.args.addr_filename.append( ( addr, filename ) )
        return True


    def _set_args_erase_all( self ):
        if self._erase_all.get():
            self.args.erase_all = True
        else:
            self.args.erase_all = False



class Args(object):

    def __init__( self ):
        self.chip = None
        self.port = None
        #self.baud = esptool.ESPLoader.ESP_ROM_BAUD
        self.baud = None
        self.before = 'default_reset'
        self.after = 'hard_reset'
        self.no_stub = True
        self.trace = True
        self.override_vddsdio = "Off"

        self.spi_connection = None

        #positional arguments:
        #load_ram
        self.load_ram = None
        self.filename = None

        #dump_mem
        self.dump_mem = None
        self.address = None
        self.size = None
        self.filename = None

        #read_mem
        self.read_mem = None
        self.address = None

        #write_mem
        self.write_mem = None
        self.address = None
        self.value = None
        self.mask = None

        #spi_flash
        self.flash_freq = '40m'
        self.flash_mode = 'dio' #Needs 'dio' to work 
        self.flash_size = 'detect'
        #self.flash_size = '4MB'

        #write_flash
        self.write_flash = None
        self.erase_all = False
        self.addr_filename = None
        self.no_progress = True
        self.verify = True
        self.compress = True
        self.no_compress = False


def main():
    root = tk.Tk()
    root.title('ESP32 FLASH WRITER')
    root.geometry('680x390+0+24')
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    app = App( root )
    app.grid(row=0, column=0, sticky='nsew')

    #Activate Tk window mainloop to track GUI events
    root.protocol("WM_DELETE_WINDOW", app.ask_quit) #Tell Tk window instance what to do before it is destroyed.
    root.mainloop()


if __name__ == '__main__':
    main()
