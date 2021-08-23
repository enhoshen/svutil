# Notes for Programming in this projects and stuffs
## Vim
### Johnjohnlin's port connect command for vim
Under johnjohnlin's `.vim` folder, copy `ftplugin/` ( short for file type plugin) and `autoload/` to your own `.vim/`.
* IO to ports: select IO lists and type `_P`, that is `-p` while holding shift
* Connect ports: select ports lists and type `_C`
### Tab navigation
change tab:
* `ctrl`+`pgup/pgdn` 
* number +`g`+`t`
### Copy, paste, cut, delete 
* `yy` to copy a line
* `p` to paste a line in the next line from the current cursor
* **`dd`** beside delete current line, it actually **cut the current line to clipboard**!
* Add number before the shortcut to specify number of lines to perform the action ex: `3`+`dd` to cut 3 lines from the current cursor
### Shortcut: `A` `$`
* Jump to the end of the line, `A` would enter insert mode afterward
## Python
### Flexible function arguments
Besides `*args` and `**kwargs`, additional positional and keyword arguments are all allowed, but watch out for their order
* All positional argument and expression `*args` should be before any keyword arguments and `**kwargs`
* Additional positional arguments should be before `*args`, likewise additional keyword arguments should be before `**kwargs`
```python
def func(a,b,c,*args,d,e,*kwargs):
  #....
func(1,2,3,4,5,6,d=7,f=9,e=8)
# a=1,b=2,c=3,args=[4,5,6],kwargs={f:9}
```
### **Interactive Shell after executing a script**
Use `-i` argument **before** the script to enter interactive shell after executing the file!  
```shell
$python -i file.py
```
## Environment
### Grep
Basic uses:
* ```$grep 'pattern' * -r```: search for pattern string in every files recursively under current working directory.
