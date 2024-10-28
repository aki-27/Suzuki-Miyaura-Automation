import nimsos

with open( "./settings.txt" ) as f:
    ls = f.readlines()

for x in ls:
    if "NumObjectives" in x:
        NumObjectives = int( x.split( '=' )[1] )
    if "NumProposals" in x:
        NumProposals = int( x.split( '=' )[1] )

print( '\n--- settings ----------' )
print( 'NumObjectives =', NumObjectives )
print( 'NumProposals  =', NumProposals, '\n' )

print( '--- running nimsos ----------' )
nimsos.selection( method = "PHYSBO", input_file = "./candidates.csv", output_file = "./proposals.csv",
                num_objectives = NumObjectives, num_proposals = NumProposals )

with open( "./proposals.csv" ) as f:
    ls = f.readlines()[1:]

# nims-os outputs experimental number started from 0
# so add 1 to convert our exp no
exps = []
for i in range( NumProposals ):
    exps.append( int( ls[i].split(',')[0] ) + 1 )

print( '\n--- next experiment ----------' )
print( 'proposals =', exps )

with open( "./next_exp.csv", mode='w' ) as f:
    for x in exps:
        f.write( str( x ) + ',' )

# generation for robot input
with open( "./exp_table.csv", mode='r' ) as f:
    strs = [ x.strip('\n').split(',') for x in f.readlines()[1:] ]

all_exp_table = [ ( int( exp_ID ), int( var1 ), int( var2 ), int( var3 ), notation ) for exp_ID, var1, var2, var3, notation in strs ]

with open( "./input_for_chemspeed.csv", mode='w' ) as f:
    f.write( 'ligand, base, solvent\n' )
    for num in exps:
        for exp_ID, var1, var2, var3, notation in all_exp_table:
            if num == exp_ID:
                f.write( str( var1 ) + ',' + str( var2 ) + ',' + str( var3 ) + '\n' )
                print( 'next exp ID {:5.0f}, '.format(exp_ID) + str( notation ).rjust( 26 ) )
print( '\n========== END ================================================================================\n\n' )

