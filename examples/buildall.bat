rem 64-bit executables
python buildall.py --appdir win64 --ifort --icl 
python buildall.py --appdir win32 --ifort --icl --ia32

pause
