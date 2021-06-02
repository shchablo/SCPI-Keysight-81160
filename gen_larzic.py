import sys
import time
import spidev
import RPi.GPIO as io

from larzic import ControlLARZIC
import PulseGenerator81160A

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
ip = '11.73.32.4'
Ag = PulseGenerator81160A.PulseGenerator81160A(ip) 

if __name__=="__main__":

    defAmpl = 50
    #print "Hit Ctrl-C to exit"
    try:
        asic = ControlLARZIC(bus = 1, dev = 0, loopback = False)
        sval = input("Conf: ip:{} Enter chan or '-1' for all  or '-2' for none or -3 for sweep or Ctrl-C to exit: ".format(ip))
        sval = int(sval)
        while True:
            if( not outp("0", Ag) ): print("Can not turn off output!")
            ampl = defAmpl
            userInput = raw_input('Press Ctrl-C to exit or [-1,-2,-3] or enter ({} mV) or input ampl [mV]: '.format(defAmpl))
            try:
                ampl = int(userInput)
            except ValueError:
                ampl = defAmpl;
                print("Do {} with ampl {} mV".format(sval, ampl))
            if(ampl < 0):
                sval = ampl
                userInput = raw_input('Press Ctrl-C or enter ({} mV) or input ampl [mV]: '.format(defAmpl));
                try:
                    ampl = int(userInput)
                except ValueError:
                    ampl = defAmpl;
            defAmpl = ampl;
            print("Do {} with ampl {} mV".format(sval, ampl))
            if( not volt(ampl, Ag) ): print("Can not set ampl!")
            if( sval == -1 ):
                asic.ch_enable_all()
    	        if( not outp("1", Ag) ): print("Can not turn on output!")
            elif( sval == -2):
                asic.ch_disable_all()
    	        if( not outp("1", Ag) ): print("Can not turn on output!")
            elif( sval == -3 ) :
                asic.ch_disable_all()
                for sch in range(64):
                    print("selected", sch)
    	            if( not outp("0", Ag) ): print("Can not turn off output!")
                    asic.ch_select(sch)
    	            if( not outp("1", Ag) ): print("Can not turn on output!")
                    time.sleep(1)
                print("done")
            else:
    	        if( not outp("1", Ag) ): print("Can not turn on output!")
                if( asic.ch_select(sval) == 0 ): 
                    print( "Channel enabled : {}".format(sval) )

    except KeyboardInterrupt:
        print "\nExiting..."

    finally:
        Ag.send("*RCL 1")
        io.cleanup() # this ensures a clean exit
