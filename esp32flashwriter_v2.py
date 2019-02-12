import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import serial.tools.list_ports
import esptool
import os
import hashlib
import zlib
import sys
import time
import struct
from pprint import pprint

BAUD = [ 9600,11520,38400,115200,230400,921600 ]



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
        self.style.configure( '.', cap=tk.ROUND, join=tk.ROUND, font=self.fonts['default'] )
        self.style.configure( 'App.TFrame',  )

        self.style.configure( 'TLabelframe',  background='light green')
        self.style.configure( 'header.TLabel', font=self.fonts['header'], anchor='w', foreground='blue' )
        self.style.configure( 'header1.TLabel', font=self.fonts['header1'] )
        self.style.configure( 'data.TLabel', font=self.fonts['data'] )
        self.style.configure( 'bytes.TLabel', font=self.fonts['default'], anchor='e' )
        self.style.configure( 'header1.TCheckbutton', font=self.fonts['header1'] )
        self.style.configure( 'device.TButton' )
        self.style.configure( 'device.TSpinbox' )
        self.style.configure( 'device.TSpinbox.oadding', padding=10 )


    def _create_widgets( self ):
        self.columnconfigure( 1, weight=1 )
        
        self.device = ESPDevice( self, self.style, self.fonts )
        self.src_dest = SourcesDestinations( self, self.device, self.style,
                                             self.fonts )
        self.write_flash = WriteFlash( self, self.device, self.src_dest,
                                       self.style, self.fonts )

        self.device.grid( row=0, column=0, padx=10, pady=[10,5], sticky='we' )
        self.src_dest.grid( row=1, column=0, padx=10, pady=[5,10], sticky='we' )
        self.write_flash.grid( row=2, column=0, padx=10, pady=[5,10], sticky='we' )

        

