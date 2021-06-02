import sys
import time
import spidev
import RPi.GPIO as io

class ControlLARZIC:
    """
    """
    # ctor
    def __init__(self, bus = 1, dev = 0, iosync_pin = 16, loopback = False):

        # use non-CE GPIO pins for chip select
        self.SYNC = None
        iosync_pin = 0# disable for now
        if( iosync_pin > 1 ):
            ### set board numbering system for GPIO
            io.setmode(io.BOARD)
            
            ### pin number for enable
            self.SYNC = iosync_pin 
            io.setup(self.SYNC, io.OUT)
            io.output(self.SYNC, 1)
        
        
        # spi device
        self.spi = spidev.SpiDev()
        # e.g., open aux bus 1 devices 0 /dev/spidev1.0
        self.spi.open(bus, dev)
        
        self.spi.max_speed_hz = 10000 #<= 100k
        self.loopback = loopback
        # disable injection for all channels
        self.ch_disable_all()
        
    #
    # dtor
    def __del__(self):
        # this ensures a clean exit
        self.__cleanup()

    # ch selector spi.mode = 0b0
    def __ch_spi_write(self, vals):
        self.spi.mode = 0
        rval = self.spi.xfer2( vals )
        if( self.loopback ): print("xfer2 {}".format( rval ))
        
    #
    def ch_enable_all(self):
        self.__ch_spi_write( 8*[0xFF] )
        return

    #
    def ch_disable_all(self):
        self.__ch_spi_write( 8*[0x00] )
        return
    
    #
    # asic ch inj select
    def ch_select(self, ival):
        try:
            i = int(ival)
        except ValueError:
            print( "bad input {}".format( ival ) )
            return -1
        
        # check the range
        if( i < 0 or i > 63 ):
            print( "out of range {}".format( i ) )
            return -1

        regs = 8 * [ 0x00 ]
        reg8 = int(i/8)
        regs[reg8] = 1<<(i-8*reg8)
        
        self.__ch_spi_write( regs )
        return 0
    #
    # clean up
    def __cleanup(self):
        self.ch_disable_all()
        if( self.SYNC ): io.cleanup() 
        self.spi.close()
        return


###
if __name__=="__main__":
    """
    test module
    """
    try:
        asic = ControlLARZIC(bus = 1, dev = 0, loopback = False)
        while True:
            sval = input("Enter chan or '-1' for all  or '-2' for none or Ctrl-C to exit: ")
            sval = int(sval)
            if( sval == -1 ):
                asic.ch_enable_all()
            elif( sval == -2):
                asic.ch_disable_all()
            elif( sval == -3 ) :
                print("do a sweep")
                asic.ch_disable_all()
                for sch in range(64):
                    print("selected", sch)
                    asic.ch_select(sch)
                    time.sleep(1)
                print("done")
            else:
                if( asic.ch_select(sval) == 0 ): 
                    print( "Channel enabled : {}".format(sval) )
                

                        
    except KeyboardInterrupt:
        print( "\nExiting..." )

    #finally:
