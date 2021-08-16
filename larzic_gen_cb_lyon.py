import sys
import time
import spidev
import argparse

import RPi.GPIO as io

import PulseGenerator81160A

################################################################################

# GPIO pins of Rasberry of Control LARZIC

LARZIC_BUS_ = 1; LARZIC_DEV_ = 0 # e.g., open aux bus 1 devices 0 /dev/spidev1.0 
LARZIC_IOSYNC_PIN_ = 16
LARZIC_SPI_MODE_ = 0

# GPIO pins of Rasberry of injMUX Control Box
NXP_ENABLE_ = 13; NXP_S1_ = 22; NXP_S2_ = 18; NXP_S3_ = 16 
ADG_ENABLE_ = 37; ADG_S1_ = 22; ADG_S2_ = 18; ADG_S3_ = 16 

INJMUX_CH_DEF_ = 1 # 1,2,3,4,5,6,7,8

# Pulser config

PULSE_IP_ = '11.73.32.4'
PULSE_AMPL_DEF_ = 50 # [mV]

# default arguments

SELF_CONFIGURE_DEF_ = 1 # ch per ch 
SELF_PERIOD_DEF_ = 5 # [sec]
################################################################################

class ControlLARZIC:
    """
    """
    # ctor
    def __init__(self, bus = LARZIC_BUS_, dev = LARZIC_DEV_, iosync_pin = LARZIC_IOSYNC_PIN_, loopback = False):

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
        self.spi.mode = LARZIC_SPI_MODE_
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
            _ival = int(ival)
        except ValueError:
            print( "bad input {}".format( ival ) )
            return -1
        
        # check the range
        if( _ival < 0 or _ival > 63 ):
            print( "out of range {}".format( _ival ) )
            return -1

        regs = 8 * [ 0x00 ]
        reg8 = int(_ival/8)
        regs[reg8] = 1<<(_ival-8*reg8)
        
        self.__ch_spi_write( regs )
        return 0

    #
    # asic ch inj select one per group of 8 
    def ch_select_group8(self, ival):
        try:
            _ival = int(ival)
        except ValueError:
            print( "bad input {}".format( ival ) )
            return -1
        
        if( _ival < 0 or _ival > 7 ):
            print( "out of range {}".format( _ival ) )
            return -1

        reg8 = int(_ival/8)
        rtmp = 1<<(_ival-8*reg8)
        regs = 8 * [rtmp]
        #print(f"Ch {_ival} in reg {reg8} -> {rtmp:08b} or 0x{rtmp:X}")
        #print(f"Send : ", *(f"0x{v:02X}" for v in regs))
        self.__ch_spi_write( regs )
        return 0

    #
    # asic ch inj select one per group of 16
    def ch_select_group16(self, ival):
        try:
            _ival = int(ival)
        except ValueError:
            print( "bad input {}".format( ival ) )
            return -1
        
        if( _ival < 0 or _ival > 15 ):
            print( "out of range {}".format( _ival ) )
            return -1

        reg8 = int(_ival/8)
        rtmp = 1<<(_ival-8*reg8)
        regs = 8 * [ 0x00 ]
        for i in range(0, len(regs), 2): regs[i + reg8%2] = rtmp
        #print(f"Ch {_ival} in reg {reg8} -> {rtmp:08b} or 0x{rtmp:X}")
        #print(f"Send : ", *(f"0x{v:02X}" for v in regs))
        self.__ch_spi_write( regs )
        return 0
    
    #
    # clean up
    def __cleanup(self):
        self.ch_disable_all()
        if( self.SYNC ): io.cleanup() 
        self.spi.close()
        return

################################################################################

class InjMuxControl:
    """
      Enable MUX with given Raspberry GPIO pins
    """
    ######
    def __init__( self, nxp_ena = NXP_ENABLE_, adg_ena = ADG_ENABLE_,
                  s1_nxp = NXP_S1_, s2_nxp = NXP_S2_, s3_nxp = NXP_S3_,
                  s1_adg = ADG_S1_, s2_adg = ADG_S2_, s3_adg = ADG_S3_ ):

        ### set board numbering system for GPIO
        io.setmode(io.BOARD)
        self.nxp_ena = nxp_ena # nxp mux pin enable
        self.adg_ena = adg_ena # adg mux pin enable

        # initial state of switches is OFF
        self.swstate = 0
        io.setup(self.nxp_ena, io.OUT, initial = 1)
        io.setup(self.adg_ena, io.OUT, initial = 0)

        self.bits_nxp = (s3_nxp, s2_nxp, s1_nxp)
        for b in self.bits_nxp: io.setup(b, io.OUT, initial = 0)

        self.bits_adg = (s3_adg, s2_adg, s1_adg)
        for b in self.bits_adg: io.setup(b, io.OUT, initial = 0)

       # logic table in order s3, s2, s1
        self.logic = [ (0, 0, 0),  # 1
                       (0, 0, 1),  # 2
                       (0, 1, 0),  # 3
                       (0, 1, 1),  # 4
                       (1, 0, 0),  # 5
                       (1, 0, 1),  # 6
                       (1, 1, 0),  # 7
                       (1, 1, 1) ] # 8
    #####
    def get_nch(self):
        return len(self.logic)
    #####
    def __del__(self):
        self.cleanup()
    #####
    def cleanup(self):
        # all switches are off
        self.disable_switches()
        io.cleanup()
        return
    def disable_switches( self ):
        io.output( self.nxp_ena, 1 ) # high to disable
        io.output( self.adg_ena, 0 ) # low to disable
        self.swstate = 0
        return

    def enable_switches( self ):
        io.output( self.nxp_ena, 0 ) # high to disable
        io.output( self.adg_ena, 1 ) # low to disable
        self.swstate = 1
        return

    def enable_output( self, ch ):
        try:
            ch = int(ch)
            if( ch < 1 or ch > 5) : raise ValueError
            se = self.logic[ch-1]
        except (ValueError, IndexError):
            #print("bad channel input '{}'".format(ch))
            return False

       #print(se)
        self.disable_switches()
        for i in range( len(se) ): io.output( self.bits_nxp[i], se[i] )
        for i in range( len(se) ): io.output( self.bits_adg[i], se[i] )
        self.enable_switches()
        #time.sleep(0.1)
        return True

################################################################################

# terminal color print
class bc:
   HEADER = '\033[95m'
   OKBLUE = '\033[94m'
   OKCYAN = '\033[96m'
   OKGREEN = '\033[92m'
   WARNING = '\033[93m'
   FAIL = '\033[91m'
   ENDC = '\033[0m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   
def print_confopts(conf_opts):
   for k in sorted( conf_opts ):
      print(bc.HEADER+"{} - {}".format(k,conf_opts[k])+bc.ENDC)
   return 0

def confopts_str(conf_opts):
   rstr = ''
   for k in sorted( conf_opts ):
      rstr = rstr + "{} - {};\n".format(k,conf_opts[k])
      rstr.rstrip('\n')
   return rstr

################################################################################

def volt(ampl, Ag):
   tmp = "-1";   
   ampl = float(ampl)/1000
   count = 0
   while(ampl != float(tmp)):
     if(count == 10):
       return False
     #time.sleep(0.1)
     Ag.send(":VOLT2 {}".format(ampl))
     #time.sleep(0.1);
     tmp = Ag.send(":VOLT2?")
     count += 1
   return True

def outp(msg, Ag):
   tmp = "-1";   
   count = 0
   while(msg != tmp):
      if(count == 10):
         return False
      #time.sleep(0.1)
      Ag.send(":OUTP1 {}".format(msg))
      #time.sleep(0.1);
      tmp = Ag.send(":OUTP1?")
      count += 1
   return True

###                                                                          ###
################################################################################
###                                                                          ###

