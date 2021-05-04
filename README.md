# SCPI-Keysight-81160

This script made to control Pulse Function Arbitrary Noise Generator 81160A.

## Requirements 

<ol>
<li>pyVISA: https://pyvisa.readthedocs.io/en/latest//li>
<li>argparse: https://docs.python.org/3/howto/argparse.html</li>
<li>sys: https://docs.python.org/3/library/sys.html</li>
<li>time: https://docs.python.org/3/library/time.html</li>
</ol> 

## Installation pyVISA with conda

```console
conda config --add channels conda-forge
conda install pyvisa
```
You can find check out conda-forge via link: https://github.com/conda-forge/pyvisa-feedstock

## Examples

```console
python gen.py -cmd ':VOLT1 1.2 :VOLT1? :VOLT1 0.05 :VOLT1? :MMEM:LOAD:STAT 1,”TEST_0012”'
```

```console
python gen.py -ex
```
Inside exp function you can find way how to use code for integration to any python script. 