class ESPDevice(ttk.Labelframe):

    def __init__( self, master=None, style=None, fonts=None, *args, **kw ):
        super().__init__( master, *args, **kw )
        #Attributes
        self.master = master
        self.fonts = fonts
        self.style = style
        self.esp = None          #Selected esp32 device
        self.ports = None        #ttk.Combobox hosting detectable serial device
        self.bauds = None        #ttk.Combobox hosting known esp32 bauds
        self.detecting = False   #Toogle True when detecting esp32
        self.status       = tk.StringVar( value='Not Detected' )
        self.mac          = tk.StringVar( value=' ' )
        self.features     = tk.StringVar( value=' ' )
        self.manufacturer = tk.StringVar( value=' ' )
        self.device       = tk.StringVar( value=' ' )
        self.flashsize    = tk.StringVar( value=' ' )
        self.port         = tk.StringVar( value='-- please select --' )
        self.baud         = tk.IntVar( value=esptool.ESPLoader.ESP_ROM_BAUD )
        #Methods Initialized
        self._create_widgets()
        

    def _create_widgets( self ):
        default = self.fonts['default']
        
        lb_title       = ttk.Label( self, text='ESP32 Device', style='header.TLabel' )
        lb_detect      = ttk.Label( self, textvariable=self.status, width=40, )
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
        self.ports.bind('<<ComboboxSelected>>', self._detect_esp_v1)

        vcmd = ( self.register( self._validate_baud ), '%S' )
        self.bauds = ttk.Combobox( self, value=BAUD, textvariable=self.baud,
                                   width=9, font=default, justify='center',  #font of Entry
                                   validate='key', validatecommand=vcmd ) 
        self.bauds.option_add('*TCombobox*Listbox.Font', default) #font of dropdown list

        baud_reset = ttk.Button( self, text='Reset', width=5,
                                 style='device.TButton',
                                 command=self._resetbaud )
        
        lb_detect.grid(      row=0, column=0, padx=10, pady=[10,0], sticky='ew',  )
        lb_mac.grid(         row=1, column=0, padx=10, pady=[0,0], sticky='ew',  )
        lb_feature.grid(     row=2, column=0, padx=10, pady=[5,0], sticky='ew', columnspan=4  )
        lb_manufacturer.grid(row=3, column=0, padx=10, pady=[0,0], sticky='ew', columnspan=4  )
        lb_device.grid(      row=4, column=0, padx=10, pady=[0,0], sticky='ew', columnspan=4  )
        lb_flashsize.grid(   row=5, column=0, padx=10, pady=[0,10], sticky='ew', columnspan=4  )
        lb_port.grid(        row=0, column=1, pady=[10,0],)
        lb_baud.grid(        row=0, column=2, pady=[10,0],)
        self.ports.grid( row=1, column=1, padx=[10,0], pady=[0,0], ipady=4 )
        self.bauds.grid( row=1, column=2, padx=[10,0], pady=[0,0], ipady=4 )
        baud_reset.grid( row=1, column=3, padx=[0,10], pady=[0,0])


    def _resetbaud( self ):
        self.baud.set( esptool.ESPLoader.ESP_ROM_BAUD )


    def _list_ports( self ):
        devices = [ port.device for port in serial.tools.list_ports.comports() ]
        # In module "serial.tools.list_ports", its .comports() method returns 
        #  an iterable of its ListPortInfo class object
        self.ports['values'] = sorted( devices ) #dropdown list values
        

    def _detect_esp_v1( self, event=None):
        print( 'def _detect_esp( self, event ):' )
        self.detecting = True
        self.status.set( 'Detecting.....' )
        self.mac.set( '' )
        self.features.set( '' )
        self.manufacturer.set( '' )
        self.device.set( '' )
        self.flashsize.set( '' )
        self.update_idletasks()
        self._detect_esp_progress_update_v1()

        try:
            self.esp = esptool.ESP32ROM( self.port.get(), self.baud.get(), #trace_enabled=True,
                                         )
            self.esp.connect()
        except (esptool.FatalError, OSError) as err:
            self.esp = None
            self.detecting = False
            raise
            print( "{} failed to connect to a Espressif device: {}".format( port, err ) )
        else:
            print( 'self.esp = ', self.esp.__dict__ )
            self.detecting = False


    def _detect_esp_progress_update_v1(self):
                                         
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
            
            #flashsize = 'Detected flash size: %s' % ( esptool.DETECTED_FLASH_SIZES.get( flid_lowbyte, "Unknown" ) )
            flashsize = '{}'.format( esptool.DETECTED_FLASH_SIZES.get( flid_lowbyte, "4MB" ) )

            return mac, features, manufacturer, device, flashsize


        if not self.detecting:
            if not self.esp:
                print('Fail to Detect')
                self.status.set( 'Fail to Detect' )
            else:
                print('Detected')
                try:
                    chip_type = self.esp.get_chip_description()
                    status = 'Detected: {}.'.format( chip_type )
                except esptool.FatalError:
                    status = 'Detected unknown chip type.'.format( mac )
                #print( status )
                mac, features, manufacturer, device, flashsize = get_info()
                self.status.set( status )
                self.mac.set('{:16}{}{}'.format('','Mac: ',mac) )
                self.features.set('{:22}{}{}'.format('','Features: ',features) )
                self.manufacturer.set('{:22}{}{}'.format('','Manufacturer: ',manufacturer) )
                self.device.set('{:22}{}{}'.format('','Device: ',device) )
                self.flashsize.set('{:22}{}{}'.format('','Flash size: ', flashsize) )
        else:
            print('Detecting')
            self.after(500, self._detect_esp_progress_update_v1) # Call this method after 500 ms.


    def _validate_baud( self, S ):
        # %S = the text string being inserted or deleted, if any
        # Only digit entries are valid.
        if S.isdigit():
            print(S, ' is allowed.')
            return True
        else:
            self.bell()
            print(S, ' is not allowed.')
            return False



