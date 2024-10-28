@ECHO off
CD C:\robotcsv
SET str_d=%date: =0%
SET str_t=%time: =0%
SET t_stamp=%str_d:~10,4%_%str_d:~4,2%%str_d:~7,2%_%str_t:~0,2%%str_t:~3,2%
COPY candidates.csv "backup\%t_stamp%_candidates.csv"
COPY results_log.csv "backup\%t_stamp%_results_log.csv"
MOVE input_for_chemspeed.csv "backup\%t_stamp%_input.csv"
MOVE next_exp.csv "backup\%t_stamp%_next_exp.csv"
