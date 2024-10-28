cd C:\robotcsv
@echo off
setlocal
for /f "usebackq delims=" %%A in (`dir /b evaluate_objective*.exe`) do set exe_name=%%A
@echo on
echo execution of %exe_name%>> log.txt
echo --- evaluate integral and objective ---------->> log.txt
%exe_name% >> log.txt
echo.>> log.txt
