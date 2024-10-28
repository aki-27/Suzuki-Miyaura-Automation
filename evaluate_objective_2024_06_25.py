import datetime as dt
from math import log

def integration_csv( file_name ):

    def pos_wl( wl ):
        return int( (wl - str_wl) / wl_intval )

    def pos_t( t ):
        return int( (t - str_time) * 60.0 * 1000.0 / t_intval )

    # Trapezoidal rule
    def integration( a, b ):
        pt_a = pos_t(a)
        pt_b = pos_t(b)
        height = sum( dat_nm[pt_a+1:pt_b-1] ) + (dat_nm[pt_a] + dat_nm[pt_b]) / 2.0
        return height * t_intval

    # 1st order integration correction for baseline
    def cor_integration( a, b ):
        a_around = dat_nm[pos_t(a-bl_ave):pos_t(a)]
        b_around = dat_nm[pos_t(b):pos_t(b+bl_ave) ]
        pt_a = sum( a_around ) / len( a_around )
        pt_b = sum( b_around ) / len( b_around )
        return integration( a, b ) - 0.5 * (pt_a + pt_b) * (b - a)
    
    params = []
    with open( 'param.txt', 'r' ) as f:
        lines = [ x.strip('\n').split(',')[1] for x in f.readlines() ]
        std_mw =  float( lines[0] )
        sub_mw =  float( lines[1] )
        wv_len =  int( lines[2] )
        std_ini = float( lines[3] )
        std_fin = float( lines[4] )
        p1_ini =  float( lines[5] )
        p1_fin =  float( lines[6] )
        p1_slp =  float( lines[7] )
        p2_ini =  float( lines[8] )
        p2_fin =  float( lines[9] )
        p2_slp =  float( lines[10] )
        p3_ini =  float( lines[11] )
        p3_fin =  float( lines[12] )
        p3_slp =  float( lines[13] )
        std_wt =  float( lines[14] )
        sub_wt =  float( lines[15] )
        bl_ave =  float( lines[16] )
        low_ps =  float( lines[17] )
        upr_ps =  float( lines[18] )

    with open( file_name, 'r' ) as f:
        lines = [ x.strip('\n').split('\t') for x in f.readlines() ]
        data_type = lines[0][1]
        t_intval  = int( lines[1][1].split('msec')[0] )
        wl_intval = float( lines[2][1].split('nm')[0] )
        str_time  = float( lines[3][1].split('min')[0] )
        end_time  = float( lines[4][1].split('min')[0] )
        str_wl    = float( lines[5][1].split('nm')[0] )
        end_wl    = float( lines[6][1].split('nm')[0] )
        time_np   = int( lines[7][1] )
        wl_np     = int( lines[8][1] )
        new_pda   = lines[9][1]
        int_unit  = lines[10][1]

    dat_nm = [ int( x[pos_wl(wv_len)] ) for x in lines[12:] if x!='' ]
    
    std_mol = std_wt / std_mw
    sub_mol = sub_wt / sub_mw
    
    std_ar = cor_integration(std_ini, std_fin )
    p1_ar = cor_integration( p1_ini, p1_fin )
    p2_ar = cor_integration( p2_ini, p2_fin )
    p3_ar = cor_integration( p3_ini, p3_fin )
    
    p1_yield = p1_ar / std_ar * p1_slp * std_mol / sub_mol
    p2_yield = p2_ar / std_ar * p2_slp * std_mol / sub_mol
    p3_yield = p3_ar / std_ar * p3_slp * std_mol / sub_mol

    return std_ar, p1_ar, p2_ar, p3_ar, p1_yield, p2_yield, p3_yield, low_ps, upr_ps

def error_text_pressure( file_name, lower_limit, upper_limit ):
    with open( file_name, 'r' ) as f:
        dat = [ x.strip('\n').split(',') for x in f.readlines()[1:] ]
    pressure = [ float( y ) for y in [ x[3] for x in dat ] ]

    if [ x for x in pressure if x < lower_limit ] != []:
        lower_error = 'lower pressure: {:.2f}'.format( min( pressure ) ) + ' MPa, '
    else:
        lower_error = ''
    
    if [ x for x in pressure if x > upper_limit ] != []:
        upper_error = 'upper pressure: {:.2f}'.format( max( pressure ) ) + ' MPa, '
    else:
        upper_error = ''
    
    if lower_error == '' and upper_error == '':
        return ''
    else:
        return lower_error + upper_error


def read_next_exp_no( b_size ):
    with open( './next_exp.csv', 'r' ) as f:
        next_exp = f.readline().strip( '\n' ).split(',')
        i = 0
        ls_exp_no = []
        while i < b_size:
            ls_exp_no.append( int( next_exp[i] ) )
            i += 1

    return ls_exp_no

