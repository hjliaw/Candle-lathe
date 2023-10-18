#!/usr/bin/python3

# GrblGru lathe V1.0 usually generates finish cuts with segments
# post process to smooth it out with curve fit

# what if gcode unit=inch ?
# todo: avoid curve fit when large and small sloped        

import struct
import sys
import getopt
import re

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

xbs = 0.0      # x-axis backlash (z-axis is not critical for lathe)
zmin = -1e6    # regoin to be smoothed
zmax = -1e6 

def usage(prog, exit_stat=0):
    str = 'Usage: %s [-x xbkls] [-r zmin:zmax] gcode\n' % prog
    str += \
'''  -x xbkls
     [experimental] specify x-axis backlash uit= mm, default = 0.0
  -r zmin:zmax
     specify the region to be smoothed
'''
    if exit_stat != 0: sys.stderr.write(str)
    else:              sys.stdout.write(str)
    sys.exit(exit_stat)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hx:r:')
except:
    usage(sys.argv[0], 1)
    
if len(args) == 0:
    usage(sys.argv[0], 1)

for opt, val in opts:
    if opt in ( '-h', '--help'):
        usage( sys.argv[0], 0 )
    elif opt in ('-x'):
        xbs = float(val)
    elif opt in ('-r'):
        rx = [-abs(float(i)) for i in val.split(":")]
        zmax = max(rx)
        zmin = min(rx)

gcfile = open( args[0], 'r')
Lines = gcfile.readlines()

if not re.findall( r'GrblGru', Lines[0]) :
    print("ERROR: file %s is not a g-code generated by GrblGru" % args[0], file=sys.stderr )
    sys.exit(2)

print("x backlash = %.4f" % xbs, file=sys.stderr )
print("z range = %.3f : %.3f" % (zmin, zmax), file=sys.stderr )

#--------------------------------------------------------------------------------------------
# figure out how many Finish passes
#--------------------------------------------------------------------------------------------

def back2start(ltxt):
    # GrblGru diff versoins have different style of comments
    if re.findall( r'gcodebacktostart', ltxt) or \
       re.findall( r'back to start', ltxt, flags=re.IGNORECASE) :
        return True
    else:
        return False

def not_finish(ltxt):
    if re.findall( r'active =', ltxt, flags=re.IGNORECASE) :
        return True
    else:
        return False 
    
fin = []
finPass = 0
lcnt = 0
for line in Lines:
    lcnt += 1

    #fin = re.findall( r'Finish', line)  # not wrking here ? but fine in main loop ?
    if re.findall( r'Finish', line) :
        fin = [1]
        #print("finish found at line %d" % lcnt, file=sys.stderr )

    if not_finish(line):
        fin = []
        #print("finish cleared at line %d" % lcnt, file=sys.stderr )

    if fin and back2start(line):
        finPass += 1

print("finish pass(es) = %d" % finPass, file=sys.stderr )

#--------------------------------------------------------------------------------------------
# vars for backlash compensation
#--------------------------------------------------------------------------------------------

xold = 0.0
xnew = 0.0
comp = False

zold = 0.0
znew = 0.0

mx = [[] for i in range(finPass+1)]
mz = [[] for i in range(finPass+1)]

fin = []
finFR = [100]
finLines = [[] for i in range(finPass+1)]    # +1 to hold the final return gcodes

fp = 0

for line in Lines:

    if not_finish(line):  fin=[]

    # backlash comp on retraction, as we should have "wind x in" when kissing the stock
    comment = ""
    xpos = re.findall( r'[X](.?\d+.\d+)', line)
    if xpos:
        xnew = float( xpos[0])
        if (abs(xnew - xold) > 0.002 ):    # abs test to avoid rouding error from GrblGru
            if ( not comp and xnew > xold ): comp = True
            if (     comp and xnew < xold ): comp = False

        if (comp and xbs > 1e-6):
            xcomp = xnew + xbs
            comment =  "     ; BKLS X%s -> X%.3f" % (xpos[0], xcomp)
        else:
            xcomp = xnew    
            
        line = line.replace( 'X%s' % xpos[0], 'X%.3f' % xcomp )
        xold = xnew

    zpos = re.findall( r'[Z](.?\d+.\d+)', line)
    if zpos:
        zold = znew
        znew = float( zpos[0])

    nline =  line.strip() + comment

    if fin :      # process finish passes
        if back2start(line): fp += 1

        finLines[fp].append(nline)

        if xpos and zpos and znew < zmax and znew > zmin :   # get (last) finish feedrate
            finFR = re.findall( r'[F](.?\d+.\d+)', line)

        if znew < zmax and znew > zmin :  # 2D array
            mx[fp].append( xnew )
            mz[fp].append( znew )
    else:
        print( nline )
        fin = re.findall( r'( Finish )', line )

gcfile.close()

#----------------------------------------------------------------------------------------------

if finFR :
    print("finish feedrate= %s" % finFR[0] , file=sys.stderr )
else:
    print("finish feedrate not found" , file=sys.stderr )
    sys.exit(1)

# spl wants increaseing 1st arg (conventionl x, z here)

for fidx in range(finPass+1):
    mrz= mz[fidx][::-1]   # mz.reverse() NOT working     
    mrx= mx[fidx][::-1]

    if len(mrz) > 2 :
        spl = UnivariateSpline(mrz, mrx )
        zs = np.linspace( min(mz[fidx]), max(mz[fidx]), int( abs(zmax-zmin)*10) )    # every 0.1mm
        xs = spl(zs)

    # process the finish cut

    for line in finLines[fidx]:
        znew = 1e6
        xpos = re.findall( r'[X](.?\d+.\d+)', line)
        zpos = re.findall( r'[Z](.?\d+.\d+)', line)

        if zpos:
            znew = float( zpos[0])

        # asumption: finish pass, z goes from 0 to negative in gcode
        if znew >= zmax :
            smoothed = False
            print( line.strip() )
        elif znew >= zmin :
            if not smoothed :
                Nzs = len(zs)
                print("DBG: Nzs= %d" % Nzs , file=sys.stderr )
                print( "( smoothed curve begins )" )
                for i in range(Nzs,0,-1):  # N..1
                    print( "F%s X%.3f Z%.3f" % (finFR[0], xs[i-1], zs[i-1]) )
                print( "( smoothed curve ends )" )
                smoothed = True
        else:
            print( line.strip() )


# show plots
# todo: plot the whole gcode

#plt.plot(mrz, mrx, 'r+', lw=1)
#plt.plot( zs, xs, 'g', lw=1)
#plt.show()

