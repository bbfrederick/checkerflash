#!/usr/bin/env python
#
#       $Author: frederic $
#       $Date: 2013/11/06 15:40:52 $
#       $Id: showtc,v 1.5 2013/11/06 15:40:52 frederic Exp $
#
import sys
import matplotlib

matplotlib.use("MacOSX")
from scipy import arange
from numpy import zeros

from pylab import plot, legend, show, hold

MAXLINES = 100000
MAXCHARS = MAXLINES * 100


def writevec(thevec, outputfile):
    FILE = open(outputfile, "w")
    for i in thevec:
        FILE.writelines(str(i) + "\n")
    FILE.close()


def readvecs(inputfilename):
    file = open(inputfilename)
    lines = file.readlines(MAXCHARS)
    numvecs = len(lines[0].split())
    inputvec = zeros((numvecs, MAXLINES), dtype="float")

    numvals = 0
    for line in lines:
        numvals = numvals + 1
        thetokens = line.split()
        for vecnum in range(0, numvecs):
            inputvec[vecnum, numvals - 1] = float(thetokens[vecnum])
    return 1.0 * inputvec[:, 0:numvals]


def usage():
    print("usage: genwave infilename outfilename numtr")
    print("	generates the regressor from an .fstim file")
    print("")
    print("required arguments:")
    print("	infilename	- an fstim file containing")
    print("	outfilename	- a text file containing one TR per line")
    print("	numtr   	- the last TR of the output file")
    return ()


# get the command line parameters
nargs = len(sys.argv)
if nargs < 4:
    usage()
    exit()

# set default variable values
dolegend = True

# handle required args first
textfilename = sys.argv[1]
outfilename = sys.argv[2]
numtrs = int(sys.argv[3])

lastpoint = 0
lastval = 0.0
inputvals = readvecs(textfilename)
numpoints = len(inputvals[0, :])
outputvec = zeros((numtrs), dtype="float")

print(numpoints, " points, ", numtrs, " trs")
for i in range(0, numpoints):
    theval = inputvals[1, i]
    outputvec[lastpoint : inputvals[0, i]] = lastval
    lastval = theval
    lastpoint = inputvals[0, i]
outputvec[lastpoint:numtrs] = lastval

writevec(outputvec, outfilename)
plot(outputvec)
show()
