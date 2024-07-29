#!/usr/bin/env python
#
#       $Author: frederic $
#       $Date: 2013/01/10 15:04:13 $
#       $Id: fMRI_checkerflash.py,v 1.2 2013/01/10 15:04:13 frederic Exp $
#

"""This demo illustrates using hardware.emulator.launchScan() to either start a real scan, 
or emulate sync pulses and user responses. Emulation is to allow debugging script timing
offline, without requiring either a scanner or a hardware sync pulse emulator.
"""

__author__ = "Jeremy Gray"

from psychopy import visual, event, core, gui
from psychopy.hardware.emulator import launchScan
from string import replace
import numpy as np

################################################
# Configurable parameters
initpath = "/Users/frederic/code/checkerflash"
initfile = "breath.wstim"
debug = True  # turn on counter in upper righthand corner

MAXLINES = 10000


def setword(thenewword, thestim):
    thestim.setText(thenewword)


def readwords(inputfilename):
    file = open(inputfilename)
    lines = file.readlines(MAXLINES)
    numvecs = 1
    inputvec = np.zeros((numvecs, MAXLINES), dtype="float")
    numvals = 0
    inputtimes = []
    inputwords = []
    for line in lines:
        numvals = numvals + 1
        thetokens = line.split()
        inputtimes.append(float(thetokens[0]))
        inputwords.append(replace(thetokens[1], "_", " "))
    return (inputtimes, inputwords)


# execution starts here

# settings for launchScan:
MR_settings = {
    "TR": 4.0,  # duration (sec) per volume
    "volumes": 120,  # number of whole-brain 3D volumes / frames
    "sync": "t",  # character to use as the sync timing event; assumed to come at start of a volume
    "skip": 0,  # number of volumes lacking a sync pulse at start of scan (for T1 stabilization)
    "sound": False,  # in test mode only, play a tone as a reminder of scanner noise
}
print("MR_settings initialization is done")
infoDlg = gui.DlgFromDict(MR_settings, title="fMRI parameters", order=["TR", "volumes"])
if not infoDlg.OK:
    core.quit()

filename = gui.fileOpenDlg(
    tryFilePath=initpath, tryFileName=initfile, allowed="*.wstim"
)
if not filename:
    core.quit()
inputtimes, inputwords = readwords(filename[0])


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
stimword = visual.TextStim(win, height=0.3, pos=(0.0, 0.0), color=win.rgb + 1.0)
pause_during_delay = MR_settings["TR"] > 0.3
sync_now = False

# can simulate user responses, here 3 key presses in order 'a', 'b', 'c' (they get sorted by time):
simResponses = []

infer_missed_sync = False  # best if your script timing works without this, but this might be useful sometimes
max_slippage = 0.02  # how long to allow before treating a "slow" sync as missed
# any slippage is almost certainly due to timing issues with your script or PC, and not MR scanner

whichstim = 0
# if valarray has three columns, they are onset time, contrast value, and flicker frequency value
# if valarray has two columns, they are onset time, and contrast value (flicker frequency is set to 8.0)
# onset time is in TRs
# the first TR is number 0
whichstim = 1

# for each TR, determine the word to present (one value per TR)
print("TR\tword")
words = []
currentword = inputwords[0]
numvalentries = len(inputtimes)

for i in range(0, MR_settings["volumes"]):
    # print("waiting for",int(valarray[0,whichstim]))
    if i >= int(inputtimes[whichstim]):
        currentword = inputwords[whichstim]
        if whichstim < numvalentries - 1:
            whichstim = whichstim + 1
    words.append(currentword)
    print(i, "\t", words[i])
print("wordstim initialization is done")

duration = MR_settings["volumes"] * MR_settings["TR"]
# launch: operator selects Scan or Test (emulate); see API documentation
vol = launchScan(
    win, MR_settings, globalClock=globalClock, simResponses=simResponses, wait_msg=""
)  # note: globalClock has been reset to 0.0 by launchScan()
setword(words[0], stimword)
stimword.draw()
win.flip()
vol = 0
onset = 0.0

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
        if debug:
            counter.setText("Volume number: %d\n%.3f seconds" % (vol, onset))
        output += "%3d  %7.3f %s\n" % (vol, onset, sync_now)
        vol += 1
        sync_now = False
    # now draw whatever we are drawing
    setword(words[vol], stimword)
    stimword.draw()
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
