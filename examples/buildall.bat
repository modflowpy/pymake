rem 64-bit executables
python buildall.py --appdir win64 --ifort --icl --zip win64.zip
python buildall.py --appdir win32 --ifort --icl --ia32 --zip win32.zip

pause