def write_objective( file_name, exp_no, obj ):
    with open( file_name, 'r' ) as f:
        strs = f.readlines()
    
    # error detection of writing
    expt_val = strs[ exp_no ].split(',')[-1]
    if expt_val != '\n':
        raise Exception( '***ERROR*** selected experiment maybe was been done.', str( expt_val ) )
    
    # strs[0] is heaer, so experimental num directly corresponds to row number
    strs[ exp_no ] = strs[ exp_no ].strip( '\n' ) + str( obj ) + '\n'
    
    with open( file_name, 'w' ) as f:
        for x in strs:
            f.write( x )
    
    return

BATCH_SIZE = 4

with open( 'exp_table.csv', 'r' ) as f:
    strs = [ x.strip('\n').split(',') for x in f.readlines()[1:] ]
    exp_ligand_no = [ x[1] for x in strs ]
    exp_base_no   = [ x[2] for x in strs ]
    exp_solvent_no= [ x[3] for x in strs ]
    exp_notations = [ x[4] for x in strs ]

ls_exp_no = read_next_exp_no( 4 )
print( 'executed exp', ls_exp_no )

i = 0
while i < BATCH_SIZE:
    std_ar, p1_ar, p2_ar, p3_ar, p1_yield, p2_yield, p3_yield, low_ps, upr_ps = integration_csv( str(i+1) + '_result.csv' )
    objective = p2_yield - p3_yield

    error_text = error_text_pressure( str(i+1) + '_profile.csv', low_ps, upr_ps )
    
    if std_ar < 0:
        error_text += 'negative area of STD, '
    
    if -0.05 <= p1_yield < 0.0:
        p1_yield = 0.0001
    elif p1_yield < -0.05:
        error_text += 'negative {: 4.2f} p1 yield, '.format( p1_yield )
        p1_yield = 0.0
    elif p1_yield > 1.20:
        error_text += 'too large {: 4.2f} p1 yield, '.format( p1_yield )
    
    if -0.05 <= p2_yield < 0.0:
        p2_yield = 0.0001
    elif p2_yield < -0.05:
        error_text += 'negative {: 4.2f} p2 yield, '.format( p2_yield )
        p2_yield = 0.0
    elif p2_yield > 1.20:
        error_text += 'too large {: 4.2f} p2 yield, '.format( p2_yield )
    
    if -0.05 <= p3_yield < 0.0:
        p3_yield = 0.0001
    elif p3_yield < -0.05:
        error_text += 'negative {: 4.2f} p3 yield, '.format( p3_yield )
    elif p3_yield > 1.20:
        error_text += 'too large {: 4.2f} p3 yield, '.format( p3_yield )

    total_yield = p1_yield + p2_yield + p3_yield
    if total_yield > 1.20:
        error_text += 'too large {: 4.2f} total yield, '.format( total_yield )

    if error_text == '':
        error_text = 'normal termination'

    # definition of objective function
    if p2_yield > 0:
        objective = log( p2_yield )

    exp_ID = ls_exp_no[i]
    with open( 'results_log.csv', 'a' ) as f:
        text = str( dt.datetime.now() ) + ', ' + str(i+1) + ', ' + str( exp_ID ) + ', ' + exp_ligand_no[exp_ID-1] + ', ' + exp_base_no[exp_ID-1] + ', ' + exp_solvent_no[exp_ID-1] + ', ' + str( exp_notations[exp_ID-1] )
        f.write( text + ', {:.6f}, {:.6f}, {:.6f}, {:.6f}, {:.6f}, {:f}, {:f}, {:f}, {:f},'.format( p1_yield, p2_yield, p3_yield, total_yield, objective, std_ar, p1_ar, p2_ar, p3_ar) + str( error_text ) + '\n' )

    if error_text == 'normal termination':
        print( str(i+1) + ', ID {:5.0f}, '.format(exp_ID) + str( exp_notations[exp_ID-1] ).rjust( 26 ) + ',    yield p1 {: 7.2f} , p2 {: 7.2f} , p3 {: 7.2f} , total {:7.2f} , obj {:7.6f}'.format( p1_yield*100.0, p2_yield*100.0, p3_yield*100.0, total_yield*100.0, objective ) )
        write_objective( 'candidates.csv', exp_ID, objective )
    else:
        print( str(i+1) + ', ID {:5.0f}, '.format(exp_ID) + str( exp_notations[exp_ID-1] ).rjust( 26 ) + ',    ERROR!: ' + error_text )
    i += 1
