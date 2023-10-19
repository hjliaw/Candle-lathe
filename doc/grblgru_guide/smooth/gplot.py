#!/usr/bin/python3

# GrblGru lathe V1.0 usually generates finish cuts with segments
# post process to smooth it out with curve fit

# can be applied multiple times

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

finPass = 1

def dbg_print(msg):
    print( msg, file=sys.stderr )

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

def finish_passes(lines):
    fin = []
    nPass = 0
    for line in lines:
        if re.findall( r'Finish', line): fin = [1]
        if not_finish(line):             fin = []
        if fin and back2start(line):     nPass += 1
    return nPass
    
def smooth(lines, zrange):
    finPass = finish_passes(lines)
    dbg_print("DBG: finPass= %d" % finPass )
            
    smthdc   = [[] for i in range(finPass+1)]    # plt obj
    mx       = [[] for i in range(finPass+1)]
    mz       = [[] for i in range(finPass+1)]
    finLines = [[] for i in range(finPass+1)]    # +1 to hold the final return gcodes
    
    fin = []
    finFR = []           # (last) feedrate during finish cut
    fp = 0               # 0..finPass-1

    zmax = max(zrange)   # in this function, z-region to be smoothed
    zmin = min(zrange)

    comp = False
    xold = 0.0
    xnew = 0.0
    zold = 0.0
    znew = 0.0
    
    for line in lines:

        if not_finish(line):  fin=[]

        # apply backlash comp on retraction, as we should have wound x in when kissing the stock
        comment = ""
        if xpos := re.findall( r'[X](.?\d+.\d+)', line) :
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

        if zpos := re.findall( r'[Z](.?\d+.\d+)', line):
            zold = znew
            znew = float( zpos[0])

        nline =  line.strip() + comment

        # process finish passes
        if fin :
            if back2start(line):
                fp += 1

            finLines[fp].append(nline)

            if xpos and zpos and znew < zmax and znew > zmin :   # get (last) finish feedrate
                finFR = re.findall( r'[F](.?\d+.\d+)', line)

            if znew < zmax and znew > zmin :  # 2D array
                mx[fp].append( xnew )
                mz[fp].append( znew )
        else:
            print( nline )
            fin = re.findall( r'( Finish )', line )

    #----------------------------------------------------------------------------------------------

    if finFR :
        dbg_print("finish feedrate= %s" % finFR[0] )
    else:
        dbg_print("finish feedrate not found")
        sys.exit(1)

    for fidx in range(finPass+1):
        # spl wants increaseing 1st arg (conventionlly x, but z here)

        mrz= mz[fidx][::-1]   # mz.reverse() NOT working     
        mrx= mx[fidx][::-1]

        if len(mrz) > 2 :
            spl = UnivariateSpline(mrz, mrx )
            zs = np.linspace( min(mz[fidx]), max(mz[fidx]), int( abs(zmax-zmin)*10) )    # every 0.1mm
            xs = spl(zs)

            if smthdc[fidx] :  smthdc[fidx].remove()
            smthdc[fidx], = plt.plot( zs, xs, 'r-', lw=1)
            plt.gcf().canvas.draw_idle()

        # process the finish cut

        for line in finLines[fidx]:
            znew = 1e6
            xpos = re.findall( r'[X](.?\d+.\d+)', line)
            zpos = re.findall( r'[Z](.?\d+.\d+)', line)
            if zpos: znew = float( zpos[0])

            # asumption: z goes from 0 to negative dring finish
            if znew >= zmax :
                smoothed = False
                print( line.strip() )
            elif znew >= zmin :
                if not smoothed :
                    Nzs = len(zs)
                    dbg_print("Nzs= %d" % Nzs )
                    print( "( smoothed curve begins )" )
                    for i in range(Nzs,0,-1):  # N..1
                        print( "F%s X%.3f Z%.3f" % (finFR[0], xs[i-1], zs[i-1]) )
                    print( "( smoothed curve ends )" )
                    smoothed = True
            else:
                print( line.strip() )

#-----------------------------------------------------------------------------

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
gcfile.close()

if not re.findall( r'GrblGru', Lines[0]) :
    dbg_print("ERROR: file %s is not a g-code generated by GrblGru" % args[0] )
    sys.exit(2)

#--------------------------------------------------------------------------------------------
# figure out boundary box, generates data points for rough and finish cuts
#--------------------------------------------------------------------------------------------

xold = 0.0
xnew = 0.0
zold = 0.0
znew = 0.0

rx=[]
rz=[]
fx=[]
fz=[]

fin=[]
for line in Lines:
    if not_finish(line):  fin=[]

    if xpos := re.findall( r'[X](.?\d+.\d+)', line) :
        xold = xnew
        xnew = float( xpos[0])
        
    if zpos := re.findall( r'[Z](.?\d+.\d+)', line) :
        zold = znew
        znew = float( zpos[0])

    if xpos or zpos :
        if fin :
            fx.append( xnew )
            fz.append( znew )
        else :
            rx.append( xnew )
            rz.append( znew )

    if not fin :
        fin = re.findall( r'( Finish )', line )
        
#----------------------------------------------------------------------------------------------

xmin = min( min(fx), min(rx) )
xmax = max( max(fx), max(rx) )
zmin = min( min(fz), min(rz) )
zmax = max( max(fz), max(rz) )
dbg_print(  'g-code limit : Z=[%.3f, %.3f]  X= [%.3f, %.3f]' % ( zmin, zmax, xmin, xmax) )

zs = [None,None]
bidx = 0           # 0,1
bnd = [[], []]     # plt objs of the two bounding lines

def mouse_event1(event):
    global zs, bidx, bnd, plt
    if event.button == 3 :   # is MouseButton.RIGHT:  not defined
        if bnd[bidx] : bnd[bidx].remove()
        bnd[bidx], = plt.plot( [event.xdata, event.xdata], [xmin, xmax], 'r-', lw=1)
        zs[bidx] = event.xdata    
        bidx = 1 -bidx
        plt.gcf().canvas.draw_idle()

def on_key(event):
    if event.key == 'S' :
        dbg_print('smooth range : Z=[%.3f, %.3f]' % (zs[0],  zs[1]) )
        smooth( Lines, zs )
    
fig = plt.figure()
cid = fig.canvas.mpl_connect('button_press_event', mouse_event1)
cid = fig.canvas.mpl_connect('key_press_event', on_key)

plt.gca().invert_yaxis()
plt.plot( rz, rx, 'b-', lw=1)
plt.plot( fz, fx, 'g.-', lw=1)
plt.show()

