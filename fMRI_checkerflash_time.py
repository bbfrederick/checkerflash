#!/usr/bin/env python
#
#       $Author: frederic $
#       $Date: 2013/01/10 22:16:36 $
#       $Id: fMRI_checkerflash.py,v 1.3 2013/01/10 22:16:36 frederic Exp $
#

"""This demo illustrates using hardware.emulator.launchScan() to either start a real scan, 
or emulate sync pulses and user responses. Emulation is to allow debugging script timing
offline, without requiring either a scanner or a hardware sync pulse emulator.
"""

__author__ = "Jeremy Gray"

from psychopy import visual, event, core, gui
from psychopy.hardware.emulator import launchScan
import numpy as np

################################################
# Configurable parameters
initpath = "/Users/frederic/code/checkerflash"
initfile = "flash.fstim"
debug = True  # turn on counter in upper righthand corner

MAXLINES = 10000


def drawcurrent(starttime, contrastvalue, flashPeriod):
    flickerphase = ((globalClock.getTime() - starttime) / flashPeriod) % 1.0
    if (flickerphase) < (0.5):  # (NB more accurate to use number of frames)
        return contrastvalue
    else:
        return -contrastvalue


def makewedge(thecolor, thecolorspace):
    thewedge = visual.RadialStim(
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


# execution starts here

# settings for launchScan:
MR_settings = {
    "TR": 0.4,  # duration (sec) per volume
    "volumes": 588,  # number of whole-brain 3D volumes / frames
    "sync": "t",  # character to use as the sync timing event; assumed to come at start of a volume
    "skip": 0,  # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    "sound": False,  # in test mode only, play a tone as a reminder of scanner noise
}

print("MR_settings initialization is done")
infoDlg = gui.DlgFromDict(MR_settings, title="fMRI parameters", order=["TR", "volumes"])
if not infoDlg.OK:
    core.quit()

filename = gui.fileOpenDlg(
    tryFilePath=initpath, tryFileName=initfile, allowed="*.fstim"
)
if not filename:
    core.quit()
valarray = readvecs(filename[0])

win = visual.Window(
    [1024, 768], fullscr=True
)  # this has been moved up to the stimulus definition
globalClock = core.Clock()

# summary of run timing, for each key press:
output = "vol    onset key\n"
for i in range(-1 * MR_settings["skip"], 0):
    output += "%d prescan skip (no sync)\n" % i

key_code = MR_settings["sync"]
if debug:
    counter = visual.TextStim(win, height=0.05, pos=(0.8, 0.95), color=win.rgb + 0.5)
    counter.setText("")
pause_during_delay = MR_settings["TR"] > 0.3
sync_now = False

# can simulate user responses, here 3 key presses in order 'a', 'b', 'c' (they get sorted by time):
simResponses = []

infer_missed_sync = False  # best if your script timing works without this, but this might be useful sometimes
max_slippage = 0.02  # how long to allow before treating a "slow" sync as missed
# any slippage is almost certainly due to timing issues with your script or PC, and not MR scanner

# initialize our specific protocol here (checkerflash)
# set some stimulus values here
radcycs = 6
angcycs = 8
print(valarray)

# make two wedges (in opposite contrast) and alternate them for flashing
thewedge = makewedge((1.0, 0.0, 0.0), "rgb")
fixation = visual.Circle(win, radius=0.01, units="height")
fixation.setFillColor((0, 0.5, 0))
fixation.setLineColor((0, 0.5, 0))

contrasttvalue = 0
frequencyvalue = 8.0
flashPeriod = 1.0 / frequencyvalue  # seconds for one B-W cycle (ie 1/Hz)
flickerstartphase = 0.0
starttime = 0.0

stim = thewedge
fp = fixation
fp.draw()

# if valarray has three columns, they are onset time, contrast value, and flicker frequency value
# if valarray has two columns, they are onset time, and contrast value (flicker frequency is set to 8.0)
# onset time is in seconds
# time starts at 0.0
onsets = valarray[0, :]
contrasts = valarray[1, :]
if len(valarray[:, 0]) == 3:
    flashPeriods = valarray[2, :]
else:
    flashPeriods = contrasts * 0.0 + 1.0 / 8.0

# note: globalClock has been reset to 0.0 by launchScan()
starttime = 0.0
if onsets[0] == 0.0:
    # there is an initial startup value, use that
    contrastvalue = contrasts[0]
    flashPeriod = flashPeriods[0]
    whichstim = 1
else:
    # there is no initial startup value, infer that contrast is zero
    contrastvalue = 0.0
    flashPeriod = 1.0 / 8.0
    whichstim = 0

print("checkerflash initialization is done")

duration = MR_settings["volumes"] * MR_settings["TR"]

thecontrastvalue = drawcurrent(starttime, contrastvalue, flashPeriod)
stim.setColor(thecontrastvalue)
win.flip()
vol = 0
onset = 0.0

# launch: operator selects Scan or Test (emulate); see API documentation
vol = launchScan(
    win, MR_settings, globalClock=globalClock, simResponses=simResponses, wait_msg=""
)
starttime = 0.0
contrastvalue = contrasts[vol - 1]
flashPeriod = flashPeriods[vol - 1]
sync_now = "Experiment start"

numtriggers = 0

print("entering main loop with whichstim =", whichstim)
while globalClock.getTime() < duration:
    allKeys = event.getKeys()
    if "escape" in allKeys:
        output += "user cancel, "
        break
    # detect scanner triggers and record their arrival times
    if MR_settings["sync"] in allKeys:
        triggertime = globalClock.getTime()
        numtriggers += 1
    if globalClock.getTime() >= onsets[whichstim]:
        # do your experiment code at this point; for demo, just shows a counter & time
        print("reached onset number ", whichstim, " at time ", globalClock.getTime())
        starttime = 0.0
        contrastvalue = contrasts[whichstim]
        flashPeriod = flashPeriods[whichstim]
        if debug:
            counter.setText("Volume number: %d\n%.3f seconds" % (numtriggers, onset))
        output += "%3d  %7.3f %s\n" % (vol, onset, sync_now)
        if whichstim < len(onsets):
            whichstim += 1
    # now draw whatever we are drawing
    thecontrastvalue = drawcurrent(starttime, contrastvalue, flashPeriod)
    stim.setColor(thecontrastvalue)
    stim.draw()
    fp.draw()
    if debug:
        counter.draw()
    win.flip()

output += "end of scan (vol 0..%d = %d of %s). duration = %7.3f" % (
    vol,
    MR_settings["volumes"],
    MR_settings["sync"],
    globalClock.getTime(),
)
print(output)
print(
    "For the test, there should be 5 trials (vol 0..4, key 5), with three simulated subject responses (a, b, c)"
)
core.quit()