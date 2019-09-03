#!/bin/sh
HOME=/home/enhoshen/research/lpAccel/
SYN=$HOME/syn/
SIM=$HOME/sim/
SRC=$HOME/src/
design_param_re="([^_]+)"
design_params=
if [[ $1 =~ $design_param_re ]]; then
    design_params=${BASH_REMATCH}
fi
echo ${design_params}
echo $BASH_REMATCH
