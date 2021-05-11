#!/usr/bin/python2
# from utiles import *
import PulseGenerator81160A
import time

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

Ag = PulseGenerator81160A.PulseGenerator81160A('11.73.32.4')
time.sleep(8)

#outp("1", Ag)
volt(53, Ag)
