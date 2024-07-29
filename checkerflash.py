#!/usr/bin/env python
#
#       $Author: frederic $
#       $Date: 2013/01/10 15:04:13 $
#       $Id: checkerflash.py,v 1.2 2013/01/10 15:04:13 frederic Exp $
#
# rotate flashing wedge
from psychopy import visual, event, core, gui
import numpy as np
from psychopy.hardware.emulator import SyncGenerator
from psychopy_visionscience.radial import RadialStim

MAXLINES = 10000


def drawcurrent(starttime, contrastvalue, flashPeriod, stim):
    t = globalClock.getTime()
    flickerphase = ((t - starttime) / flashPeriod) % 1.0
    print(flickerphase, contrastvalue)
    if (flickerphase) < (0.5):  # (NB more accurate to use number of frames)
        stim.setColor(contrasttvalue)
    else:
        stim.setColor(-contrasttvalue)


def makewedge(thecolor, thecolorspace):
    thewedge = RadialStim(
        win,
        tex="sqrXsqr",
        color=thecolor,
        size=2.0,
        units="height",
        visibleWedge=[0, 360],
        radialCycles=radcycs,
        colorSpace=thecolorspace,
        angularCycles=angcycs,
        interpolate=False,
        autoLog=False,
    )  # this stim changes too much for autologging to be useful
    return thewedge


def readvecs(inputfilename):
    file = open(inputfilename)
    lines = file.readlines(MAXLINES)
    numvecs = len(lines[0].split())
    inputvec = np.zeros((numvecs, MAXLINES), dtype="float")

    numvals = 0
    for line in lines:
        numvals = numvals + 1
        thetokens = line.split()
        for vecnum in range(0, numvecs):
            inputvec[vecnum, numvals - 1] = float(thetokens[vecnum])
    return 1.0 * inputvec[:, 0:numvals]


# settings for launchScan:
MR_settings = {"TR": 2.000, "volumes": 5, "sync": "t", "skip": 0, "sound": True}
# infoDlg = gui.DlgFromDict(MR_settings, title='fMRI parameters', order=['TR','volumes'])
# if not infoDlg.OK: core.quit()

win = visual.Window([1440, 900], allowGUI=False, fullscr=True)

# set some global values here
radcycs = 6
angcycs = 8
valarray = readvecs("/Users/frederic/code/checkerflash/timefile4")
print(valarray)

globalClock = core.Clock()
# win = visual.Window([1440,900], allowGUI=False)
# make two wedges (in opposite contrast) and alternate them for flashing
thewedge = makewedge((1.0, 1.0, 1.0), "rgb")
fp = visual.Circle(win, radius=0.01, units="height")
fp.setFillColor((0, 0.5, 0))
fp.setLineColor((0, 0.5, 0))

t = 0
contrasttvalue = 0
frequencyvalue = 8.0
flashPeriod = 1.0 / frequencyvalue  # seconds for one B-W cycle (ie 1/Hz)
flickerstartphase = 0.0
starttime = 0.0

stim = thewedge

for i in range(0, len(valarray[0, :])):
    nexttime = valarray[0, i]
    # print("will show contrast ",contrasttvalue," until t=",nexttime, " with frequency ",frequencyvalue)
    while t < nexttime:  # for 5 secs
        t = globalClock.getTime()
        flickerphase = flickerstartphase + (t - starttime) / flashPeriod
        print(flickerphase)
        if (flickerphase % 1) < (0.5):  # (NB more accurate to use number of frames)
            stim.setColor(contrasttvalue)
        else:
            stim.setColor(-contrasttvalue)
        stim.draw()
        fp.draw()
        win.flip()
    flickerstartphase = flickerstartphase + (nexttime - starttime) / flashPeriod
    starttime = nexttime
    contrasttvalue = valarray[1, i]
    if len(valarray[:, 0]) == 3:
        frequencyvalue = valarray[2, i]
        flashPeriod = 1.0 / valarray[2, i]


win.close()
