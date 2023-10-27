#!/usr/bin/python3

# GrblGru lathe V1.0 usually generates finish cuts with segments
# post process to smooth it out with curve fit

# what if gcode unit=inch ? shold still works, will break if mixed metric and imperial

# todo: avoid curve fit when large and small sloped        

# After 'pip3 install PyQt5', the toolbar is moved to top of the windows
# and figure seems to be much bigger (or could be full-screen ?) 

import struct
import sys
import re
import os
import time

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

#import tkinter.ttk as ttk    # who use this ?

#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from matplotlib.backend_tools import ToolBase
matplotlib.rcParams["toolbar"] = "toolmanager"


Xbs = 0.0           # x-axis backlash (z-axis is not critical for lathe)
FinPass = 0         # number of final passes
Zmin, Zmax, Xmin, Xmax = -1e6, +1e6, -1e6, +1e6   # g-code range
NewFname = ""
SmthdC = [[] for i in range(100)]    # plt obj, assumes FinPass < 100
Lines=[]
NewLines = []
NPF = 1.5            # new points factor

nfile_saved = False

# class MyToolbar(NavigationToolbar2Tk):

#     def __init__(self, canvas, parent):
#         self.toolitems = (
#             ('Home', 'Reset original view', 'home', 'home'),
#             ('Back', 'Back to previous view', 'back', 'back'),
#             ('Forward', 'Forward to next view', 'forward', 'forward'),
#             (None, None, None, None),
#             ('Pan', 'Left button pans, Right button zooms\nx/y fixes axis, CTRL fixes aspect', 'move', 'pan'),
#             ('Zoom', 'Zoom to rectangle\nx/y fixes axis', 'zoom_to_rect', 'zoom'),
#             ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#             (None, None, None, None),
#             ('Save', 'Save g-code', 'filesave', 'mysave_file')
#         )
#         super().__init__(canvas, parent)

#     def mysave_file(self):
#         print("TBD, save g-code file...")
#         msg.showwarning("Warning", "TBD, save g-code")
        

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

def save_new():
    global NewFname, NewLines, nfile_saved
    nfile_saved = False
    if not NewLines :
        msg = "Nothing new to save. \n\nHint: right clicks to define region, 'v' or 'h' key to smooth"
        messagebox.showwarning("No New Data", msg )
        return

    # check if file exists
    if os.path.isfile( NewFname ):
        msg = "\"%s\" already exists\n\nover-write?" % os.path.basename(NewFname)
        if not messagebox.askyesno("File Exists", msg ):
            NewFname = filedialog.asksaveasfilename( initialfile = NewFname,
                                          filetypes=[("G-Code","*.gc"),("G-Code","*.ngc"),("G-Code","*.nc")] )

    ngcfile = open( NewFname, 'w')
    for nline in NewLines:
                ngcfile.write(nline)

    ngcfile.close()
    #dbg_print("New gcode file %s geerated\n" % NewFname )
    nfile_saved = True
    NewLines = []

