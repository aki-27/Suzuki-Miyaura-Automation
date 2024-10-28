cd C:\robotcsv
echo --- PDA and Profile transfer ---------->> log.txt

copy Y:\robotcsv\1_result.csv C:\robotcsv\1_result.csv >> log.txt
copy Y:\robotcsv\2_result.csv C:\robotcsv\2_result.csv >> log.txt
copy Y:\robotcsv\3_result.csv C:\robotcsv\3_result.csv >> log.txt
copy Y:\robotcsv\4_result.csv C:\robotcsv\4_result.csv >> log.txt

copy Y:\robotcsv\1_profile.csv C:\robotcsv\1_profile.csv >> log.txt
copy Y:\robotcsv\2_profile.csv C:\robotcsv\2_profile.csv >> log.txt
copy Y:\robotcsv\3_profile.csv C:\robotcsv\3_profile.csv >> log.txt
copy Y:\robotcsv\4_profile.csv C:\robotcsv\4_profile.csv >> log.txt

echo.>> log.txt