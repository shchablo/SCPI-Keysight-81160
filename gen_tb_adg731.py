#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import spidev, time
import RPi.GPIO as io

import PulseGenerator81160A

def volt(ampl, Ag):
   tmp = "-1";   
   ampl = float(ampl)/1000
   count = 0
   while(ampl != float(tmp)):
     if(count == 10):
       return False
     time.sleep(0.1)
     Ag.send(":VOLT1 {}".format(ampl))
     time.sleep(0.1);
     tmp = Ag.send(":VOLT1?")
     count += 1
   return True

def outp(msg, Ag):
   tmp = "-1";   
   count = 0
   while(msg != tmp):
     if(count == 10):
       return False
     time.sleep(0.1)
     Ag.send(":OUTP1 {}".format(msg))
     time.sleep(0.1);
     tmp = Ag.send(":OUTP1?")
     count += 1
   return True


Ag = PulseGenerator81160A.PulseGenerator81160A('11.73.32.4') 
io.setmode(io.BOARD)
SYNC=15; io.setup(SYNC,io.OUT); io.output(SYNC,1)
spi=spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=100000 #<= 100k
spi.mode=2

#spi.xfer2([5])

def send(i):
    io.output(SYNC,0)
    print("xfer {}".format( spi.xfer2([i])) )
    #spi.xfer2([i])
    io.output(SYNC,1)


def dosingle():
    """
    open single mux channel
    """
    #send(128)
    i = input("Enter mux chan or Ctrl-C to exit: ")
    print "MUX channel enabled", i
    send(i)
    
def doscan():
    """
    loop over all mux channels
    """
    #raw_input("Press enter to start or Ctrl-C to exit")
    if( not outp("0", Ag) ): print("Can not turn off output!")
    ampl = input('Press Ctrl-C to exit or enter ampl [mV]: ')
    if( not volt(ampl, Ag) ): print("Can not set ampl!")
    for i in range(32):
        print "MUX channel enabled:", i
    	if( not outp("0", Ag) ): print("Can not turn off output!")
        # disable trigger
        send(i)
    	if( not outp("1", Ag) ): print("Can not turn on output!")
        # enable trigger
        time.sleep(3) # sleep for XX seconds
    


####
if __name__=="__main__":

    #print "Hit Ctrl-C to exit"
    try:
        send(128)
        while True:
            if(len(sys.argv)>1 and sys.argv[1]=="s"):
                dosingle()
            else:
                doscan()

    except KeyboardInterrupt:
        print "\nExiting..."

    finally:
        io.cleanup() # this ensures a clean exit
        
        
"""
while True:
    i = input("Enter mux chan: ")
    print "channel", i
    send(i)
    #raw_input("Press any key")
exit()
"""
"""
raw_input("Press any key")

for i in range(32):
    print "channel", i
    send(i)
    #raw_input("press enter")
    time.sleep(50/10.) #50
"""
