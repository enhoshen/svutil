# Memory scripts
## db_gen.sh
Call the lc_shell and Convert the desired .lib to .db file for the memory module. The script read the `.lib` file under `memlib/` and write `.db` file to `memdb/`, note that my `.synopsys_setup` read .db file from `memdb/` directory so that's where I would output my db files.  
usage:  ```sh db_gen.sh MODULE```
```
$sh db_gen.sh RF_2P_64x16
```
## mem_gen.sh
Open up the chosen memory generator GUI under `CELL_LIB_PATH`, but actually only 90nm library would work I suppose.  
usage: ```sh mem_gen.sh```
## includgen.sh under memv
Take advantage of 541's `include_gen.py` script, run includegen.sh to create a include file containing all of the `.v` memory files under `memv/` directory.
```shell
$sh includegen.sh
```
## Memory Generator
`TODO`