class SourcesDestinations(ttk.Labelframe):

    def __init__( self, master, device, style=None, fonts=None, *args, **kw ):
        super().__init__( master, *args, **kw )
        #Attributes
        self.master = master
        self.device = device # an instance of ESPDevice()
        self.style = style
        self.fonts = fonts
        self._writes = []    # list of ttk.Checkbutton()
        self._filenames = [] # list of tk.StringVar()
        self._sizes = []     # list of tk.IntVar()
        self._addresses = [] # list of tk.StringVar()
        self.addr_filename = []
        #Methods Initialized
        self._create_widgets()
        

    def _create_widgets( self ):
        default = self.fonts['default']

        lb_title = ttk.Label( self, text='Firmwares / Files', style='header.TLabel' )
        self['labelwidget'] = lb_title

        ttk.Label( self, text='Write', style='header1.TLabel' ).\
                    grid( row=0, column=0, padx=[10,0], pady=[10,0] )
        ttk.Label( self, text='Source', style='header1.TLabel' ).\
                    grid( row=0, column=1, padx=[10,0], pady=[10,0] )
        ttk.Label( self, text='Bytes', style='header1.TLabel' ).\
                    grid( row=0, column=3, padx=[10,0], pady=[10,0] )
        ttk.Label( self, text='Destination', style='header1.TLabel' ).\
                    grid( row=0, column=4, padx=[40,10], pady=[10,0] )
       
        maxrows = 5
        for i in range(maxrows):
            
            if i==0: t=5
            else: t=2
                
            if i==maxrows-1: b=10
            else: b=0
            
            
            self._writes.append( tk.IntVar() )
            ttk.Checkbutton( self, variable=self._writes[i],
                             style='header1.TCheckbutton',
                             command=self._set_addr_filename ).\
                             grid( row=i+1, column=0, padx=[10,0], pady=[t,b],
                                   ipady=3 )

            self._filenames.append( tk.StringVar() )
            ttk.Entry( self, textvariable=self._filenames[i], font=default,
                       width=40,  state="readonly",).\
                       grid( row=i+1, column=1, padx=[5,0], pady=[t,b], ipady=3 )

            ttk.Button( self, text='...', width=2,
                        command=lambda i=i:self._get_firmware(i) ).\
                        grid( row=i+1, column=2, padx=[5,0], pady=[t,b] )
            
            self._sizes.append( tk.IntVar() )
            ttk.Label( self, textvariable=self._sizes[i], width=9,
                       style='bytes.TLabel',).\
                       grid( row=i+1, column=3, padx=[5,0], pady=[t,b] )

            self._addresses.append( tk.StringVar() )
            ttk.Entry( self, textvariable=self._addresses[i], font=default,
                       width=10, justify='right' ).\
                       grid( row=i+1, column=4, padx=[40,10], pady=[t,b], ipady=3 )

        self._addresses[0].set('0x1000')
        self._addresses[1].set('0x4000')
        self._addresses[2].set('0x10000')


    def _get_firmware( self, i ):
        filename = filedialog.askopenfilename(
            #defaultextension='bin',
            filetypes=[('bin','*.bin'),('py','*.py'), ('all files','*.*')],
            title='Select Firmware' )
        self._filenames[i].set( filename )
        self._sizes[i].set( self._get_file_size( filename ) )


    def _get_file_size( self, file ):
        print('file = ', file )
        try:
            size = os.path.getsize( file )
        except :
            size = 0
        print('size = ', size)
        return size


    def _set_addr_filename( self ):
        self.addr_filename = []
        for i, writ in enumerate( self._writes ):
            if writ.get():
                self.addr_filename.append( ( self._addresses[i].get(),
                                             self._filenames[i].get() ) )
        print( '\nself.addr_filename = ', self.addr_filename )


        
