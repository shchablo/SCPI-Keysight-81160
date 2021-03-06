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

Inside exp function you can find method how to use code for integration to any python script. 

```console
python gen.py -ex
```

```console
python gen.py -info
```

```console
python -cmd :MEM:STAT:NAME? 1
```

```console
python -cmd *RCL 1
```

```console
python -cmd :VOLT1? :VOLT1 1.33
```

```console
python gen.py -cmd :VOLT1? :VOLT1 1.33 :VOLT1? :MEM:STAT:NAME? 1 *RCL 1 :VOLT1?
```

## Links 

https://github.com/ebecheto/testbench
