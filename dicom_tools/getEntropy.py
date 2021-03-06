import numpy as np
from skimage.filters.rank import entropy as skim_entropy
from skimage.morphology import disk as skim_disk
from skimage.morphology import square as skim_square
from skimage import exposure
import ROOT
from dicom_tools.histFromArray import histFromArray

def getEntropy(image, ROI=None, square_size=5, verbose=False):
    image = exposure.rescale_intensity(image, in_range='uint16')
    if ROI is None:
        entropyImg = skim_entropy(image,skim_square(square_size))
    else:
        entropyImg = skim_entropy(image,skim_square(square_size), mask=ROI)
    return entropyImg


def make_histo_entropy(data, ROI, suffix="", verbose=False):
    entropy3D = np.zeros( tuple([len(data)])+data[0,:,:].shape)
    for layer in xrange(0,len(data)):
        entropy3D[layer] = getEntropy(data[layer], ROI[layer])
    
    # his = ROOT.TH1F("entropy"+suffix,"entropy",nbin,binmin,binmax)
    # nbin = 10000
    # binmin=entropy3D.min() *0.8
    # binmax=entropy3D.max() *1.2
    if verbose:
        print("getEntropy creating histogram","hEntropy"+suffix)
    his = histFromArray(data, name="hEntropy"+suffix, verbose=verbose)        
    allhistos = []
    
    for i, layer in enumerate(entropy3D):
        if verbose:
            print("getEntropy creating histogram","hEntropy"+str(i)+suffix)        
        thishisto = histFromArray(layer, name="hEntropy"+str(i)+suffix)
        if thishisto is not None:
            allhistos.append(thishisto)


    return his, allhistos
