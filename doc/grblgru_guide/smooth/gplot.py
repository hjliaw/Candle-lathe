#!/usr/bin/python3

# GrblGru lathe V1.0 usually generates finish cuts with segments
# post process to smooth it out with curve fit

# can be applied multiple times

# what if gcode unit=inch ?
# todo: avoid curve fit when large and small sloped        

import struct
import sys
import re
import os

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

xbs = 0.0           # x-axis backlash (z-axis is not critical for lathe)
finPass = 0         # number of final passes
zmin, zmax, xmin, xmax = -1e6, +1e6, -1e6, +1e6   # g-code range
nfname = ""
smthdc = [[] for i in range(100)]    # plt obj, assumes finPass < 100

def dbg_print(msg):
    print( "    %s" % msg, file=sys.stderr )

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
    ai, bi = a, b
    if a[0] > a[1] :
        ai, bi = a[::-1], b[::-1]
    return ai, bi

def decreasing( a, b):
    if len(a) < 2 : return a, b
    ai, bi = a, b
    if a[0] < a[1] :
        ai, bi = a[::-1], b[::-1]
    return ai, bi

def smooth(lines, zrange, xrange, dir):

    ngcfile = open( nfname, 'w')
    
    finPass = finish_passes(lines)
    dbg_print("DBG: finish passes= %d" % finPass )

    global smthdc
    mx       = [[] for i in range(finPass+1)]
    mz       = [[] for i in range(finPass+1)]
    finLines = [[] for i in range(finPass+1)]    # +1 to hold the final return gcodes
    
    fin = []
    fp = 0               # 0..finPass-1

    zmax = max(zrange) + 1e-4   # in this function, z-region to be smoothed
    zmin = min(zrange) - 1e-4

    xmax = max(xrange) + 1e-4   # in this function, z-region to be smoothed
    xmin = min(xrange) - 1e-4

    comp = False
    xold, xnew, zold, znew = [0.0]*4
    
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
                mx[fp].append( xnew )
                mz[fp].append( znew )
        else:
            ngcfile.write( nline + '\n' )
            fin = re.findall( r'( Finish )', line ) # keep looking for finish cut(s)

    #----------------------------------------------------------------------------------------------

    finFR = finish_feedrate(lines)
            
    for fidx in range(finPass+1):
        if len(mz[fidx]) > 2 :
            try:
                if smthdc[fidx] : smthdc[fidx].remove() 
            except:
                dbg_print( "no curve to delete")
        plt.gcf().canvas.draw_idle()

    for fidx in range(finPass+1):
        # spl wants increaseing 1st arg (conventionlly x, but is z here for lathe)

        if dir == 'v':    # vertical fit lathe-X as the variable
            mrx, mrz = increasing( mx[fidx], mz[fidx])
        else :            # horizontal (only 'S' or 'H' will be passed here
            mrz, mrx = increasing( mz[fidx], mx[fidx])

        if len(mrz) > 2 :
            nn = 2*len(mrz)
            try:
                if dir == 'v':
                    spl = UnivariateSpline(mrx, mrz )
                    xs = np.linspace( min(mx[fidx]), max(mx[fidx]), nn )    
                    zs = spl(xs)
                else:  # normal horizontal curve fit
                    spl = UnivariateSpline(mrz, mrx )
                    zs = np.linspace( min(mz[fidx]), max(mz[fidx]), nn )
                    xs = spl(zs)
            except:
                msg = "Click OK to try in the different direction"
                messagebox.showerror("Fail to fit a curve", msg )
        
                try:
                    if dir == 'v':
                        spl = UnivariateSpline(mrz, mrx )
                        zs = np.linspace( min(mz[fidx]), max(mz[fidx]), nn )
                        xs = spl(zs)
                    else:
                        spl = UnivariateSpline(mrx, mrz )
                        xs = np.linspace( min(mx[fidx]), max(mx[fidx]), nn )    
                        zs = spl(xs)
                except:
                    msg = "May need to narrow down the region to be smoothed"
                    messagebox.showerror("Failed again)", msg )
                    return

            # force end points to meet with shift (linearly scaled)
            # makes the transition smooth, but may be too close to rough cuts
            
            N = len(xs)
            s0 = mrx[0]  - xs[0]
            s1 = mrx[-1] - xs[-1]
            for i in range(N):
                xs[i] +=  s0 + (s1-s0)*i/(N-1)
            
            smthdc[fidx], = plt.plot( zs, xs, 'r.-', lw=1)
            plt.gcf().canvas.draw_idle()


        # process the finish cut

        smoothed = False
        for line in finLines[fidx]:
            # skip "smoothed" lines, they will mes up var smoothed 
            if re.findall( r'smoothed', line): continue
            znew = 1e6
            xnew = 1e6
            xpos = re.findall( r'[X](.?\d+.\d+)', line)
            zpos = re.findall( r'[Z](.?\d+.\d+)', line)
            if zpos: znew = float( zpos[0])
            if xpos: xnew = float( xpos[0])

            # asumption: z goes from 0 to negative dring finish

            if znew >= zmax:
                smoothed = False               # may not be set if zmax > 0
                ngcfile.write( line + '\n' )
            elif znew >= zmin and xnew <= xmax:
                if not smoothed :
                    Nzs = len(zs)
                    dbg_print("DBG: Nzs= %d" % Nzs )
                    ngcfile.write( "( smoothed curve begins )\n" )

                    # ensure z in decreasing order
                    zs, xs = decreasing( zs, xs)
                    for i in range(Nzs):
                        ngcfile.write( "F%s X%.3f Z%.3f\n" % (finFR, xs[i], zs[i]) )
                        
                    ngcfile.write( "( smoothed curve ends )\n" )
                    smoothed = True
            else:
                ngcfile.write( line + '\n' )

    #----------------------------------------------------------------------------------------------
    
    ngcfile.close()
    dbg_print("New gcode file %s geerated\n" % nfname )

