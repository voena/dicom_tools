#!/usr/bin/python
import glob
import argparse
import numpy as np
from dicom_tools.pyqtgraph.Qt import QtCore, QtGui
import dicom_tools.pyqtgraph as pg
import dicom
from dicom_tools.FileReader import FileReader
from scipy import ndimage
import os
import nrrd
from dicom_tools.roiFileHandler import roiFileHandler
from dicom_tools.nrrdFileHandler import nrrdFileHandler
from dicom_tools.highlight_color import highlight_color
from dicom_tools.Normalizer import Normalizer
from dicom_tools.myroi2roi import myroi2roi
from dicom_tools.calculateMeanInROI import calculateMeanInROI
import scipy
from dicom_tools.curvatureFlowImageFilter import curvatureFlowImageFilter
from dicom_tools.connectedThreshold import connectedThreshold

class AboutWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)

        self.closeButton = QtGui.QPushButton(self.tr("&Close"))
        self.closeButton.setDefault(True)
        
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.addButton(self.closeButton, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        # self.closeButton.connect(self.o)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL("clicked()"), self.o)

        
        self.textBrowser = QtGui.QTextBrowser(self)
        self.textBrowser.append("DICOM tool (v2.0)")
        self.textBrowser.append("carlo.mancini.terracciano@roma1.infn.it")

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.textBrowser)
        self.verticalLayout.addWidget(self.buttonBox)

    def o(self):
        # print("close the window") 
        self.close()
        
