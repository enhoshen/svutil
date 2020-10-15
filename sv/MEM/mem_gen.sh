#!/bin/sh
CELL_LIB_PATH=/opt/CAD/cell_lib/
LS=(   $(ls ${CELL_LIB_PATH} ) )
MEM_PATH=/
function memtype()
{
 
 for i in "${!LS[@]}" 
 do
    echo ${i} ${LS[i]}
 done
 echo "choose cell library"
 read IN
# MEM_PATH=${CELL_LIB_PATH}${LS[${IN}]}/CIC/Memory/
 MEM_PATH=${CELL_LIB_PATH}${LS[${IN}]}/orig_lib/aci/
}
function sourceMem()
{
 MEM_TYPE=( $( ls ${MEM_PATH}) )
 for i in "${!MEM_TYPE[@]}" 
 do
    echo ${i} ${MEM_TYPE[i]}
 done
 echo "choose memory type"
 read IN
 MEM_PATH=${MEM_PATH}${MEM_TYPE[IN]}/bin/${MEM_TYPE[IN]}
}

OUTPUT="$(ls -1)"

memtype 
echo ${MEM_PATH}

sourceMem
echo ${MEM_PATH}
$MEM_PATH&

#if [ $1 == "ls" ]; then
#   ls /opt/CAD/cell_lib/CBDK_TSMC90GUTM_Arm_f1.0/CIC/Memory/
#else 
#   /opt/CAD/cell_lib/CBDK_TSMC90GUTM_Arm_f1.0/CIC/Memory/$1/bin/$1 &
#fi