def smooth(lines, zrange, xrange, dir):
    global NewLines, SmthdC, NPF
    NewLines = []
    
    FinPass = finish_passes(lines)
    dbg_print("DBG: finish passes= %d" % FinPass )
    mx       = [[] for i in range(FinPass+1)]
    mz       = [[] for i in range(FinPass+1)]
    finLines = [[] for i in range(FinPass+1)]    # +1 to hold the final return gcodes
    
    fin = []
    fp = 0               # 0..FinPass-1

    Zmax = max(zrange) + 1e-4   # in this function, z-region to be smoothed
    Zmin = min(zrange) - 1e-4

    Xmax = max(xrange) + 1e-4   # in this function, z-region to be smoothed
    Xmin = min(xrange) - 1e-4

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

            if (comp and Xbs > 1e-6):
                xcomp = xnew + Xbs
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
            
            if xpos and zpos and znew < Zmax and znew > Zmin :
                mx[fp].append( xnew )
                mz[fp].append( znew )
        else:
            NewLines.append( nline + '\n' )
            fin = re.findall( r'( Finish )', line ) # keep looking for finish cut(s)

    finFR = finish_feedrate(lines)
            
    for fidx in range(FinPass+1):
        if len(mz[fidx]) > 2 :
            try:
                if SmthdC[fidx] : SmthdC[fidx].remove() 
            except:
                dbg_print( "warning: no curve to delete (unusal, but happens)")
        plt.gcf().canvas.draw_idle()

    for fidx in range(FinPass+1):
        # todo: try both, and use the one with least error

        # u-spline wants requires 1st arg
        if dir == 'v':    # vertical fit lathe-X as the variable
            mrx, mrz = increasing( mx[fidx], mz[fidx])
        else :            # horizontal (only 'S' or 'H' will be passed here
            mrz, mrx = increasing( mz[fidx], mx[fidx])

        if len(mrz) > 2 :
            nn = int(NPF*len(mrz))
            if nn < 2 :
                nn = 2
                NPF=NPF*1.5   # not necessary, but prevet NPF from becoming 0
            try:
                if dir == 'v':
                    spl = UnivariateSpline(mrx, mrz )
                    xs = np.linspace( min(mx[fidx]), max(mx[fidx]), nn )    
                    zs = spl(xs)
                else:  # 'h'
                    spl = UnivariateSpline(mrz, mrx )
                    zs = np.linspace( min(mz[fidx]), max(mz[fidx]), nn )
                    xs = spl(zs)
            except:
                msg = "Will try the different direction"
                messagebox.showerror("Fail to fit a curve with %s" % dir, msg )
        
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
                    msg = "Need to change the region to be smoothed"
                    messagebox.showerror("Failed to fit a curve again", msg )
                    return

            # force end points to meet with shift (linearly scaled)
            # makes the transition smooth, but may be too close to rough cuts
            
            N = len(xs)
            s0 = mrx[0]  - xs[0]
            s1 = mrx[-1] - xs[-1]
            for i in range(N):
                xs[i] +=  s0 + (s1-s0)*i/(N-1)
            
            SmthdC[fidx], = plt.plot( zs, xs, 'r.-', lw=1)
            plt.gcf().canvas.draw_idle()

        # process the finish cut

        smoothed = False
        for line in finLines[fidx]:
            if re.findall( r'smoothed', line): continue   # otherwise, will mess up var 'smoothed'  
            znew = 1e6
            xnew = 1e6
            xpos = re.findall( r'[X](.?\d+.\d+)', line)
            zpos = re.findall( r'[Z](.?\d+.\d+)', line)
            if zpos: znew = float( zpos[0])
            if xpos: xnew = float( xpos[0])

            # requirement: z goes from 0 to negative during finish cut(s)

            if znew >= Zmax:
                smoothed = False               # may not be set if Zmax > 0
                NewLines.append( line + '\n')
            elif znew >= Zmin and xnew <= Xmax:
                if not smoothed :
                    zs, xs = decreasing( zs, xs)
                    NewLines.append( "( smoothed curve begins )\n" )
                    Nzs = len(zs)
                    dbg_print( "No. of data pints: old= %d -> new= %d" % (len(mz[fidx]), Nzs) ) 
                    for i in range(Nzs): NewLines.append(  "F%s X%.3f Z%.3f\n" % (finFR, xs[i], zs[i]) )
                    NewLines.append( "( smoothed curve ends )\n" )
                    smoothed = True
            else:
                NewLines.append( line + '\n')

def extract_data(lines):
    xnew, znew = 0, 0
    rx, rz, fx, fz = [[] for i in range(4)]
    fin = []
    for line in lines:
        if not_real_finish(line):  fin=[]

        if xpos := re.findall( r'[X](.?\d+.\d+)', line) :
            xnew = float( xpos[0])
        if zpos := re.findall( r'[Z](.?\d+.\d+)', line) :
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

# scan the lines multiple times, as lathe g-codes are small

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
    global Lines, fnsel, fnsel_nopath, NewFname
    while True:
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
            msg = "File \"%s\" not generated by GrblGru\n\n ignore and continue ?" % fnsel_nopath
            if not messagebox.askyesno("Warning", msg ):
                break

        if finish_passes(Lines) < 1:
            msg = "No finish pass found in \"%s\" \n\n Exit ?" % fnsel_nopath    # todo: reload
            if messagebox.askyesno("Error", msg ):
                sys.exit(1)

        dbg_print( "gcode = %s" % fnsel_nopath )
        dbg_print( "fin FR= %f" % finish_feedrate(Lines) )

        if finish_feedrate(Lines) > 0.0:
            break
        else:
            msg = "No feedrate found in finish cut(s), \"%s\" \n\n Exit ?" % fnsel_nopath
            if messagebox.askyesno("Error", msg ):
                sys.exit(1)
        
    idx   = fnsel.rfind('.')
    fbase = fnsel[:idx]
    fext  = fnsel[idx+1:]

    if underN := re.findall( r'_(\d+)$', fbase) :
        cnt = int(underN[0])
        NewFname = "%s%d.%s" % (fbase[:-len(underN[0])], cnt+1, fext)
    else:
        NewFname =  "%s_1.%s" % (fbase, fext)

    global rx, rz, fx, fz
    global Xmin, Xmax, Zmin, Zmax
    global Zs, Xs, bidx, bnd
    
    rx, rz, fx, fz = extract_data(Lines)

    Xmin = min( min(fx), min(rx) )
    Xmax = max( max(fx), max(rx) )
    Zmin = min( min(fz), min(rz) )
    Zmax = max( max(fz), max(rz) )
    dbg_print(  'g-code limit : Z=[%.3f, %.3f]  X= [%.3f, %.3f]' % ( Zmin, Zmax, Xmin, Xmax) )

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
        bnd[bidx], = plt.plot( [zn, zn], [Xmin, Xmax], 'r-', lw=1)
        Zs[bidx] = zn   #event.xdata
        Xs[bidx] = xn   #event.ydata    
        bidx = 1 -bidx
        plt.gcf().canvas.draw_idle()



