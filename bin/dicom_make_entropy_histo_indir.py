#!/usr/bin/python
from __future__ import print_function
import os
import glob
import argparse
import numpy as np
import dicom
import sys
from dicom_tools.make_histo import make_histo
# from dicom_tools.read_files import read_files
from dicom_tools.FileReader import FileReader
import ROOT
from array import array
from dicom_tools.myroi2roi import myroi2roi
from dicom_tools.info_file_parser import info_file_parser
from dicom_tools.timeflagconverter import timeflagconverter_string2int
from dicom_tools.getEntropy import make_histo_entropy

outfname="out.root"

parser = argparse.ArgumentParser()
parser.add_argument("inputdirecotry", help="path of the input direcotry")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-o", "--outfile", help="define output file name (default out.root)")
parser.add_argument("-jo", "--justone", help="limit the analisys to one subdirecotry")
parser.add_argument("-n", "--norm", help="normalize to the mean defined in a myroi file",
                    action="store_true")

args = parser.parse_args()

if args.outfile:
    outfname = args.outfile

inputdir = args.inputdirecotry

if args.verbose:
    print("Verbose\n")

    
outfile = ROOT.TFile(outfname,"RECREATE")
patientID= bytearray(64)
timeflag = array('i', [0])
nVoxel   = array('i', [0])
ypT      = array('i', [0])
mean     = array('f', [0])
stdDev   = array('f', [0])
skewness = array('f', [0])
kurtosis = array('f', [0])
entropy_mean = array('f', [0])
entropy_var = array('f', [0])

nmax = 100
nFette   = array('i', [0])

nVoxelPF   = array('i', nmax*[0])
meanPF     = array('f', nmax*[0])
stdDevPF   = array('f', nmax*[0])
skewnessPF = array('f', nmax*[0])
kurtosisPF = array('f', nmax*[0])
entropy_meanPF = array('f', nmax*[0])
entropy_varPF = array('f', nmax*[0])

tree = ROOT.TTree("analisi_T2","analisi_T2")
tree.Branch("patientID",patientID,"patientID/C")
tree.Branch("timeflag",timeflag,"timeflag/I")
tree.Branch("nVoxel",nVoxel,"nVoxel/I")
tree.Branch("ypT",ypT,"ypT/I")
tree.Branch("mean",mean,"mean/F")
tree.Branch("stdDev",stdDev,"stdDev/F")
tree.Branch("skewness",skewness,"skewness/F")
tree.Branch("kurtosis",kurtosis,"kurtosis/F")
tree.Branch("entropy_mean",entropy_mean,"entropy_mean/F")
tree.Branch("entropy_var",entropy_var,"entropy_var/F")

tree.Branch("nFette",nFette,"nFette/I")

tree.Branch("nVoxelPF",nVoxelPF,"nVoxelPF[nFette]/I")
tree.Branch("meanPF",meanPF,"meanPF[nFette]/F")
tree.Branch("stdDevPF",stdDevPF,"stdDevPF[nFette]/F")
tree.Branch("skewnessPF",skewnessPF,"skewnessPF[nFette]/F")
tree.Branch("kurtosisPF",kurtosisPF,"kurtosisPF[nFette]/F")
tree.Branch("entropy_meanPF",entropy_meanPF,"entropy_meanPF[nFette]/F")
tree.Branch("entropy_varPF",entropy_varPF,"entropy_varPF[nFette]/F")

patientdirs= glob.glob(inputdir+"*/")

if args.justone:
    print("Looking for dir",args.justone)

for patientdir in patientdirs:

    print(patientdir)
    if args.justone:
        if not args.justone in patientdir: continue
    
    analasisysdirs=glob.glob(patientdir+"*/")
    for analasisysdir in analasisysdirs:
        print("\t",analasisysdir)

        pathT2 = analasisysdir + "T2/"
        
        nFette[0] = 0
        if patientdir[-1]=='/':
            patID = patientdir.split('/')[-2].replace('.','')
        else:
            patID = patientdir.split('/')[-1].replace('.','')
        patientID[:63] = patID
        print("working on patient: "+patientID)
        print("in the directory: "+pathT2)
        if os.path.isdir(pathT2):
            print("T2 dir found.")
        pathROI = analasisysdir + "ROI/"
        if os.path.isdir(pathROI):
            print("ROI dir found.")

        infos = info_file_parser(analasisysdir + "info.txt")
        timeflag[0] = timeflagconverter_string2int(infos["time"])
        ypT[0] = int(infos["ypT"])
        
        #         # data, ROI = read_files(pathT2, pathROI, args.verbose, True)
        freader = FileReader(pathT2, pathROI, args.verbose)
        try:
            data, ROI = freader.read(raw=True)
        except NotImplementedError:
            data = freader.readUsingGDCM(raw=True)
            ROI = freader.readROI()
        except ValueError:
            continue
        
        roinorm=False
        
        if args.verbose:
            print("dicom file read")
            
        if args.norm:
            myroifilename = analasisysdir + "roinormmuscle.myroi"
        
            roireader = roiFileHandler(args.verbose)
            myroisnorm, roisnormSetted = roireader.read(myroifilename)
            
            roinorm = myroi2roi(myroisnorm, data.shape, args.verbose)
    
            if args.verbose:
                print("norm file read")
        if args.verbose:                
            print("data mean:",data.mean(),"min:",data.min(),"max:",data.max(),"shape:",data.shape)
            print("ROI mean:",ROI.mean(),"min:",ROI.min(),"max:",ROI.max(),"shape:",ROI.shape)

        if len(ROI) is not len(data):
            print("skipping this analysis len(data)",len(data),"len(ROI)",len(ROI))
            continue
            
        patientsuffix = patID + infos["time"]
        his, allhistos, histogiafatti = make_histo(data,ROI,patientsuffix,
                                                   args.verbose,roinorm,args.norm)
        entropy_his, allentropy_his = make_histo_entropy(data,ROI,patientsuffix,
                                                         args.verbose)
        nVoxel[0]   = int(his.GetEntries())
        mean[0]     = his.GetMean()
        stdDev[0]   = his.GetStdDev()
        skewness[0] = his.GetSkewness()
        kurtosis[0] = his.GetKurtosis()

        entropy_mean[0] = entropy_his.GetMean()
        entropy_var[0]  = entropy_his.GetStdDev()
        
        if args.verbose:
            print(patientID, timeflag[0], nVoxel[0], ypT[0], mean[0], stdDev[0], skewness[0], kurtosis[0])
        his.Write()
        entropy_his.Write()
        
        for thishisto in allhistos:
            if thishisto.GetEntries() >0:
                nVoxelPF[nFette[0]]   = int(thishisto.GetEntries())
                meanPF[nFette[0]]     = thishisto.GetMean()
                stdDevPF[nFette[0]]   = thishisto.GetStdDev()  
                skewnessPF[nFette[0]] = thishisto.GetSkewness()
                kurtosisPF[nFette[0]] = thishisto.GetKurtosis()
                
                nFette[0] +=1
                thishisto.Write()

        for n in range(0,len(allentropy_his)):
            thishisto = allentropy_his[n]
            if thishisto.GetEntries() >0:
                entropy_meanPF[n] = thishisto.GetMean()
                entropy_varPF[n] = thishisto.GetStdDev()                
                thishisto.Write()
                
        for thishisto in histogiafatti:
                thishisto.Write()
        if args.verbose:
            print(patientID, nFette[0])
        tree.Fill()
                
tree.Write()            
# outfile.Write()
outfile.Close()
