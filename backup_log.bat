@ECHO off
CD C:\robotcsv
SET str_d=%date: =0%
SET str_t=%time: =0%
SET t_stamp=%str_d:~10,4%_%str_d:~4,2%%str_d:~7,2%_%str_t:~0,2%%str_t:~3,2%
COPY log.txt "backup\%t_stamp%_log.txt"
