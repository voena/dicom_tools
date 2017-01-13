#!/usr/bin/python
import ROOT
import numpy as np
import glob
import argparse
from dicom_tools.roiFileHandler import roiFileHandler
import os
from dicom_tools.FileReader import FileReader
import dicom_tools.pyqtgraph as pg

inpath="."
outfname="max-roi.txt"
myroifilename="myroi.myroi"

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-i", "--inputpath", help="path of the DICOM directory (default ./)")
parser.add_argument("-r", "--roi", help="path of the myroi file (default ./myroi.myroi")
parser.add_argument("-o", "--outfile", help="define output file name (default ./max-roi.txt)")
args = parser.parse_args()

if args.inputpath:
    inpath = args.inputpath

if args.roi:
    myroifilename = args.roi

if args.outfile:
    outfname = args.outfile    

out_file = open(outfname,"w")
out_file.write("#layer \t max \t meaninroi \n")
    
freader = FileReader(inpath, False, args.verbose)
data, unusedROI = freader.read(True)

roireader = roiFileHandler()
rois, roisSetted = roireader.read(myroifilename)

nFette = len(data)
if nFette != len(rois):
    print("error: len rois = ",len(rois)," but len dicom=",nFette)

roi = pg.PolyLineROI([[80, 60], [90, 30], [60, 40]], pen=(6,9), closed=True)    
    
for layer in xrange(0,nFette):
    fetta = data[layer]
    roi.setState(rois[layer])
    img1a = pg.ImageItem()
    img1a.setImage(fetta)
    thisroi = roi.getArrayRegion(fetta, img1a).astype(float)

    maximum = fetta.max()
    meaninroi = thisroi.mean()
    out_file.write(str(layer)+"\t"+str(maximum)+"\t"+str(meaninroi)+"\n")

out_file.close()
