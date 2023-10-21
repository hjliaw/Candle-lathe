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

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

xbs = 0.0      # x-axis backlash (z-axis is not critical for lathe)
zmin = -1e6    # regoin to be smoothed
zmax = -1e6

finPass = 1

def dbg_print(msg):
    print( "    %s" % msg, file=sys.stderr )

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

def has_finish(ltxt):
    if re.findall( r'Finish', ltxt):
        return True
    else:
        return False
            
def not_real_finish(ltxt):
    if re.findall( r'active =', ltxt, flags=re.IGNORECASE) :
        return True
    else:
        return False

def finish_passes(lines):
    nPass = 0
    fin = False
    for line in lines:
        if has_finish(line):         fin = True
        if not_real_finish(line):    fin = False
        if fin and back2start(line): nPass += 1
    return nPass

def increasing( a, b):  # ensure a is in increasing order
    if len(a) < 2 : return a, b
    ai = a
    bi = b
    if a[0] > a[1] :
        ai = a[::-1]
        bi = b[::-1]
    return ai, bi

def decreasing( a, b):
    if len(a) < 2 : return a, b
    ai = a
    bi = b
    if a[0] < a[1] :
        ai = a[::-1]
        bi = b[::-1]
    return ai, bi

smthdc   = [[] for i in range(20)]    # plt obj

def smooth(lines, zrange, xrange, dir):

    ngcfile = open( nfname, 'w')
    
    finPass = finish_passes(lines)
    dbg_print("DBG: finish passes= %d" % finPass )

    global smthdc
    mx       = [[] for i in range(finPass+1)]
    mz       = [[] for i in range(finPass+1)]
    finLines = [[] for i in range(finPass+1)]    # +1 to hold the final return gcodes
    
    fin = []
    finFR = []           # (last) feedrate during finish cut
    fp = 0               # 0..finPass-1

    zmax = max(zrange) + 1e-4   # in this function, z-region to be smoothed
    zmin = min(zrange) - 1e-4

    xmax = max(xrange) + 1e-4   # in this function, z-region to be smoothed
    xmin = min(xrange) - 1e-4

    comp = False
    xold = 0.0
    xnew = 0.0
    zold = 0.0
    znew = 0.0
    
    for line in lines:

        if not_real_finish(line):  fin=[]

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
            if back2start(line): fp += 1
            finLines[fp].append(nline)
            
            if xpos and zpos and znew < zmax and znew > zmin :   # get (last) finish feedrate
                finFR = re.findall( r'[F](.?\d+.\d+)', line)
                mx[fp].append( xnew )
                mz[fp].append( znew )
        else:
            ngcfile.write( nline + '\n' )
            fin = re.findall( r'( Finish )', line ) # keep looking for finish cut(s)

    #----------------------------------------------------------------------------------------------

    if finFR :
        dbg_print("DBG: finish feedrate = %s" % finFR[0] )
    else:
        dbg_print("finish feedrate not found")
        sys.exit(1)

    #----------------------------------------------------------------------------------------------
            
    # nearly vetical curve should be fit with z(x)
    # while horizotal ones should be fit with x(z)   Q: can user specify this ?
    
    for fidx in range(finPass+1):
        # spl wants increaseing 1st arg (conventionlly x, but is z here for lathe)

        if dir == 'V':    # vertical fit lathe-X as the variable
            mrx, mrz = increasing( mx[fidx], mz[fidx])
        else :            # horizontal (only 'S' or 'H' will be passed here
            mrz, mrx = increasing( mz[fidx], mx[fidx])

        if len(mrz) > 2 :
            # interpolate every 0.2mm, to be parameterized
            if dir == 'V':
                spl = UnivariateSpline(mrx, mrz )
                xs = np.linspace( min(mx[fidx]), max(mx[fidx]), int( abs(xmax-xmin)*5) )    
                zs = spl(xs)
            else:  # normal horizontal curve fit
                spl = UnivariateSpline(mrz, mrx )
                zs = np.linspace( min(mz[fidx]), max(mz[fidx]), int( abs(zmax-zmin)*5) )
                xs = spl(zs)
            
            # force end points to meet with shift (linearly scaled)
            # makes the transition smooth, but may be too close to rough cuts
            N = len(xs)
            s0 = mrx[0]  - xs[0]
            s1 = mrx[-1] - xs[-1]
            for i in range(N):
                xs[i] +=  s0 + (s1-s0)*i/(N-1)
            
            # delete old trace if exists, add new
            if smthdc[fidx] : smthdc[fidx].remove()   
            smthdc[fidx], = plt.plot( zs, xs, 'r.-', lw=1)
            plt.gcf().canvas.draw_idle()

        # process the finish cut

        smoothed = False
        for line in finLines[fidx]:
            znew = 1e6
            xpos = re.findall( r'[X](.?\d+.\d+)', line)
            zpos = re.findall( r'[Z](.?\d+.\d+)', line)
            if zpos: znew = float( zpos[0])

            # asumption: z goes from 0 to negative dring finish

            if znew >= zmax:
                smoothed = False               # may not be set if zmax > 0
                ngcfile.write( line + '\n' )
            elif znew >= zmin :
                if not smoothed :
                    Nzs = len(zs)
                    dbg_print("DBG: Nzs= %d" % Nzs )
                    ngcfile.write( "( smoothed curve begins )\n" )
                    # ensure z in decreasing order
                    zs, xs = decreasing( zs, xs)
                    for i in range(Nzs):
                        ngcfile.write( "F%s X%.3f Z%.3f\n" % (finFR[0], xs[i], zs[i]) )

                    #for i in range(Nzs,0,-1):  # N..1
                    #    ngcfile.write( "F%s X%.3f Z%.3f\n" % (finFR[0], xs[i-1], zs[i-1]) )
                    ngcfile.write( "( smoothed curve ends )\n" )
                    smoothed = True
            else:
                ngcfile.write( line + '\n' )

    #----------------------------------------------------------------------------------------------
    
    ngcfile.close()
    dbg_print("New gcode file %s geerated\n" % nfname )

