#!/usr/bin/python3

# backlash compensation in X


import struct
import sys
import getopt
import re

showOffset = False
byteOffset = 0

def usage(prog, exit_stat=0):
    str = 'Usage: %s [-x x-backlash] g-code\n' % prog
    str += \
'  -x --xbacklash\n' + \
'    x-axis backlash, such as 0.1mm or 0.003\n'
    
    if exit_stat != 0:
        sys.stderr.write(str)
    else:
        sys.stdout.write(str)
    sys.exit(exit_stat)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hx', ['help', 'xbacklash'])
except:
    usage(sys.argv[0], 1)

if len(args) == 0:
    usage(sys.argv[0], 1)


for opt, val in opts:
    if opt in ( '-h', '--help'):
        usage( sys.argv[0], 0 )
    elif opt in ('-x', '--xbacklash'):
        xbs = 0.1

gcfile = open( args[0], 'r')
Lines = gcfile.readlines()

xold = 0.0
xnew = 0.0
xbs  = 0.1
comp = False

count = 0
for line in Lines:
    count += 1
    #print("%4d %s" % (count, line.strip()))

    comment = ""

    xpos = re.findall( r'[X](.?\d+.\d+)', line)
    if xpos:
        xnew = float( xpos[0])

        # abs test to avoid rouding error from GrblGru
        # backlash comp on retraction, as we already "wind x in"
        
        if (abs(xnew - xold) > 0.002 ):
            if ( not comp and xnew > xold ): comp = True
            if (     comp and xnew < xold ): comp = False

        if (comp ):
            xcomp = xnew + xbs
            comment =  "     ; BKLS X%s -> X%.3f" % (xpos[0], xcomp)
        else:
            xcomp = xnew    
            
        #print( ";" +  line.strip() )
        line = line.replace( 'X%s' % xpos[0], 'X%.3f' % xcomp )
        xold = xnew

    print( line.strip() + comment )

gcfile.close()
