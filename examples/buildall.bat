rem 64-bit executables
python make_mf2005.py --appdir win64 --ifort --icl --double
python make_mfnwt.py --appdir win64 --ifort --icl --double
python make_mfusg.py --appdir win64 --ifort --icl --double
python make_mflgr.py --appdir win64 --ifort --icl --double
python buildall.py --appdir win64 --ifort --icl

rem 32-bit executables
python make_mf2005.py --appdir win32 --ifort --icl --double
python make_mfnwt.py --appdir win32 --ifort --icl --double
python make_mfusg.py --appdir win32 --ifort --icl --double
python make_mflgr.py --appdir win32 --ifort --icl --double
python buildall.py --appdir win32 --ifort --icl --ia32

pause