#-----------------------------------------------------------------------------

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hx:r:')
except:
    usage(sys.argv[0], 1)
    
#if len(args) == 0:
#    usage(sys.argv[0], 1)

for opt, val in opts:
    if opt in ( '-h', '--help'):
        usage( sys.argv[0], 0 )
    elif opt in ('-x'):
        xbs = float(val)

root = tk.Tk()
root.withdraw()

while True:
    global Lines, fnsel
    fnsel = filedialog.askopenfilename( title="Select A G-Code file", \
                                        filetypes=[("G-Code","*.gc"),("G-Code","*.ngc"),("G-Code","*.nc")])

    if not fnsel: sys.exit(0)

    gcfile = open( fnsel, 'r')
    Lines = gcfile.readlines()
    gcfile.close()

    if re.findall( r'GrblGru', Lines[0]) :
        break
    else:
        # tkinter generates ugly message box
        msg = "File %s is not generated by GrblGru, continue ?" % fnsel
        if messagebox.askyesno("Warning", msg ):
            break
        
# allow long file name, or relative position

idx = fnsel.rfind('.')
fbase = fnsel[:idx]
fext  = fnsel[idx+1:]

nfname =  "%s_1.%s" % (fbase, fext)
if underN := re.findall( r'_(\d+)$', fbase) :
    cnt = int(underN[0])
    nfname = "%s%d.%s" % (fbase[:-len(underN[0])], cnt+1, fext)

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
    if not_real_finish(line):  fin=[]

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

Zs = [None,None]
Xs = [None,None]
bidx = 0           # 0,1
bnd = [[], []]     # plt objs of the two bounding lines

def nearby(z, za):
    d = 1e6
    idx = -1
    for i in range(len(za)):
        if abs(z-za[i]) < d :
            d = abs(z-za[i])
            idx = i
    if idx >= 0 :
        return za[idx]
    else:
        return z
        
def mouse_event1(event):
    global Zs, Xs, bidx, bnd, plt
    if event.button == 3 :   # is MouseButton.RIGHT:  not defined
        zn = nearby( event.xdata, fz )
        xn = nearby( event.ydata, fx )
        
        # detect which end point
        if Zs[0] and Zs[1] :
            if abs(zn-Zs[0]) < 0.2*abs(zn-Zs[1]): bidx = 0
            if abs(zn-Zs[1]) < 0.2*abs(zn-Zs[0]): bidx = 1
        
        if bnd[bidx] : bnd[bidx].remove()
        bnd[bidx], = plt.plot( [zn, zn], [xmin, xmax], 'r-', lw=1)
        Zs[bidx] = zn   #event.xdata
        Xs[bidx] = xn   #event.ydata    
        bidx = 1 -bidx
        plt.gcf().canvas.draw_idle()

def on_key(event):
    if event.key == 'S' or event.key == 'H' or event.key == 'V' :
        dbg_print('smooth range : Z=[%.3f, %.3f]' % (Zs[0],  Zs[1]) )
        dbg_print('smooth range : X=[%.3f, %.3f]' % (Xs[0],  Xs[1]) )
        smooth( Lines, Zs, Xs, event.key )

    if event.key == 'q' or event.key == 'Q' :
        sys.exit(0)
        
fig = plt.figure()
cid = fig.canvas.mpl_connect('button_press_event', mouse_event1)
cid = fig.canvas.mpl_connect('key_press_event', on_key)

plt.gca().invert_yaxis()
plt.plot( rz, rx, 'b-', lw=1)
plt.plot( fz, fx, 'g.-', lw=1)
plt.show()

