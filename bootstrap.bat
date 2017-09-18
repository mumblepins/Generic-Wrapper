@echo off
REM Generates initial wrapper executable, and then uses that to generate compressed version
REM Shows size difference at end

setlocal
set "GWX_DEL=q"
set "GWX_PROG=D:\Dev\UPX\upx.exe"

set "GWX_R_OPT=lzma=ultra-brute"

rm upx.exe
pyinstaller -F --clean wrapper.py
mv dist/wrapper.exe upx.exe
pyinstaller -F --clean wrapper.py

python get_file_size.py
endlocal