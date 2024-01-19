# Simulation utilities

SVutil simulation utilites works mainly on several environment variables so it doesn't messed with nicotb Makefiles:

[//]: <> (* --SV variable define the simulated .sv source file path)

* Nicotb set variables
  * `TEST` sets the testbench module `EX`: AhbWrap_tb
    * +define TEST macro for the tool.
  * `TESTMODULE` sets the tested module name `EX`: Ahb3ToReqAckWrap
* SVutil set variables
  * `INC` sets the include file name `EX`:Ahb_include
  * `TOPSV` set the top/testbench module file `EX`:../Ahb_tb.sv
  * `GATE_LEVEL` post-sim simulation mode, define the gate level design and +define+ GATE_LEVEL macro for the tool.
  * `SIM` pre-sim simulation mode.
  * `HCLK/HCYCLE` define the half-clock cycle time in ns.

Folder hierarchy is strict, run SVgen,SVparse under `sim/`
to avoid unexpected problems. When working under `sim/vcs` or such, specify `TOPSV`
for NicoUtil to work properly.

```
include/
src/
sim/
   ->working directory
   vcs/
```

## Setup

```
git clone https://github.com/enhoshen/SVutil
export SVutil=<SVutil project path>
```

Please export `SVutil` enviroment variable for your SVutil repo base
folder.

## SVparse

SVparse see verilog module, file, package as **hier**, as they are ones that contain `typedef`, `logic`, `port` and `parameter`. And they are ones that need constant review and reference while writing verilog codes.  
This module parse the mentioned **hier** into a tree-like structure, so visible parameters and types from the a hier's vertical relations with its parent hiers could be directly accessed and easily examined in the provided helper functions.

### Interactive python shell usage

Simply type `python -i SVparse.py includefilepath` in the console. The included files then parsed into the class SVparse for further usages.

## EAdict

stands for easy access dictionary, SVparse initializes one for
SVparse.hiers and can be accessed by `hiers`

* hiers.hier_name.ShowTypes
* hiers.hier_name.ShowParams
* hiers.hier_name.ShowPorts
* hiers.hier_name.ShowConnect
  All of the parsed hierarchies are stored in `SVparse.hiers` dictionary, I provide a instance `hiers` for easier access to the hiers inside the dictionary.  
  The Above commands essentially was of `SVparse.hiers['hier_name'].ShowTypes` form.

  ```shell
  $python -i SVparse.py PE_compile.sv
  >>> hiers.PE
  
  -------------------------PE-------------------------
      params     :['IDLE', 'WRITE', 'READ', 'DONE']
       scope     :'PE.sv'
       types     :[]
       child     :[]
       ports     :['i i_PEconf', 'i i_PEinst', 'i i_Input', 'i i_Weight', 'o o_Psum']
  
  >>> hiers.PE.ShowConnect
  Error: Can't open display: (null)
  .*,
  `rdyack_connect(Input,),
  `rdyack_connect(Weight,),
  `rdyack_connect(Psum,),
  .i_PEconf(),
  .i_PEinst(),
  .i_Input(),
  .i_Weight(),
  .o_Psum()
  >>>
  ```
  
  If the X server display variable is properly set, ShowConnect attribute also copy it to the clipboard, works on MobaXterm, but not ConEmu sadly ( I can't figure out how to set X forwarding for ConEmu).

### SVhier class and its structure

`TODO`

* `name`
* `params`
  * accessed by `ShowParams`
  * traced all the way to its related parents
* `types`
  * accessed by `ShowTypes`
  * traced all the way to its related parents
* `child` is a dictionary of the children
* `_scope` is the parent hierarchy
* ports
  * `paramports` for module parameter ports
  * `ports` for module ports
  * `protoPorts` is used for text macro simple protocols 
  * accessed by `ShowPorts` `ShowConnect`
* `imported` marks if a file or module imported any packages or parameters

### helper functions

* show_paths()
* ShowFiles(file_index [,start_line[, end_line]] )
* reset()
  * reset SVparse class
* file_parse(paths=[(True,INC)])
  * parse a list of path enclosed in a tuple (bool,path)
  * the bool marks if the path is under `include/`
  
### Class Structure

`TODO`

#### hiers

#### String

### to_clip

`to_clip` global function makes use of package `xclip`, by specifying
environment variable `XCLIP` pointing to `xclip` binary executable, so
you can benefit from string to clipboard convenience.

---

## NicoUtil

is built upon SVparse, so make sure `$SVutil` is set for package import

### StructBus

`TODO`

### Protocol Wrapper

`TODO`

### ProtoBus

ProtoBus wraps similar protocol class in `Nicotb.protocols`, including argument parser for easier protocol bus initialization, easier data/control generator with master and slave selections.

### Methods


---

## SVgen

SVgen class provide several building blocks for systemverilog related
files, it generally works on env `$TESTMODULE`, `$INC`, `$TEST`  
`usage`: TESTMODULE=Module INC=Module_include TEST=Apb_tb TOPMODULE=Apb_tb python -i SVgen.py

The Files you need to prepare:

```
include/test_include.sv
```

After parsing the include file of related modules, packages etc, the
Library can generates single module testbench for you, connecting
ports, declaring parameters, creating buses for Nicotb and so on in py and sv files.

### Structure

SVgen building blocks are **generators** generating strings accessed by
next() built-in function. Users can choose desirable block and
combine them into a file description list:  
`EX`: genlist([ (A,B) , A , (C,) , [1, D , E], (2, F, G), A])
generates a file structure of such

```
A
B
A'
C
  D
    E
    E'
  D'
    F
    G
A''
```

* naked block structure generates a string once
* tuple initializes and generates once of its contents
* nested list will initialize, generates strings and expands its
content in a hierarchical structure
* integer will add up to the current indent level

### Building Block

Why generators? Code often comes with building blocks, each `next()`
call produces a part of the blocks, enable easy combinations bewteen
blocks

```
yield -> A  always_comb begin
yield -> B    logic a;
              logic b;
yield -> C      //comment
                //comment
yield -> B'   logic c;
yield -> A' end
```

* Building blocks needs one initialization section at the start
so the blocks has a base indentation

```python
ind = self.cur_ind.copy()
yield ''
```

* remember to add indetation using `ind.b`,`ind[n]` using format
string in the building block

#### building block example

the following blocks generates a connected module instance for you

```python
    def InsGen(self , module , name='dut' ,  **conf):
        ind = self.cur_ind.copy()
        yield ''
        s = '\n'
        s += ind.base + module.hier + ' #(\n'
        s_param = ''
        for param in module.paramports.keys():
            s_param += f'{ind[1]},.{param}({param})\n'
        s_param = s_param.replace(f'{ind[1]},' , ind[1]+' ', 1)
        sb = f'{ind.b}) {name} (\n'
        s_port =''
        for io , n , dim , *_ in module.ports:
            s_port += ind[1] + ',.' + n + (  (f'({n})\n') if dim ==() else (f'({{ >>{{{n}}} }})\n'))
        s_port = s_port.replace(f'{ind[1]},' , ind[1]+' ' , 1)
        s += s_param + sb + s_port + ind.base + ');\n'
        yield s
```

### Indentation class: `Ind`

The building block generators makes indentation generation easier.
`Ind` class object returns multiples of 4 spaces for indentation.

* IndObj.b returns the base indentation of the Ind object as a string
* IndObj[n] adds n indentation to the base indentation and returns
a string of such number of spaces

### Module Test structure

Module test generates `*_tb.sv` and `\*_tb.py` files for single
module easy testbench generation. After genration the files can be
freely modified  

### tb.sv, tb.py file generation

``` python
g = SVgen()
g.SVWrite(g.ModuleTestSV(g.dut))
g.PYWrite(g.ModuleTestPY(g.dut))
```

### SVgen Methods

`TODO`

### SVgen structure

* `dut` is the targeted `$TESTMODULE` SVhier object
* `testname`
* `test`
* `incfile`
* `fsdbname`
* `cond` is the configuration for this test, used to be appended at
fsdb files or synthesized files.# SVutil

 SystemVerilog helper libraries, scripts, tips..

## Setup

    git clone https://github.com/enhoshen/SVutil
    export SVutil=<SVutil project path>
