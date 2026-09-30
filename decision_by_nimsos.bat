<<<<<<< HEAD
cd C:\robotcsv
@echo off
setlocal
for /f "usebackq delims=" %%A in (`dir /b decision_by_nimsos*.exe`) do set exe_name=%%A
@echo on
echo execution of %exe_name%>> log.txt
echo === execute nims-os ==========>>log.txt
%exe_name% >> log.txt
=======
cd C:\robotcsv
@echo off
setlocal
for /f "usebackq delims=" %%A in (`dir /b decision_by_nimsos*.exe`) do set exe_name=%%A
@echo on
echo execution of %exe_name%>> log.txt
echo === execute nims-os ==========>>log.txt
%exe_name% >> log.txt
>>>>>>> 3d0d2dcbce1cf236e6e2e8f2527c7b914b89b02b
echo.>> log.txt