SET makensis="C:\Program Files (x86)\NSIS\makensis.exe"
SET python="c:\Python27\python.exe"

%python% setup.py py2exe
%makensis% install.nsi