class WriteFlash(ttk.Labelframe):

    def __init__( self, master, device, src_dest, style=None, fonts=None,
                  *args, **kw ):
        super().__init__( master, *args, **kw )
        #Attributes
        self.master = master
        self.device = device # an instance of ESPDevice()
        self.src_dest = src_dest # an instance of ESPDevice()
        self.style = style
        self.fonts = fonts
        #Methods Initialized
        self._create_widgets()


    def _create_widgets( self ):
        default = self.fonts['default']

        lb_title = ttk.Label( self, text='Write Flash', style='header.TLabel' )
        self['labelwidget'] = lb_title

        flash_btn = ttk.Button( self, text='WRITE', command=self._write_flash )
        flash_btn.grid( row=0, column=0, padx=10, pady=[5,10], )


    def _set_args(self):
        self.args = Args( self.device )
        self.args.chip = 'esp32'
        self.args.baud = self.device.baud.get()
        self.args.port = self.device.port.get()

        self._set_args_flash_size()
        self._set_args_addr_filename()
        

    def _set_args_flash_size( self ):
        #FLASH_SIZES = {'1MB':0x00,'2MB':0x10,'4MB':0x20,'8MB':0x30,'16MB':0x40}
        for key in esptool.ESP32ROM.FLASH_SIZES:
            if key in self.device.flashsize.get():
                self.args.flash_size = key
                break
        print('\nflash_size in bytes =', esptool.flash_size_bytes( self.args.flash_size))
        if self.args.flash_size == 'detect':
            raise Exception( "Invalid flash size used.")


    def _set_args_addr_filename( self ):
        '''Convert addr, filename from string & string to integer and open file.'''
        self.args.addr_filename = []
        if len( self.src_dest.addr_filename ) >= 1:
            for addr, filename in self.src_dest.addr_filename:
                print(type(addr), type(filename) )
                self.args.addr_filename.append( ( int(addr,16), open(filename,'rb+') ) )
        #print( 'self.args.__dict__ =', self.args.__dict__ )
        
        
    def _write_flash( self ):
        self._set_args()
        args = self.args
        esp = self.device.esp
        print('\nesp.__dict__ = ', esp.__dict__)
        print('\nargs.__dict__ = ', args.__dict__)

        '''try:
            esptool.write_flash( esp, args )
        except esptool.FatalError:
            raise
        '''

        # set args.compress based on default behaviour:
        # -> if either --compress or --no-compress is set, honour that
        # -> otherwise, set --compress unless --no-stub is set
        if args.compress is None and not args.no_compress:
            args.compress = not args.no_stub
        print('\nargs.compress = ',args.compress)

        print('\nVerify file sizes fit in flash' )
        # verify file sizes fit in flash
        flash_end = esptool.flash_size_bytes(args.flash_size)
        print('\nflash_end =', type(flash_end), flash_end )
        for address, argfile in args.addr_filename:
            argfile.seek(0,2)  # seek to end
            print('address =', type(address), address )
            print('argfile.tell() =', type(argfile.tell()), argfile.tell() )
            if address + argfile.tell() > flash_end:
                raise FatalError(("File %s (length %d) at offset %d will not fit in %d bytes of flash. " +
                                 "Use --flash-size argument, or change flashing address.")
                                 % (argfile.name, argfile.tell(), address, flash_end))
        argfile.seek(0)

        if args.erase_all:
            print('\nDo Erase All' )
            erase_flash(esp, args)

        print('\nwrite_flash main loop' )
        for address, argfile in args.addr_filename:
            if args.no_stub:
                print('Erasing flash...')
            image = pad_to(argfile.read(), 4)
            print('##Completed pad_to')
            if len(image) == 0:
                print('WARNING: File %s is empty' % argfile.name)
                continue
            image = _update_image_flash_params(esp, address, args, image)
            calcmd5 = hashlib.md5(image).hexdigest()
            uncsize = len(image)
            print('calcmd5 = ', calcmd5)
            print('uncsize = ', uncsize)
            
            print('\n###Download file to flash Get ratio & block')
            #print('esp.port = ', esp.port)
            print('esp._port = ', esp._port)
            #esp.connect()
            if args.compress:
                print('compress is True')
                uncimage = image
                image = zlib.compress(uncimage, 9)
                ratio = uncsize / len(image)
                print('esp.FLASH_WRITE_SIZE = ', esp.FLASH_WRITE_SIZE)
                print('esp.IS_STUB = ', esp.IS_STUB)
                print('ratio = ', ratio)
                blocks = esp.flash_defl_begin(uncsize, len(image), address)
            else:
                ratio = 1.0
                print('ratio = ', ratio)
                blocks = esp.flash_begin(uncsize, address)
            print('blocks = ', blocks)
            
            argfile.seek(0)  # in case we need it again
            seq = 0
            written = 0
            t = time.time()
            while len(image) > 0:
                print('\rWriting at 0x%08x... (%d %%)' % (address + seq * esp.FLASH_WRITE_SIZE, 100 * (seq + 1) // blocks), end='')
                sys.stdout.flush()
                block = image[0:esp.FLASH_WRITE_SIZE]
                if args.compress:
                    esp.flash_defl_block(block, seq, timeout=DEFAULT_TIMEOUT * ratio * 2)
                else:
                    # Pad the last block
                    block = block + b'\xff' * (esp.FLASH_WRITE_SIZE - len(block))
                    esp.flash_block(block, seq)
                image = image[esp.FLASH_WRITE_SIZE:]
                seq += 1
                written += len(block)
            t = time.time() - t
            speed_msg = ""
            if args.compress:
                if t > 0.0:
                    speed_msg = " (effective %.1f kbit/s)" % (uncsize / t * 8 / 1000)
                print('\rWrote %d bytes (%d compressed) at 0x%08x in %.1f seconds%s...' % (uncsize, written, address, t, speed_msg))
            else:
                if t > 0.0:
                    speed_msg = " (%.1f kbit/s)" % (written / t * 8 / 1000)
                print('\rWrote %d bytes at 0x%08x in %.1f seconds%s...' % (written, address, t, speed_msg))
            try:
                res = esp.flash_md5sum(address, uncsize)
                if res != calcmd5:
                    print('File  md5: %s' % calcmd5)
                    print('Flash md5: %s' % res)
                    print('MD5 of 0xFF is %s' % (hashlib.md5(b'\xFF' * uncsize).hexdigest()))
                    raise FatalError("MD5 of file does not match data in flash!")
                else:
                    print('Hash of data verified.')
            except NotImplementedInROMError:
                pass

        print('\nLeaving...')

        if esp.IS_STUB:
            # skip sending flash_finish to ROM loader here,
            # as it causes the loader to exit and run user code
            esp.flash_begin(0, 0)
            if args.compress:
                esp.flash_defl_finish(False)
            else:
                esp.flash_finish(False)

        if args.verify:
            print('Verifying just-written flash...')
            print('(This option is deprecated, flash contents are now always read back after flashing.)')
            esptool.verify_flash(esp, args)
        

def pad_to(data, alignment, pad_character=b'\xFF'):
    """ Pad to the next alignment boundary """
    print("\ndef pad_to(data, alignment, pad_character=b'\xFF'):" )
    print('len(data) = ',len(data) )
    pad_mod = len(data) % alignment
    print('pad_mod = ', pad_mod )
    if pad_mod != 0:
        data += pad_character * (alignment - pad_mod)
        print('len(data) = ',len(data) )
    return data


def _update_image_flash_params(esp, address, args, image):
    """ Modify the flash mode & size bytes if this looks like an executable bootloader image  """
    print("\ndef _update_image_flash_params(esp, address, args, image):" )
    if len(image) < 8:
        return image  # not long enough to be a bootloader image

    # unpack the (potential) image header
    magic, _, flash_mode, flash_size_freq = struct.unpack("BBBB", image[:4])
    print('magic={}, flash_mode={}, flash_size_freq={}'.format(
        magic, flash_mode, flash_size_freq ) )
    print('esp.BOOTLOADER_FLASH_OFFSET={}, address={}'.format(
        esp.BOOTLOADER_FLASH_OFFSET, address ) )
    print('esp.ESP_IMAGE_MAGIC = ', esp.ESP_IMAGE_MAGIC )
    
    if address != esp.BOOTLOADER_FLASH_OFFSET or magic != esp.ESP_IMAGE_MAGIC:
        return image  # not flashing a bootloader, so don't modify this

    if args.flash_mode != 'keep':
        flash_mode = {'qio':0, 'qout':1, 'dio':2, 'dout': 3}[args.flash_mode]
        print('flash_mode = ', flash_mode )

    flash_freq = flash_size_freq & 0x0F
    if args.flash_freq != 'keep':
        flash_freq = {'40m':0, '26m':1, '20m':2, '80m': 0xf}[args.flash_freq]
        print('flash_freq = ', flash_freq )

    flash_size = flash_size_freq & 0xF0
    print('flash_size = ', flash_size )
    if args.flash_size != 'keep':
        flash_size = esp.parse_flash_size_arg(args.flash_size)
        print('flash_size = ', flash_size )

    flash_params = struct.pack(b'BB', flash_mode, flash_size + flash_freq)
    if flash_params != image[2:4]:
        print('Flash params set to 0x%04x' % struct.unpack(">H", flash_params))
        image = image[0:2] + flash_params + image[4:]
    return image


class Args(object):

    def __init__( self, device ):
        self.chip = None
        self.port = None
        self.baud = esptool.ESPLoader.ESP_ROM_BAUD
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
        self.flash_mode = 'qio'
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

        #print( 'self.__dict__ =', self.__dict__ )


def main():
    root = tk.Tk()
    root.title('ESP32 SPI FLASH WRITER')
    root.geometry('700x500+0+24')
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    app = App( root )
    app.grid(row=0, column=0, sticky='nsew')

    root.mainloop()



if __name__ == '__main__':
    main()