# class Window(QtGui.QWidget):
class Window_dicom_tool(QtGui.QMainWindow): 

    def __init__(self):
        # QtGui.QWidget.__init__(self)
        super(Window_dicom_tool, self).__init__()
        # self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("DICOM tool (v2.0)")
        # self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        widgetWindow = QtGui.QWidget(self)
        self.setCentralWidget(widgetWindow)
        
        outfname="roi.txt"
        self.inpath="."        
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", help="increase output verbosity",
                            action="store_true")
        parser.add_argument("-i", "--inputpath", help="path of the DICOM directory (default ./)")
        parser.add_argument("-o", "--outfile", help="define output file name (default roi.txt)")
        parser.add_argument("-l", "--layer", help="select layer",
                            type=int)
        parser.add_argument("-f", "--filterROI", help="filter the image with a ROI (folder path, nrrd file supported)")
        parser.add_argument("-c","--colorRange", help="highlight a color range (expects sometghin like 100:200)")
        parser.add_argument("-r","--raw", help="do not normalize",action="store_true")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-y", "--yview", help="swap axes",
                           action="store_true")
        group.add_argument("-x", "--xview", help="swap axes",
                           action="store_true")
        
        args = parser.parse_args()
        self.layer=0
        self.layerZ=0
        self.layerX=0
        self.layerY=0        
        self.verbose = args.verbose
        self.xview = args.xview
        self.yview = args.yview
        self.zview = not self.xview and not self.yview
        self.imgScaleFactor = 1
        
        if args.outfile:
            outfname = args.outfile
            
            
        if args.layer:
            self.layer = args.layer

        openDicomDirectory = QtGui.QAction("&Open DICOM Directory", self)
        openDicomDirectory.setShortcut("Ctrl+O")
        openDicomDirectory.setStatusTip("Open DICOM Directory (dcm uncompressed)")
        openDicomDirectory.triggered.connect(self.select_dicom_folder)
            
        # openDicomFile = QtGui.QAction("&Open DICOM File", self)
        # openDicomFile.setStatusTip("Open DICOM File (dcm uncompressed)")
        # openDicomFile.triggered.connect(self.read_dicom_file)
        
        openDicomDirectoryGDCM = QtGui.QAction("&Open DICOM Directory with GDCM", self)
        openDicomDirectoryGDCM.setStatusTip("Open DICOM Directory with GDCM (dcm also compressed)")
        openDicomDirectoryGDCM.triggered.connect(self.select_dicom_folderGDCM)    
        
        openMyROIFile = QtGui.QAction("&Open MyROI File", self)
        # openFile.setShortcut("Ctrl+O")
        openMyROIFile.setStatusTip('Open ROI File (myroi format)')
        openMyROIFile.triggered.connect(self.myroi_file_open)
        
        saveMyROIFile = QtGui.QAction("&Save ROI on File", self)
        saveMyROIFile.setShortcut("Ctrl+S")
        saveMyROIFile.setStatusTip('Save ROI on File (myroi format)')
        saveMyROIFile.triggered.connect(self.myroi_file_save)

        saveROIonNRRD = QtGui.QAction("&Save ROI on nrrd File", self)
        saveROIonNRRD.setStatusTip('Save ROI on File (nrrd format)')
        saveROIonNRRD.triggered.connect(self.nrrdroi_file_save)

        highlightnrrdROIaction = QtGui.QAction("&Highlight nrrd ROI", self)
        highlightnrrdROIaction.setStatusTip("&Highlight ROI (nrrd file)")
        highlightnrrdROIaction.triggered.connect(self.highlightnrrdROI)
        
        highlightMyROIaction = QtGui.QAction("&Highlight myroi ROI", self)
        highlightMyROIaction.setStatusTip("&Highlight ROI (myroi file)")
        highlightMyROIaction.triggered.connect(self.highlightMyROI)        
        
        # self.statusBar()
        normalizeHistogramMatching = QtGui.QAction("&Normalize using hm", self)
        # normalizeHistogramMatching.setShortcut("Ctrl+O")
        normalizeHistogramMatching.setStatusTip('Normalize using histogram matching')
        normalizeHistogramMatching.triggered.connect(self.histogram_matching_normalization)

        normalizeToROIAction = QtGui.QAction("&Normalize to ROI", self)
        normalizeToROIAction.setStatusTip("&Normalize to a ROI (myroi file)")
        normalizeToROIAction.triggered.connect(self.normalizeToROI)
        
        switchToZViewAction = QtGui.QAction("&Switch to Z view", self)
        switchToZViewAction.setStatusTip('Switch to Z view')
        switchToZViewAction.triggered.connect(self.switchToZView)
        
        switchToXViewAction = QtGui.QAction("&Switch to X view", self)
        switchToXViewAction.setStatusTip('Switch to X view')
        switchToXViewAction.triggered.connect(self.switchToXView)

        switchToYViewAction = QtGui.QAction("&Switch to Y view", self)
        switchToYViewAction.setStatusTip('Switch to Y view')
        switchToYViewAction.triggered.connect(self.switchToYView)

        saveToTiffAction = QtGui.QAction("&Save to TIFF", self)
        saveToTiffAction.setStatusTip('Save current view to TIFF file')
        saveToTiffAction.triggered.connect(self.saveToTIFFImage)
        saveToPngAction = QtGui.QAction("&Save to PNG", self)
        saveToPngAction.setStatusTip('Save current view to PNG file')
        saveToPngAction.triggered.connect(self.saveToPNGImage)        

        histoOfAllLayerAction = QtGui.QAction("&Histogram of all layer" ,self)
        histoOfAllLayerAction.setStatusTip('Histogram of all layer')
        histoOfAllLayerAction.triggered.connect(self.histoOfAllLayer)

        aboutAction = QtGui.QAction("&About this program", self)
        aboutAction.setStatusTip('About this program')
        aboutAction.triggered.connect(self.about)

        CurvatureFlowImageFilterAction = QtGui.QAction("&Apply Curvature Flow Filter",self)
        CurvatureFlowImageFilterAction.setStatusTip("Apply Curvature Flow Filter")
        CurvatureFlowImageFilterAction.triggered.connect(self.CurvatureFlowImageFilter)
        
        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(openDicomDirectory)
        fileMenu.addAction(openDicomDirectoryGDCM)
        
        ROIfileMenu = mainMenu.addMenu('&ROI')
        # fileMenu.addAction(extractAction)
        ROIfileMenu.addAction(openMyROIFile)
        ROIfileMenu.addAction(saveMyROIFile)
        ROIfileMenu.addAction(saveROIonNRRD)
        ROIfileMenu.addAction(highlightnrrdROIaction)
        ROIfileMenu.addAction(highlightMyROIaction)        
        
        normMenu = mainMenu.addMenu('&Normalization')
        normMenu.addAction(normalizeHistogramMatching)
        normMenu.addAction(normalizeToROIAction)

        viewMenu = mainMenu.addMenu('&View')
        viewMenu.addAction(switchToZViewAction)
        viewMenu.addAction(switchToXViewAction)
        viewMenu.addAction(switchToYViewAction)

        imageMenu = mainMenu.addMenu('&Image')
        imageMenu.addAction(saveToTiffAction)
        imageMenu.addAction(saveToPngAction)        

        analysisMenu = mainMenu.addMenu('&Analysis')
        analysisMenu.addAction(histoOfAllLayerAction)

        filtersMenu = mainMenu.addMenu('&Filters')
        filtersMenu.addAction(CurvatureFlowImageFilterAction)
        filtersMenu.addAction(aboutAction)
        
        helpMenu = mainMenu.addMenu('&Help')
        helpMenu.addAction(aboutAction)
        
        # if not args.raw:
        #     thisNormalizer = Normalizer(self.verbose)
        #     thisNormalizer.setRootOutput()
        #     self.dataZ = thisNormalizer.match_all(dataRGB)
        #     thisNormalizer.writeRootOutputOnFile("checkNorm.root")
        # else:

        
        if args.colorRange:
            self.dataZ = highlight_color(dataRGB,args.colorRange,args.verbose)
        

        self.img1a = pg.ImageItem()
        self.arr = None
        self.firsttime = True            
            
        self.button_next = QtGui.QPushButton('Next', self)
        self.button_prev = QtGui.QPushButton('Prev', self)
        self.button_next.clicked.connect(self.nextimg)
        self.button_prev.clicked.connect(self.previmg)
        # layout = QtGui.QVBoxLayout(self)
        # layout = QtGui.QGridLayout(self)
        layout = QtGui.QGridLayout(widgetWindow)
        layout.addWidget(self.button_next,1,1)
        layout.addWidget(self.button_prev,2,1)
        self.button_setroi = QtGui.QPushButton('Set ROI', self)
        self.button_setroi.clicked.connect(self.setROI)
        layout.addWidget(self.button_setroi,12,1)
        self.button_delroi = QtGui.QPushButton('Del ROI', self)
        self.button_delroi.clicked.connect(self.delROI)
        layout.addWidget(self.button_delroi,13,1)
        
        label = QtGui.QLabel("Click on a line segment to add a new handle. Right click on a handle to remove.")        
        # label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label,0,0)    

        self.label_layer = QtGui.QLabel("layer: ")
        self.label_shape = QtGui.QLabel("shape: ")
        self.label_size = QtGui.QLabel("size: ")
        self.label_min = QtGui.QLabel("min: ")
        self.label_max = QtGui.QLabel("max: ")
        self.label_mean = QtGui.QLabel("mean: ")
        self.label_sd = QtGui.QLabel("sd: ")
        self.label_sum = QtGui.QLabel("sum: ")
        layout.addWidget(self.label_layer,3,1)
        layout.addWidget(self.label_shape,4,1)
        layout.addWidget(self.label_size,5,1)
        layout.addWidget(self.label_min,6,1)
        layout.addWidget(self.label_max,7,1)
        layout.addWidget(self.label_mean,8,1)
        layout.addWidget(self.label_sd,9,1)
        layout.addWidget(self.label_sum,10,1)

        self.roisSetted = 0
        self.label2_roisSetted = QtGui.QLabel("ROI setted: 0")
        self.label2_shape = QtGui.QLabel()
        self.label2_size = QtGui.QLabel()
        self.label2_min = QtGui.QLabel()
        self.label2_max = QtGui.QLabel()
        self.label2_mean = QtGui.QLabel()
        self.label2_sd = QtGui.QLabel()
        self.label2_sum = QtGui.QLabel()
        layout.addWidget(self.label2_roisSetted,14,1)
        layout.addWidget(self.label2_shape,15,1)
        layout.addWidget(self.label2_size,16,1)
        layout.addWidget(self.label2_min,17,1)
        layout.addWidget(self.label2_max,18,1)
        layout.addWidget(self.label2_mean,19,1)
        layout.addWidget(self.label2_sd,20,1)
        layout.addWidget(self.label2_sum,21,1)
                                      
        self.p1 = pg.PlotWidget()
        self.p1.setAspectLocked(True,self.imgScaleFactor)
        self.p1.addItem(self.img1a)
        self.p1ViewBox = self.p1.plotItem.vb
        proxy = pg.SignalProxy(self.p1.scene().sigMouseClicked, rateLimit=60, slot=self.mouseMoved)
        self.p1.scene().sigMouseClicked.connect(self.mouseMoved)
        # imv = pg.ImageView(imageItem=img1a)
        layout.addWidget(self.p1,1,0,10,1)

        # self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider = QtGui.QScrollBar(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setValue(self.layer+1)
        self.slider.setSingleStep(1)
        self.slider.setFocus()
        self.slider.setFocusPolicy(QtCore.Qt.StrongFocus) 
        # self.slider.setTickPosition(QtGui.QSlider.TicksBelow)
        # self.slider.setTickInterval(5)

        # self.slider.sliderMoved.connect(self.slider_jump_to)
        self.slider.valueChanged.connect(self.slider_jump_to)
        layout.addWidget(self.slider,11,0)

        self.img1b = pg.ImageItem()
        self.roi = pg.PolyLineROI([[80, 60], [90, 30], [60, 40]], pen=(6,9), closed=True)
        # if self.rois[self.layer]:
        #     self.roi = self.rois[self.layer]
        self.p2 = pg.PlotWidget()
        # self.p2.disableAutoRange('xy')
        self.p2.setAspectLocked(True,self.imgScaleFactor)
        self.p2.addItem(self.img1b)
        self.p1.addItem(self.roi)
        self.roi.sigRegionChanged.connect(self.update)
        layout.addWidget(self.p2,12,0,10,1)


        if args.inputpath:
            self.read_dicom_in_folder(args.inputpath)

        
    def update(self):
        thisroi = self.roi.getArrayRegion(self.arr, self.img1a).astype(float)
        convertedROI = myroi2roi(self.roi.saveState(), self.arr[:,:,2].shape, self.verbose)
        toshowvalues = np.ma.masked_array(self.arr[:,:,2],mask=np.logical_not(convertedROI))
        self.img1b.setImage(thisroi, levels=(0, self.arr.max()))
        self.label2_shape.setText("shape: "+str(toshowvalues.shape))
        self.label2_size.setText("size: "+str(toshowvalues.size))
        self.label2_min.setText("min: "+str(toshowvalues.min()))
        self.label2_max.setText("max: "+str(toshowvalues.max()))
        self.label2_mean.setText("mean: "+str(toshowvalues.mean()))
        self.label2_sd.setText("sd: "+str( ndimage.standard_deviation(toshowvalues) ))
        self.label2_sum.setText("sum: "+str( ndimage.sum(toshowvalues) ))
        # print("entropy: ",entropy(thisroi, disk(5))
        # print("maximum: ",maximum(thisroi, disk(5))
        # print("\n"
        # print(disk(5)
        # print("\n")
        self.p2.autoRange()

    def updatemain(self):

        if self.verbose:
            print "updating",self.layer
        if self.xview:
            # dataswappedX = np.swapaxes(self.data,0,1)
            self.arr=self.dataswappedX[self.layer]
        elif self.yview:
            # dataswappedY = np.swapaxes(self.data,0,2)
            self.arr=self.dataswappedY[self.layer]
        else:
            self.arr=self.dataZ[self.layer]
        self.img1a.setImage(self.arr)
        if self.firsttime:
            self.firsttime = False
        else:
            if self.verbose:
                print self.rois
            if self.rois[self.layer]:
                # self.p1.removeItem(self.roi)
                # self.restorePolyLineState(self.roi, self.rois[self.layer])
                self.roi.setState(self.rois[self.layer])
                # self.p1.addItem(self.roi)
                
            self.update()
            self.label_layer.setText("layer: "+str(self.layer)+"/"+str(len(self.data[:,:,:,0])))
            self.label_shape.setText("shape: "+str(self.arr[:,:,2].shape))
            self.label_size.setText("size: "+str(self.arr[:,:,2].size))
            self.label_min.setText("min: "+str(self.arr[:,:,2].min()))
            self.label_max.setText("max: "+str(self.arr[:,:,2].max()))
            self.label_mean.setText("mean: "+str(self.arr[:,:,2].mean()))
            self.label_sd.setText("sd: "+str(ndimage.standard_deviation(self.arr[:,:,2])))
            self.label_sum.setText("sum: "+str(ndimage.sum(self.arr[:,:,2])))
        self.img1a.updateImage()

        
    def nextimg(self):
        if self.layer < (len(self.data[:,:,:,0])-1):
            # if self.xview or self.yview:
            #     self.layer +=1
            # else:
            #     self.layer += int(self.scaleFactor+0.5)
            self.layer +=1
            self.slider.setValue(self.layer+1)
            self.updatemain()

    def previmg(self):
        if self.layer > 0:            
            # if self.xview or self.yview:
            #     self.layer -=1
            # else:
            #     self.layer -= int(self.scaleFactor+0.5)
            self.layer -=1
            self.slider.setValue(self.layer+1)                
            self.updatemain()        

    def setROI(self):
        # self.rois[self.layer] = self.savePolyLineState(self.roi)
        thisroiswassetted=False
        if self.rois[self.layer]:
            thisroiswassetted=True
        self.rois[self.layer] = self.roi.saveState()
        if thisroiswassetted:
            self.dehighlightROI()
        if self.verbose:
            print(self.rois[self.layer])
        convertedROI = myroi2roi(self.rois[self.layer], self.arr[:,:,2].shape, self.verbose)
        # toshowvalues = np.ma.masked_array(self.arr[:,:,2],mask=np.logical_not(convertedROI))
        # self.label2_min.setText("min: "+str(toshowvalues.min()))
        # self.label2_max.setText("max: "+str(toshowvalues.max()))
        # self.label2_mean.setText("mean: "+str(toshowvalues.mean()))
        # # self.label2_mean.setText("mean: "+str( calculateMeanInROI(self.arr[:,:,2],convertedROI, verbose=True) ))
        # self.label2_sd.setText("sd: "+str( ndimage.standard_deviation(toshowvalues) ))
        # self.label2_sum.setText("sum: "+str( ndimage.sum(toshowvalues) ))        
        self.highlightROI1layer(convertedROI)
        self.roisSetted = 0
        for thisroi in self.rois:
            if thisroi:
                self.roisSetted +=1
        self.label2_roisSetted.setText("ROI setted: "+str(self.roisSetted))

    def delROI(self):
        if self.rois[self.layer]:
            self.rois[self.layer] = None
            self.dehighlightROI()
            for thisroi in self.rois:
                if thisroi:
                    self.roisSetted -= 1
            self.label2_roisSetted.setText("ROI setted: "+str(self.roisSetted))        
        
    def myroi_file_save(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        writer = roiFileHandler(self.verbose)
        writer.dicomsPath = os.path.abspath(self.inpath)
        if not str(filename).endswith('.myroi'):
            filename = filename+".myroi"
        writer.write(filename, self.rois, self.roisSetted)


    def nrrdroi_file_save(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        writer = nrrdFileHandler(self.verbose)
        if not str(filename).endswith('.nrrd'):
            filename = filename+".nrrd"
        ROI = myroi2roi(self.rois, self.data[:,:,:,0].shape, self.verbose)            
        writer.write(filename, ROI)
            
    def myroi_file_open(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File','ROI','ROI files (*.myroi)')
        reader = roiFileHandler()
        originalpath = reader.dicomsPath
        self.rois, self.roisSetted = reader.read(filename)
        self.updatemain()
        self.label2_roisSetted.setText("ROI setted: "+str(self.roisSetted))
        ROI = myroi2roi(self.rois, self.data[:,:,:,0].shape, self.verbose)
        colorchannel = 0
        regiontohighlight = self.dataZ[:,:,:,colorchannel]*ROI                
        referenceValue = self.dataZ[:,:,:,colorchannel].max()/regiontohighlight.max()/2.        
        self.dataZ[:,:,:,colorchannel] = self.dataZ[:,:,:,colorchannel] + regiontohighlight*referenceValue 

        
    def slider_jump_to(self):
        self.layer = self.slider.value()-1
        self.updatemain()

    def histogram_matching_normalization(self):
        tmpLayer=self.layer
        tmpXview=self.xview
        tmpYview=self.yview
        self.switchToZView()
        thisNormalizer = Normalizer(self.verbose)
        self.data = self.dataZ = thisNormalizer.match_all(self.dataZ)
        if tmpXview:
            self.switchToXView()
        if tmpYview:
            self.switchToYView()
        self.layer=tmpLayer
        self.slider.setValue(self.layer+1)        
        self.updatemain()

    def normalizeToROI(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File','ROI','ROI files (*.myroi)')
        reader = roiFileHandler()
        roisForNorm, roisNormSetted = reader.read(filename)
        if len(roisForNorm) != len(self.dataZ[:,:,:,2]):
            print("ERROR: not all the layers have a ROI, I can't normalize.")
        convertedRoi = myroi2roi(roisForNorm, self.dataZ[:,:,:,2].shape, self.verbose)
        for thislayer in xrange(0,len(self.dataZ[:,:,:,2])):
            meaninroi = calculateMeanInROI(self.dataZ[thislayer,:,:,2], convertedRoi[thislayer],self.verbose)
            self.dataZ[thislayer] /= meaninroi
        self.allineateViews()            
        self.updatemain()
        
    def read_dicom_in_folder(self, path, useGDCM=False):
        freader = FileReader(path, False, self.verbose)
        if useGDCM:
            dataRGB = freader.readUsingGDCM(False)
        else:
            dataRGB, unusedROI = freader.read(False)
        self.xview=False
        self.yview=False
        self.zview=True        
        self.scaleFactor = freader.scaleFactor
        self.dataZ = dataRGB
        if self.verbose:
            print("shape:", self.dataZ.shape)
            print("shape of a color channel:", self.dataZ[:,:,:,0].shape)
            print("layer: ",self.layer)

        self.imgScaleFactor= 1.
        self.data =  self.dataZ
        self.p1.setAspectLocked(True,self.imgScaleFactor)
        self.p2.setAspectLocked(True,self.imgScaleFactor)
        self.rois = [None]*len(self.data[:,:,:,0])
        self.slider.setMaximum(len(self.data[:,:,:,0]))
        self.layerZ=int(len(self.data[:,:,:,0])/2)
        self.layerX=int(len(self.data[0,:,0,0])/2)
        self.layerY=int(len(self.data[0,0,:,0])/2)
        self.layer = self.layerZ
        self.arr = self.dataZ[self.layerZ]
        self.slider.setValue(self.layer+1)
        self.updatemain()

        if self.verbose:
            print("data len:",len(self.data[:,:,:,0]))

    def select_dicom_folder(self):
        path =  QtGui.QFileDialog.getExistingDirectory(self, 'Open DICOM Directory',os.path.expanduser("~"),QtGui.QFileDialog.ShowDirsOnly)
        if self.verbose:
            print path
        self.read_dicom_in_folder(str(path))

    def select_dicom_folderGDCM(self):
        path =  QtGui.QFileDialog.getExistingDirectory(self, 'Open DICOM Directory',os.path.expanduser("~"),QtGui.QFileDialog.ShowDirsOnly)
        if self.verbose:
            print path
        self.read_dicom_in_folder(str(path),useGDCM=True)        

    def switchToXView(self):
        if self.xview:
            return
        if self.zview:
            self.layerZ = self.layer
        elif self.yview:
            self.layerY = self.layer
        self.xview=True
        self.yview=False
        self.zview=False
        self.allineateViews()        
        self.imgScaleFactor= 1./self.scaleFactor
        self.p1.setAspectLocked(True,self.imgScaleFactor)
        self.p2.setAspectLocked(True,self.imgScaleFactor)        
        self.data = self.dataswappedX
        self.rois = [None]*len(self.data[:,:,:,0])
        self.slider.setMaximum(len(self.data[:,:,:,0]))
        self.layer = self.layerX
        self.slider.setValue(self.layer+1)
        self.updatemain()

    def switchToYView(self):
        if self.yview:
            return
        if self.zview:
            self.layerZ = self.layer
        elif self.xview:
            self.layerX = self.layer        
        self.yview=True
        self.xview=False
        self.zview=False
        self.allineateViews()        
        self.imgScaleFactor= 1./self.scaleFactor
        self.p1.setAspectLocked(True,self.imgScaleFactor)
        self.p2.setAspectLocked(True,self.imgScaleFactor)        
        self.data = self.dataswappedY
        self.rois = [None]*len(self.data[:,:,:,0])
        self.slider.setMaximum(len(self.data[:,:,:,0]))
        self.layer=self.layerY
        self.slider.setValue(self.layer+1)
        self.updatemain()

    def switchToZView(self):
        if self.zview:
            return
        if self.yview:
            self.layerY = self.layer
        elif self.xview:
            self.layerX = self.layer                
        self.zview=True
        self.yview=False
        self.xview=False
        self.imgScaleFactor= 1.
        self.p1.setAspectLocked(True,self.imgScaleFactor)
        self.p2.setAspectLocked(True,self.imgScaleFactor)        
        self.data = self.dataZ
        self.rois = [None]*len(self.data[:,:,:,0])
        self.slider.setMaximum(len(self.data[:,:,:,0]))
        self.layer=self.layerZ
        self.slider.setValue(self.layer+1)
        self.updatemain()

    def dehighlightROI(self, colorchannel = 0):
        referencecolorchannel = colorchannel+1
        if referencecolorchannel>2:
            referencecolorchannel = 0
            
        self.dataZ[:,:,:,colorchannel] = self.dataZ[:,:,:,referencecolorchannel]
        self.allineateViews()
        self.updatemain()


    def allineateViews(self):
        self.dataswappedX = np.swapaxes(np.swapaxes(self.dataZ,0,1),1,2)[:,::-1,::-1,:]        
        self.dataswappedY = np.swapaxes(self.dataZ,0,2)[:,:,::-1,:]          

    def highlightROI(self, ROI, colorchannel=0):
        regiontohighlight = self.dataZ[:,:,:,colorchannel]*ROI
        referenceValue = self.dataZ[:,:,:,colorchannel].max()/regiontohighlight.max()/4.
        #referenceValue = self.dataZ[:,:,:,colorchannel].max()
        self.dataZ[:,:,:,colorchannel] = self.dataZ[:,:,:,colorchannel] - regiontohighlight*referenceValue 
        self.allineateViews()        
        self.updatemain()

    def highlightROI1layer(self, ROI, colorchannel=0):
        regiontohighlight = self.dataZ[self.layer,:,:,colorchannel]*ROI
        referenceValue = self.dataZ[self.layer,:,:,colorchannel].max()/regiontohighlight.max()/2.
        #referenceValue = self.dataZ[:,:,:,colorchannel].max()
        self.dataZ[self.layer,:,:,colorchannel] = self.dataZ[self.layer,:,:,colorchannel] + regiontohighlight*referenceValue 
        # self.dataswappedX = np.swapaxes(np.swapaxes(self.dataZ,0,1),1,2)[:,::-1,::-1,:]        
        # self.dataswappedY = np.swapaxes(self.dataZ,0,2)[:,:,::-1,:]        
        self.updatemain()        
        
    def highlightnrrdROI(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File','ROI','ROI files (*.nrrd)')
        roiFileReader = nrrdFileHandler(self.verbose)
        ROI = roiFileReader.read(filename)
        self.highlightROI(ROI)

    def highlightMyROI(self, colorchannel=0):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File','ROI','MyROI files (*.myroi)')        
        reader = roiFileHandler(self.verbose)
        myroi, roisSetted = reader.read(filename)
        ROI = myroi2roi(myroi, self.data[:,:,:,0].shape, self.verbose)
        self.highlightROI(ROI)

    def saveToImage(self, extension):
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save File'))
        if not filename.endswith(extension):
            filename = filename+extension
        print(filename)
            
        if self.verbose:
            print(type(self.arr))
            print(self.arr.shape)
        image = self.arr.transpose(1,0,2)[::-1,:,:]
        sides = image.shape
        image = scipy.misc.imresize(image,size=tuple([int(sides[0]/self.imgScaleFactor),sides[1]]))
        scipy.misc.imsave(filename,image)        
        
    def saveToTIFFImage(self):
        self.saveToImage(".tiff")

    def saveToPNGImage(self):
        self.saveToImage(".png")        


    def histoOfAllLayer(self):
        print("to be done")

    def about(self):
        dialogTextBrowser = AboutWindow(self)
        dialogTextBrowser.exec_()

    def CurvatureFlowImageFilter(self):
        filtered = curvatureFlowImageFilter(self.arr, self.verbose)
        self.img1b.setImage(filtered)
        self.p2.autoRange()
        self.img1b.updateImage()

    def mouseMoved(self, pos):
        print(type(pos))
        print(pos)
        # # print("lastPos",pos.lastPos())
        # print("pos",pos.pos())
        # print("scenePos",pos.scenePos())        
        # print "Image position:", self.img1a.mapFromScene(pos)
        # if self.p1.sceneBoundingRect().contains(pos.pos()):
        # mousePoint = self.p1ViewBox.mapSceneToView(pos.pos())
        # print("mousePoint",mousePoint)
        mousePoint = self.p1ViewBox.mapSceneToView(pos.scenePos())
        if self.verbose:
            print("mousePoint",mousePoint)        
        # # print(self.img1a.mapFromScene(pos.pos()))
        # print(type(mousePoint.x()))
        seedX = int(mousePoint.x()+0.5)
        seedY = int(mousePoint.y()+0.5)
        if seedX <0:
            seedX = 0
        if seedY <0:
            seedY = 0 
        thisSeed = (seedX, seedY)
        # print(type(thisSeed[0]))
        # thisSeed = (100,100)
        if self.verbose:        
            print(thisSeed)
        thisImage = self.arr[:,:,0]
        # # print(type(thisImage))
        # # print(thisImage.shape)
        value = thisImage[seedX,seedY]
        print("value",value)
        thresPer = 0.20
        lowThres = value - value*thresPer
        if lowThres<0:
            lowThres = 0
        hiThres = value + value*thresPer
        print("range",lowThres, hiThres)
        fat = connectedThreshold(thisImage, thisSeed, lowThres, hiThres)
        if fat.any():
            self.highlightROI(fat)
            
if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window_dicom_tool()
    window.show()
    sys.exit(app.exec_())
