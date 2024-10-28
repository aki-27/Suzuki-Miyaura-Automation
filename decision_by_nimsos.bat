cd C:\robotcsv
@echo off
setlocal
for /f "usebackq delims=" %%A in (`dir /b decision_by_nimsos*.exe`) do set exe_name=%%A
@echo on
echo execution of %exe_name%>> log.txt
echo === execute nims-os ==========>>log.txt
%exe_name% >> log.txt
echo.>> log.txt