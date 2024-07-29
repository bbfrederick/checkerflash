#!/usr/bin/env python
#
#       $Author: frederic $
#       $Date: 2014/01/29 16:36:05 $
#       $Id: fMRI_checkerflash_LMS.py,v 1.1 2014/01/29 16:36:05 frederic Exp $
#

"""This demo illustrates using hardware.emulator.launchScan() to either start a real scan, 
or emulate sync pulses and user responses. Emulation is to allow debugging script timing
offline, without requiring either a scanner or a hardware sync pulse emulator.
"""

__author__ = "Jeremy Gray"

from psychopy import misc, visual, event, core, gui, data, monitors
from psychopy.hardware.emulator import launchScan
import numpy as np

################################################
# Configurable parameters
initpath = "/Users/frederic/code/checkerflash"
initfile = "flash.fstim"
debug = False  # turn on counter in upper righthand corner

MAXLINES = 10000


def drawcurrent(starttime, contrastvalueL, contrastvalueM, contrastvalueS, flashPeriod):
    flickerphase = ((globalClock.getTime() - starttime) / flashPeriod) % 1.0
    if (flickerphase) < (0.5):  # (NB more accurate to use number of frames)
        return (1.0 * contrastvalueL, 1.0 * contrastvalueM, 1.0 * contrastvalueS)
    else:
        return (-1.0 * contrastvalueL, -1.0 * contrastvalueM, -1.0 * contrastvalueS)


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
    "TR": 0.52,  # duration (sec) per volume
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
    [1024, 768], fullscr=False
)  # this has been moved up to the stimulus definition
globalClock = core.Clock()

# summary of run timing, for each key press:
output = "vol    onset key\n"
for i in range(-1 * MR_settings["skip"], 0):
    output += "%d prescan skip (no sync)\n" % i

key_code = MR_settings["sync"]
if debug:
    counter = visual.TextStim(win, height=0.05, pos=(0.8, 0.95), color=win.lms + 0.5)
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
thewedge = makewedge((1.0, 1.0, 1.0), "lms")
fixation = visual.Circle(win, radius=0.01, units="height")
fixation.setFillColor((0, 0.5, 0))
fixation.setLineColor((0, 0.5, 0))

contrasttvalueL = 0
contrasttvalueM = 0
contrasttvalueS = 0
frequencyvalue = 8.0
flashPeriod = 1.0 / frequencyvalue  # seconds for one B-W cycle (ie 1/Hz)
flickerstartphase = 0.0
starttime = 0.0
longfac = 0.2
medfac = 0.2
shortfac = 0.8

stim = thewedge
fp = fixation
fp.draw()

# turn valarray into a list of values for each TR
flashPeriods = np.zeros((MR_settings["volumes"]), dtype="float")
contrastsL = np.zeros((MR_settings["volumes"]), dtype="float")
contrastsM = np.zeros((MR_settings["volumes"]), dtype="float")
contrastsS = np.zeros((MR_settings["volumes"]), dtype="float")

whichstim = 0
currentcontrastL = valarray[1, whichstim]
currentcontrastM = valarray[2, whichstim]
currentcontrastS = valarray[3, whichstim]
# if valarray has five columns, they are onset time, contrast L, contrast M,  contrast S, and flicker frequency value
# if valarray has four columns, they are onset time,  contrast L, contrast M, and contrast S (flicker frequency is set to 8.0)
# onset time is in TRs
# the first TR is number 0
if len(valarray[:, 0]) == 5:
    currentflashPeriod = 1.0 / valarray[4, whichstim]
else:
    currentflashPeriod = 1.0 / 8.0
whichstim = 1
numvalentries = len(valarray[0, :])

# for each TR, determine the contrast and flicker frequency (one value per TR)
print("TR\tcontrast\tflashperiod")
for i in range(0, MR_settings["volumes"]):
    # print("waiting for",int(valarray[0,whichstim]))
    if i >= int(valarray[0, whichstim]):
        currentcontrastL = valarray[1, whichstim]
        currentcontrastM = valarray[2, whichstim]
        currentcontrastS = valarray[3, whichstim]
        if len(valarray[:, 0]) == 5:
            currentflashPeriod = 1.0 / valarray[4, whichstim]
        else:
            currentflashPeriod = 1.0 / 8.0
        if whichstim < numvalentries - 1:
            whichstim = whichstim + 1
    contrastsL[i] = currentcontrastL
    contrastsM[i] = currentcontrastM
    contrastsS[i] = currentcontrastS
    flashPeriods[i] = currentflashPeriod
    print(
        i,
        "\t",
        contrastsL[i],
        "\t",
        contrastsM[i],
        "\t",
        contrastsS[i],
        "\t",
        flashPeriods[i],
    )
print("checkerflash initialization is done")

duration = MR_settings["volumes"] * MR_settings["TR"]
# note: globalClock has been reset to 0.0 by launchScan()
starttime = 0.0
contrastvalueL = contrastsL[0]
contrastvalueM = contrastsM[0]
contrastvalueS = contrastsS[0]
flashPeriod = flashPeriods[0]
thecontrastvalueL, thecontrastvalueM, thecontrastvalueS = drawcurrent(
    starttime, contrastvalueL, contrastvalueM, contrastvalueS, flashPeriod
)
print(thecontrastvalueL, thecontrastvalueM, thecontrastvalueS)
stim.setColor(
    (
        longfac * thecontrastvalueL,
        medfac * thecontrastvalueM,
        shortfac * thecontrastvalueS,
    )
)
win.flip()
vol = 0
onset = 0.0

# launch: operator selects Scan or Test (emulate); see API documentation
vol = launchScan(
    win, MR_settings, globalClock=globalClock, simResponses=simResponses, wait_msg=""
)
starttime = 0.0
contrastvalueL = contrastsL[vol - 1]
contrastvalueM = contrastsM[vol - 1]
contrastvalueS = contrastsS[vol - 1]
flashPeriod = flashPeriods[vol - 1]
sync_now = "Experiment start"

while globalClock.getTime() < duration:
    allKeys = event.getKeys()
    if "escape" in allKeys:
        output += "user cancel, "
        break
    # detect sync or infer it should have happened:
    if MR_settings["sync"] in allKeys:
        sync_now = key_code  # flag
        onset = globalClock.getTime()
    if infer_missed_sync:
        expected_onset = vol * MR_settings["TR"]
        now = globalClock.getTime()
        if now > expected_onset + max_slippage:
            sync_now = "(inferred onset)"  # flag
            onset = expected_onset
    if sync_now:
        # do your experiment code at this point; for demo, just shows a counter & time
        starttime = 0.0
        contrastvalueL = contrastsL[vol]
        contrastvalueM = contrastsM[vol]
        contrastvalueS = contrastsS[vol]
        flashPeriod = flashPeriods[vol]
        if debug:
            counter.setText("Volume number: %d\n%.3f seconds" % (vol, onset))
        output += "%3d  %7.3f %s\n" % (vol, onset, sync_now)

        vol += 1
        sync_now = False
    # now draw whatever we are drawing
    thecontrastvalueL, thecontrastvalueM, thecontrastvalueS = drawcurrent(
        starttime, contrastvalueL, contrastvalueM, contrastvalueS, flashPeriod
    )
    print(1.0 * thecontrastvalueL, 1.0 * thecontrastvalueM, 1.0 * thecontrastvalueS)
    stim.setColor(
        (
            longfac * thecontrastvalueL,
            medfac * thecontrastvalueM,
            shortfac * thecontrastvalueS,
        )
    )
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
