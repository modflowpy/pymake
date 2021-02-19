rem 64-bit executables
python buildall.py --appdir win64 -fc ifort -cc icl --zip win64.zip --keep
python buildall.py --appdir win32 -fc ifort -cc icl --arch ia32 --zip win32.zip --keep

pause
