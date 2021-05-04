import pyvisa as visa
import argparse
import sys
import time

def info():
  print("Commands to read states:")
  print("  VOLT[1,2]? EX: VOLT1?") 
  print("  AM[1,2]:INT:FUNC? EX:  AM1:INT:FUNC?") 
  print("  MEM:STAT:NAME? [1,2,...,N] EX:  MEM:STAT:NAME? 1") 
  
  print("Commands to write states:")
  print("  VOLT[1,2] [value] EX: VOLT1 1.2") 
  print("  AM[1,2]:INT:FUNC [SIN, SQU, RAMP, NRAM, TRI, NOIS, USER] EX: AM2:INT:FUNC SIN") 
  print('  MMEM:LOAD:STAT [1,2,3,4], "NAME" EX: MMEM:LOAD:STAT 1, "bOISE__"')

def intro(ip_address, inst):
  print('################################################################################\n') 
  print('Connected to TCPIP0::' + ip_address + '::inst0::INSTR') 
  print('The session: ' + str(inst.session)) 
  idn = inst.query('*IDN?')
  print('IDN: ' + idn)
  print("TimeOut: " + str(inst.timeout) + ' ms')
  print('################################################################################') 

def merge_cmds(commands):
  isLoop = True;
  while(isLoop):
    isLoop = False;
    for idx, cmd in enumerate(commands):
        if(not(commands[idx].startswith(':')) and idx != 0):
          commands[idx - 1] = (str(commands[idx - 1]) + ' ' + str(commands[idx]))
          commands[idx] = ''
          isLoop = True;
    commands = [x for x in commands if len(x.strip()) > 0]
  return commands

def exp(ip_address, result):
  
  try:
    
    rm = visa.ResourceManager('@py')
    inst = rm.open_resource('TCPIP0::' + ip_address + '::inst0::INSTR')
    
    # ---
    
    cmd = 'VOLT2 1.2'
    inst.write(cmd)
    result.append([cmd, ' '])
    # or
    cmd = 'VOLT2?'
    msg = inst.query(cmd)
    result.append([cmd, msg])
     
    # ---
    
    inst.close()
    rm.close()

  except visa.Error as ex:
    print('An error occurred: %s' % ex)
  return result

def main(ip_address, timeout, delay, commands, introduction, information, example):

  result = []
  
  # --- Features
  if(example):
    exp(ip_address, result)
    print(result)
    return result 
  # --- 
  
  try:
    
    rm = visa.ResourceManager('@py')
    inst = rm.open_resource('TCPIP0::' + ip_address + '::inst0::INSTR')
    inst.timeout = timeout
  
    commands = merge_cmds(commands)
    print(commands)  
    for idx, cmd in enumerate(commands): 
        if(cmd.find('?') != -1):
          msg = inst.query(cmd)
          result.append([cmd, msg])
          time.sleep((delay)/1000)
        else:
          inst.write(cmd)
          result.append([cmd, ' '])
          time.sleep((delay)/1000)
    
    # --- Features
    if(introduction):
      intro(ip_address, inst)
    
    if(information):
      info()
    # --- 
    
    inst.close()
    rm.close()
  
  except visa.Error as ex:
    print('An error occurred: %s' % ex)
    print('Done.')

  print(result)
  return result

parser = argparse.ArgumentParser();
parser = argparse.ArgumentParser(description='This is the script to read/write the generator (81160A Keysight / Agilent) by a SCPI protocol.')
parser.add_argument("-ip", "--ip_address", type=str, default="11.73.32.4", required=False, help='<xxx.xxx.xxx.xxx>: If ignore this arg - The default IP will be set.')
parser.add_argument("-cmd", "--commands", default=[], nargs='+', required=False, help='<:cmd0 :cmd1 :cmdN> This argument can be used for read/write SCPI commands. Any Command must start with \':\'. EX: -cmd :VOLT1? :VOLT1 1.2 :VOLT1?')
parser.add_argument("-t", "--timeout", type=int, default=1000, required=False, help='<int> ms. This argument can be used for set timeout for cmds.')
parser.add_argument("-d", "--delay", type=int, default=100, required=False,help='<int> ms. This argument can be used for set delay for cmds.')
parser.add_argument("-exp", "--example", default=False, action = argparse.BooleanOptionalAction, help='Example of code for control pulser.')
parser.add_argument("-intro", "--introduction", default=False, action = argparse.BooleanOptionalAction, help='This argument used to dump general info about the instrument.')
parser.add_argument("-info", "--information", default=False, action = argparse.BooleanOptionalAction, help='This argument used to list SCPI commands.')

args = parser.parse_args(sys.argv[1:])

main(**vars(args)) 