def on_key(event):
    global nfile_saved, saved_key
    if event.key == 'S' or event.key == 'h' or event.key == 'v' :
        dbg_print('smooth range : Z=[%.3f, %.3f]' % (Zs[0],  Zs[1]) )
        dbg_print('smooth range : X=[%.3f, %.3f]' % (Xs[0],  Xs[1]) )
        saved_key = event.key
        smooth( Lines, Zs, Xs, event.key )

    if event.key == 'R':   # toggle rough cut
        vis = not rufcuts.get_visible()
        print( "DBG vis = ", vis )
        rufcuts.set_visible(vis)
        plt.draw()

    if event.key == 'L':  # load new file
        plt.close()
        gplot([])         # CRASH !?

    if event.key == '+' or event.key == '-':  # more|less points
        global NPF
        if NewLines :
            if event.key == '+' : NPF = NPF * 1.5; mol = "more"
            if event.key == '-' : NPF = NPF / 1.5; mol = "less"
            dbg_print( "smooth with %s data points" % mol )
            smooth( Lines, Zs, Xs, saved_key )

    if event.key == 's':
        save_new()
        if nfile_saved:
            msg = "G-code file \"%s\" saved\n\n OK to load new file" % os.path.basename(NewFname )
            messagebox.showinfo("Info", msg )
            plt.close()

    if event.key == 'q' or event.key == 'Q' :
        sys.exit(0)

def format_coord(x,y):
    return "Z={:.2f} X={:.2f}".format(x,y)

class SaveGcode(ToolBase):   # to be merged with key-event 's'
    default_keymap = 'M'
    description = 'Save Modified G-Code'
    image='filesave'  # see ~/.local/lib/python3.10/site-packages/matplotlib/backend_tools.py
    def trigger(self, *args, **kwargs):
        save_new()
        if nfile_saved:
            msg = "G-code file \"%s\" saved\n\n click to load new file" % os.path.basename(NewFname )
            messagebox.showinfo("Info", msg )
            plt.close()


def gplot(fn):
    global rufcuts, fincuts, fnsel_nopath, nfile_saved
    
    load_file( fn )
    nfile_saved = False

    #ar = (abs(Xmax-Xmin)/abs(Zmax-Zmin))   NOT useful, esp after zoomed in
    #fig = plt.figure(num=fnsel_nopath, figsize=(16, 16*ar*1.2 ))  # space for title
    #ax = fig.subplots()
    
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.98)

    ax.format_coord=format_coord
    cid = fig.canvas.mpl_connect('button_press_event', mouse_event1)
    cid = fig.canvas.mpl_connect('key_press_event', on_key)

    fig.canvas.manager.set_window_title('gplot')

    tm = fig.canvas.manager.toolmanager   # finally some tool buttons can be removed
    tm.remove_tool('subplots')
    tm.remove_tool('help')
    tm.remove_tool('save')
    tm.add_tool("save", SaveGcode)
    fig.canvas.manager.toolbar.add_tool( tm.get_tool("save"), "toolgroup")

    # before Qt installation, matplotlib.backends.backend_gtk4.SaveFigureGTK4
    # after                   matplotlib.backends.backend_qt.SaveFigureQt
    # can be changed
    #    "MPLBACKEND=GTK4Agg ./gplot.py  KnobReel2.gc" 
    #    "MPLBACKEND=QtAgg   ./gplot.py  KnobReel2.gc"

    stm = tm.tools['save']
    print(stm)   
    print( type(stm) )

    #sys.exit(2)

    plt.xlabel("Z (lathe spindle)")  # if moved into main, generate extra empty figure 
    plt.ylabel("X (cross slide)")
    plt.title(fnsel_nopath)
    
    plt.gca().invert_yaxis()
    plt.gca().set_aspect('equal')
    rufcuts, = plt.plot( rz, rx, 'b--', lw=0.2, label="rough")
    fincuts, = plt.plot( fz, fx, 'g.-', lw=1.0,   label="finish")

    # add button, unfortunately  mess up subsequent plt
    #axsave = fig.add_axes([0.7, 0.05, 0.2, 0.05])
    #img = Image.open("disk.gif")

    #axsave = ax.inset_axes([.7, -.4, .2, .1],)   # position fine, but mess up curve fit ??
    #bsave = Button(ax=axsave, label='Save gcode' )  #, image=img)
    #bsave.on_clicked(foo)

    # gee, this is so hard to tweak,
    
    plt.show()   # blocking
    
#---------------------------------------------------------------------------
# here we go
#---------------------------------------------------------------------------

root = tk.Tk()
root.withdraw()

plt.rcParams['keymap.home'] = 'A'      # 'h' fit
plt.rcParams['keymap.forward'] = 'W'   # 'v' fit
plt.rcParams['keymap.save'] = '$'      # 's' to save g-code, not figure
plt.rcParams['keymap.zoom'] = 'z'
plt.rcParams['figure.figsize'] = [12, 8]

ofn = []  if len(sys.argv) < 2  else sys.argv[1]

nfile_saved = False
while True:
    gplot(ofn)
    if nfile_saved:
        ofn = NewFname
        nfile_saved = False   # new plot
    else:
        break   # exit as plot closed w/o new data

