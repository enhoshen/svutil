# Shell scripting and stuff
## Variables
`export` some variable in a shell script makes it global, so that it can be accessed in sub processes:
```shell
MYVAR="my cool variable"

echo "Without export:"
printenv | grep MYVAR

echo "With export:"
export MYVAR
printenv | grep MYVAR
```
in the above example, MYVAR can be printed out in the case with export.
## Synopsys tools Shell
### variable
How to pass variables to the shell in your script? not `+define+`, not like `VAR=3`,but to export the variable you want. However in the tool shell, you can only access the variables through `get_unix_variable` command.
```shell
PATH=memv/
export PATH
```
```shell
$dc_shell get_unix_variable PATH
$lc_shell get_unix_variable PATH
```
Instead of exporting the variable, you can specify the variable you want to pass on at the start of the command:
```shell
$PATH=memv/ lc_shell -f lib2db.tcl
```