def extract_data(lines):
    xnew, znew = 0, 0
    rx, rz, fx, fz = [[] for i in range(4)]
    fin = []
    for line in lines:
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
            
    return rx, rz, fx, fz

# scan the lines multiple times, should be ok, as lathe files are relatively small

def finish_feedrate(lines):   # get (last) frrerate during finish
    fr, fin = [], []
    for line in lines:
        xpos = re.findall( r'[X](.?\d+.\d+)', line)
        zpos = re.findall( r'[Z](.?\d+.\d+)', line)

        if not_real_finish(line):  fin=[]
        if fin :
            if xpos and zpos:    # last line starts with Fnnn
                fr = re.findall( r'[F](.?\d+.\d+)', line)
        else:
            fin = re.findall( r'( Finish )', line )
    if fr: return float(fr[0])
    else : return 0.0

def load_file(fname):
    while True:
        global Lines, fnsel, fnsel_nopath
        if fname :
            fnsel = fname
        else:
            fnsel = filedialog.askopenfilename( title="Select A G-Code file", \
                                                filetypes=[("G-Code","*.gc"),("G-Code","*.ngc"),("G-Code","*.nc")])
        if not fnsel: sys.exit(0)
        gcfile = open( fnsel, 'r')
        Lines = gcfile.readlines()   # todo: try
        gcfile.close()
        fnsel_nopath = os.path.basename(fnsel)

        if not re.findall( r'GrblGru', Lines[0]) :
            msg = "File \"%s\" not generated by GrblGru, continue ?" % fnsel_nopath
            if messagebox.warning("Warning", msg ):
                break

        if finish_passes(Lines) < 1:
            msg = "No finish pass found in \"%s\", exit ?" % fnsel_nopath
            if messagebox.askyesno("Error", msg ):
                sys.exit(1)

        dbg_print( "fin FR= %f" % finish_feedrate(Lines) )

        if finish_feedrate(Lines) > 0.0:
            break
        else:
            msg = "No feedrate found in finish cut(s), \"%s\", exit ?" % fnsel_nopath
            if messagebox.askyesno("Error", msg ):
                sys.exit(1)
        
    idx   = fnsel.rfind('.')
    fbase = fnsel[:idx]
    fext  = fnsel[idx+1:]

    if underN := re.findall( r'_(\d+)$', fbase) :
        cnt = int(underN[0])
        nfname = "%s%d.%s" % (fbase[:-len(underN[0])], cnt+1, fext)
    else:
        nfname =  "%s_1.%s" % (fbase, fext)


def init_vars():
    global Lines, rx, rz, fx, fz
    global xmin, xmax, zmin, zmax
    global Zs, Xs, bidx, bnd
    
    rx, rz, fx, fz = extract_data(Lines)

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
        
        # detect which end point, works most of the time, but can be confusing when user zoom in
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
    if event.key == 'S' or event.key == 'h' or event.key == 'v' :
        dbg_print('smooth range : Z=[%.3f, %.3f]' % (Zs[0],  Zs[1]) )
        dbg_print('smooth range : X=[%.3f, %.3f]' % (Xs[0],  Xs[1]) )
        smooth( Lines, Zs, Xs, event.key )

    if event.key == 'R':
        vis = not rufcuts.get_visible()
        print( "DBG vis = ", vis )
        rufcuts.set_visible(vis)
        plt.draw()
        
    if event.key == 'q' or event.key == 'Q' :
        sys.exit(0)

#---------------------------------------------------------------------------
# here we go
#---------------------------------------------------------------------------

root = tk.Tk()
root.withdraw()

load_file( [] if len(sys.argv)<2 else sys.argv[1] )
init_vars()

ar = (abs(xmax-xmin)/abs(zmax-zmin))
fig = plt.figure(num="g-plot", figsize=(16, 16*ar*1.2 ))  # need space for title
cid = fig.canvas.mpl_connect('button_press_event', mouse_event1)
cid = fig.canvas.mpl_connect('key_press_event', on_key)

plt.rcParams['keymap.zoom'] = 'z'
plt.rcParams['keymap.home'] = 'A'      # 'h'-fit no zoom out
plt.rcParams['keymap.forward'] = 'W'   # 'v'-fit no forward

plt.xlabel("lathe-Z (spindle)")
plt.ylabel("X (cross slide)")
plt.title(fnsel_nopath)

plt.gca().invert_yaxis()
plt.gca().set_aspect('equal')
rufcuts, = plt.plot( rz, rx, 'b--',  lw=0.2, label="rough")
fincuts, = plt.plot( fz, fx, 'g.-', lw=1, label="finish")

plt.show()