if __name__=="__main__":
   conf_opts = { 0:"enable all",
                 1:"enable channels one by one",
                 2:"enable channels one by one per group of 8",
                 3:"enable channels one by one per group of 16",
                 4:"enable a given channel"}
   
   parser = argparse.ArgumentParser()
   parser.add_argument('-c','--configure',help=confopts_str( conf_opts ),
                       default = SELF_CONFIGURE_DEF_, type = int )
   parser.add_argument('-p','--period',help='period in seconds',
                       default = SELF_PERIOD_DEF_, type = int )
   parser.add_argument('-ch','--chinjmux',help='ch of inj mux',
                       default = INJMUX_CH_DEF_, type = int )
   args  = parser.parse_args()
   tperiod = args.period
   iopt    = args.configure
   chinj   = args.chinjmux
   try:
      sopt = conf_opts[iopt]
   except (KeyError):
      print( bc.FAIL + "'{}' is not a valid configuration option".format( iopt ) + bc.ENDC)
      print_confopts( conf_opts )
      sys.exit(1)

   ##
   print(bc.OKBLUE+"Configuration {} ('{}') and period {} s".format(iopt, conf_opts[iopt], tperiod)+bc.ENDC)

   # mux box
   mux = InjMuxControl() 
   if(mux.enable_output(chinj) == True):
      print(bc.OKBLUE+"MUX channel enabled {}".format(chinj)+bc.ENDC)
   else:
      print(bc.WARNING+"MUX channel can not be enabled"+bc.ENDC)
   
   # 
   print( bc.HEADER+"Initialzing SPI for ASIC control"+bc.ENDC )
   asic = ControlLARZIC(bus = LARZIC_BUS_, dev = LARZIC_DEV_, loopback = False)
   
   # pulse generator
   ip = PULSE_IP_
   print( bc.HEADER+"Connecting to pulse generator at address {}".format(ip)+bc.ENDC)
   Ag = PulseGenerator81160A.PulseGenerator81160A(ip)
   defAmpl = PULSE_AMPL_DEF_ # default amplitude in mV
    
   isStart = True
   try:

      while True:
         if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
         
         if(isStart == True): 
             print(bc.WARNING+"Start/Stop DAQ run before continue"+bc.ENDC)
             isStart = False
         # get amplitude
         ampl = raw_input(bc.UNDERLINE + "Press enter for {} mV or -n [chimney] or input a value in [mV] for pulse amplitude".format(defAmpl)+bc.ENDC+": ")
         try:
            ampl = int(ampl)
         except ValueError:
            #print(bc.WARNING+"bad input value '{}' use default {} mV".format(ampl, defAmpl)+bc.ENDC)
            ampl = defAmpl
            continue

         if(ampl <= 0):
            i = -1*(ampl)
            if( mux.enable_output(i) == True ):
               print(bc.OKBLUE+"MUX channel enabled {}".format(i)+bc.ENDC)
               chinj = i
            else :
    	       print(bc.WARNING+"MUX channel can not be enabled {}".format(i)+bc.ENDC)
            continue
         print(bc.OKBLUE+"{} with amplitude {} mV".format(conf_opts[iopt], ampl)+bc.ENDC)

         if( not volt(ampl, Ag) ):
            print(bc.FAIL+"Cannot set amplitude"+bc.ENDC)
            continue
        
         isStart = True
         ###
         asic.ch_disable_all()
         
         # if/else if for options
         if( iopt == 0 ):
            if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
            asic.ch_enable_all()
            if( not outp("1", Ag) ): print(bc.WARNING+"Cannot turn on output"+bc.ENDC)
            time.sleep(tperiod) # time to take data for this setting

         elif( iopt == 1):
            for sch in range(64):
               print(bc.HEADER+"selected {}:{}".format(chinj, sch)+bc.ENDC)
    	       if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
               asic.ch_select(sch)
    	       if( not outp("1", Ag) ): print(bc.WARNING+"Cannot turn on output"+bc.ENDC)
               time.sleep(tperiod) # time to take data for this setting
               
            # finished loop over channels
            time.sleep(tperiod/2) # sleep some more to avoid missing data from last setting
            if( not outp("0", Ag) ): print("Cannot turn off output")
            asic.ch_disable_all()
            #print(bc.OKGREEN+"done"+bc.ENDC)

         elif( iopt == 2 ):
            for sch in range(8):
               print(bc.HEADER+"selected {}:{}".format(chinj, sch)+bc.ENDC)
               if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
               asic.ch_select_group8(sch)
    	       if( not outp("1", Ag) ): print(bc.WARNING+"Cannot turn on output"+bc.ENDC)
               time.sleep(tperiod) # time to take data for this setting
               
            # finished loop over channels
            time.sleep(tperiod/2) # sleep some more to avoid missing data from last setting
            if( not outp("0", Ag) ): print("Cannot turn off output")
            asic.ch_disable_all()
            #print(bc.OKGREEN+"done"+bc.ENDC)

         elif( iopt == 3 ):
            for sch in range(16):
               print(bc.HEADER+"selected {}:{}".format(chinj, sch)+bc.ENDC)
    	       if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
               asic.ch_select_group16(sch)
    	       if( not outp("1", Ag) ): print(bc.WARNING+"Cannot turn on output"+bc.ENDC)
               time.sleep(tperiod) # time to take data for this setting
               
            # finished loop over channels
            time.sleep(tperiod/2) # sleep some more to avoid missing data from last setting
            if( not outp("0", Ag) ): print("Cannot turn off output")
            asic.ch_disable_all()
            #print(bc.OKGREEN+"done"+bc.ENDC)

         elif( iopt == 4):
            sval = raw_input(bc.UNDERLINE + "Enter channel to enable channel"+bc.ENDC+": ")
            try:
               sval  = int(sval)
            except (ValueError):
               print( bc.FAIL + "'{}' is not a valid channel number".format( sval ) + bc.ENDC)
               continue
            if( not outp("0", Ag) ): print(bc.WARNING+"Cannot turn off output"+bc.ENDC)
            if( not asic.ch_select(sval) ):
               print( bc.FAIL + "Could not enable channel : {}".format(sval) + bc.ENDC )
               continue

            if( not outp("1", Ag) ): print(bc.WARNING+"Cannot turn on output"+bc.ENDC)
            time.sleep( tperiod )
            if( not outp("0", Ag) ): print("Cannot turn off output")
            asic.ch_disable_all()

         print(bc.OKGREEN+"done"+bc.ENDC+"\n")
         
   except KeyboardInterrupt:
      print("\nExiting...")
        
   finally:
      Ag.send("*RCL 1")
