#class used to manage the pyramid HOG features
import resize
import util2 as util
import numpy
import math
import pylab
#import scipy.misc.pilutil
import cPickle
import time

SMALL=100 #coefficient to multiply resolution features
DENSE=0 #number of levels to use a dense scan instead of a Ctf
K=1.0 #0.3 #coefficient for the deformation featres

from numpy import ctypeslib
from ctypes import c_int,c_double,c_float
import ctypes

#library to compute HOGs
ctypes.cdll.LoadLibrary("./libhog.so")
lhog= ctypes.CDLL("libhog.so")
lhog.process.argtypes=[
    numpy.ctypeslib.ndpointer(dtype=c_float,ndim=3,flags="F_CONTIGUOUS")#im
    ,c_int #dimy
    ,c_int #dimx
    ,c_int #sbin
    ,numpy.ctypeslib.ndpointer(dtype=c_float,ndim=3,flags="F_CONTIGUOUS")# *hog (round(dimy/float(sbin))-2,round(dimx/float(sbin))-2,31)
    ,c_int #hy
    ,c_int #hx
    ,c_int #hz
    ]


#library to compute correlation between object model and HOGs
ctypes.cdll.LoadLibrary("./libexcorr.so")
ff= ctypes.CDLL("libexcorr.so")

ff.scaneigh.argtypes=[numpy.ctypeslib.ndpointer(dtype=c_float,ndim=3,flags="C_CONTIGUOUS"),c_int,c_int,numpy.ctypeslib.ndpointer(dtype=c_float,ndim=3,flags="C_CONTIGUOUS"),c_int,c_int,c_int,numpy.ctypeslib.ndpointer(dtype=c_int,flags="C_CONTIGUOUS"),numpy.ctypeslib.ndpointer(dtype=c_int,flags="C_CONTIGUOUS"),numpy.ctypeslib.ndpointer(dtype=c_float,flags="C_CONTIGUOUS"),numpy.ctypeslib.ndpointer(dtype=c_int,flags="C_CONTIGUOUS"),numpy.ctypeslib.ndpointer
(dtype=c_int,flags="C_CONTIGUOUS"),c_int,c_int,c_int,c_int]

ff.scanDef2.argtypes = [
    ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),
    c_int,c_int,c_int,
    ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),ctypeslib.ndpointer(c_float),
    ctypeslib.ndpointer(c_float),
    c_int,c_int,ctypeslib.ndpointer(c_int),ctypeslib.ndpointer(c_int),
    ctypeslib.ndpointer(c_int),
    ctypeslib.ndpointer(c_float),
    c_int,c_int,c_int,ctypeslib.ndpointer(c_float),c_int,
    ctypes.POINTER(c_float),c_int,c_int,c_int]
ff.scanDef2.restype=ctypes.c_float

ff.setK.argtypes = [c_float]
ff.setK(K)

ff.getK.argtypes = []
ff.getK.restype = ctypes.c_float
ff.setK(K)

def setK(pk):
    ff.setK(pk)    

def getfeat(a,y1,y2,x1,x2,trunc=0):
    """
        returns the hog features at the given position and 
        zeros in case the coordiantes are outside the borders
        """
    dimy=a.shape[0]
    dimx=a.shape[1]
    py1=y1;py2=y2;px1=x1;px2=x2
    dy1=0;dy2=0;dx1=0;dx2=0
    #if trunc>0:
    b=numpy.zeros((abs(y2-y1),abs(x2-x1),a.shape[2]+trunc))
    if trunc>0:
        b[:,:,-trunc]=1
    #else:
    #    b=numpy.zeros((abs(y2-y1),abs(x2-x1),a.shape[2]))
    if py1<0:
        py1=0
        dy1=py1-y1
    if py2>=dimy:
        py2=dimy
        dy2=y2-py2
    if px1<0:
        px1=0
        dx1=px1-x1
    if px2>=dimx:
        px2=dimx
        dx2=x2-px2
    if numpy.array(a[py1:py2,px1:px2].shape).min()==0 or numpy.array(b[dy1:y2-y1-dy2,dx1:x2-x1-dx2].shape).min()==0:
        pass
    else:
        if trunc==1:
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2,:-1]=a[py1:py2,px1:px2]
            #b[:,:,-1]=1
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2,-1]=0
        else:
            b[dy1:y2-y1-dy2,dx1:x2-x1-dx2]=a[py1:py2,px1:px2]
    return b


#wrapper for the HOG computation
def hog(img,sbin=8):
    """
    Compute the HOG descriptor of an image
    """
    if type(img)!=numpy.ndarray:
        raise "img must be a ndarray"
    if img.ndim!=3:
        raise "img must have 3 dimensions"
    hy=int(round(img.shape[0]/float(sbin)))-2
    hx=int(round(img.shape[1]/float(sbin)))-2
    mtype=c_float
    hog=numpy.zeros((hy,hx,31),dtype=mtype,order="f")
    lhog.process(numpy.asfortranarray(img,dtype=mtype),img.shape[0],img.shape[1],sbin,hog,hy,hx,31)
    return hog;#mfeatures.mfeatures(img , sbin);


def hogflip(feat,obin=9):
    """    
    returns the horizontally flipped version of the HOG features
    """
    #feature shape
    #[9 not oriented][18 oriented][4 normalization]
    if feat.shape[2]==31:
        p=numpy.array([10,9,8,7,6,5,4,3,2,1,18,17,16,15,14,13,12,11,19,27,26,25,24,23,22,21,20,30,31,28,29])-1
    else:
        p=numpy.array([10,9,8,7,6,5,4,3,2,1,18,17,16,15,14,13,12,11,19,27,26,25,24,23,22,21,20,30,31,28,29,32])-1
    aux=feat[:,::-1,p]
    return numpy.ascontiguousarray(aux)

def defflip(feat):
    """    
    returns the horizontally flipped version of the deformation features
    """
    sx=feat.shape[1]/2-1
    fflip=numpy.zeros(feat.shape,dtype=feat.dtype)
    for ly in range(feat.shape[0]/2):
        for lx in range(feat.shape[1]/2):
            fflip[ly*2:(ly+1)*2,lx*2:(lx+1)*2]=feat[ly*2:(ly+1)*2,(sx-lx)*2:(sx-lx+1)*2].T
    return fflip

#auxiliary class
class container(object):
    def __init__(self,objarray,ptrarray):
        self.obj=objarray
        self.ptr=ptrarray

class pyrHOG:
    def __init__(self,im,interv=10,sbin=8,savedir="./",compress=False,notload=False,notsave=False,hallucinate=0,cformat=False,flip=False):
        """
        Compute the HOG pyramid of an image
        if im is a string call precomputed
        if im is an narray call compute
        """

        import time
        t=time.time()       
        self.hog=[]#hog pyramid as a list of hog features
        self.interv=interv
        self.oct=0
        self.sbin=sbin#number of pixels per spatial bin
        self.flip=flip
        if isinstance(im,pyrHOG):#build a copy
            self.__copy(im)
            #return
        if isinstance(im,str):
            self._precompute(im,interv,sbin,savedir,compress,notload,notsave,hallucinate,cformat=cformat)
            #return
        if type(im)==numpy.ndarray:
            self._compute(im,interv,sbin,hallucinate,cformat=cformat)
            #return
        print "Features: %.3f s"%(time.time()-t)
        #raise "Error: im must be either a string or an image"
        
    def _compute(self,img,interv=10,sbin=8,hallucinate=0,cformat=False):
        """
        Compute the HOG pyramid of an image
        """
        l=[]
        scl=[]
        octimg=img.astype(numpy.float)#copy()
        maxoct=int(numpy.log2(int(numpy.min(img.shape[:-1])/sbin)))-1#-2
        intimg=octimg
        if hallucinate>1:
            #hallucinate features
            for i in range(interv):
                if cformat:
                    l.append(numpy.ascontiguousarray(hog(intimg,sbin/4),numpy.float32))
                else:
                    l.append(hog(intimg,sbin/4).astype(numpy.float32))                    
                intimg=resize.resize(octimg,math.pow(2,-float(i+1)/interv))
                scl.append(4.0*2.0**(-float(i)/interv))
        if hallucinate>0:
            #hallucinate features
            for i in range(interv):
                if cformat:
                    l.append(numpy.ascontiguousarray(hog(intimg,sbin/2),numpy.float32))                    
                else:
                    l.append(hog(intimg,sbin/2).astype(numpy.float32))
                intimg=resize.resize(octimg,math.pow(2,-float(i+1)/interv))
                scl.append(2.0*2.0**(-float(i)/interv))
        #normal features
        for o in range(maxoct):
            intimg=octimg
            for i in range(interv):
                t1=time.time()
                if cformat:
                    l.append(numpy.ascontiguousarray(hog(intimg,sbin),numpy.float32))                    
                else:
                    l.append(hog(intimg,sbin).astype(numpy.float32))
                scl.append(2.0**(-o-float(i)/interv))
                t2=time.time()
                intimg=resize.resize(octimg,math.pow(2,-float(i+1)/interv))
            octimg=intimg
        self.hog=l
        self.interv=interv
        self.oct=maxoct
        self.sbin=sbin
        self.scale=scl
        self.hallucinate=hallucinate
        
    def _precompute(self,imname,interv=10,sbin=8,savedir="./",compress=False,notload=False,notsave=True,hallucinate=0,cformat=False):
        """
        Check if the HOG if imname is already computed, otherwise 
        compute it and save in savedir
        """
        try:
            if notload:
                #generate an error to pass to computing hog
                error
            else:
                "Warning: image flip do not work with preload!!!"
            f=[]
            if compress:
                f=gzip.open(savedir+imname.split("/")[-1]+".zhog%d_%d_%d"%(interv,sbin,hallucinate),"rb")
            else:
                f=open(savedir+imname.split("/")[-1]+".hog%d_%d_%d"%(interv,sbin,hallucinate),"r")
            print "Loading precalculated Hog"
            aux=cPickle.load(f)
            self.interv=aux.interv
            self.oct=aux.oct
            self.sbin=aux.sbin
            self.hog=aux.hog
            self.scale=aux.scale
            self.hallucinate=aux.hallucinate
        except:
            print "Computing Hog"
            img=None
            img=util.myimread(imname,self.flip)
            if img.ndim<3:
                aux=numpy.zeros((img.shape[0],img.shape[1],3))
                aux[:,:,0]=img
                aux[:,:,1]=img
                aux[:,:,2]=img
                img=aux
            self._compute(img,interv=interv,sbin=sbin,hallucinate=hallucinate,cformat=cformat)
            if notsave:
                return
            f=[]
            if compress:
                f=gzip.open(savedir+imname.split("/")[-1]+".zhog%d_%d_%d"%(self.interv,self.sbin,hallucinate),"wb")
            else:
                f=open(savedir+imname.split("/")[-1]+".hog%d_%d_%d"%(self.interv,self.sbin,hallucinate),"w")
            cPickle.dump(self,f,2)   

    def resetHOG(self):
        "reset the HOG computation counter"
        ff.resetHOG()

    def getHOG(self):
        "get the HOG computation counter"
        return ff.getHOG()

    def scanRCFL(self,model,initr=1,ratio=1,small=True,trunc=0):
        """
        scan the HOG pyramid using the CtF algorithm
        """        
        ww=model["ww"]
        rho=model["rho"]
        if model.has_key("occl"):
            print "Occlusions:",model["occl"]
            occl=numpy.array(model["occl"])*SMALL
        else:
            #print "No Occlusions"
            occl=numpy.zeros(len(model["ww"]))
        res=[]#score
        pparts=[]#parts position
        tot=0
        if not(small):
            self.starti=self.interv*(len(ww)-1)
        else:
            if type(small)==bool:
                self.starti=0
            else:
                self.starti=self.interv*(len(ww)-1-small)
        from time import time
        for i in range(self.starti,len(self.hog)):
            samples=numpy.mgrid[-ww[0].shape[0]+initr:self.hog[i].shape[0]+1:1+2*initr,-ww[0].shape[1]+initr:self.hog[i].shape[1]+1:1+2*initr].astype(ctypes.c_int)
            sshape=samples.shape[1:3]
            res.append(numpy.zeros(sshape,dtype=ctypes.c_float))
            pparts.append(numpy.zeros((2,len(ww),sshape[0],sshape[1]),dtype=c_int))
            for lev in range(len(ww)):
                if i-self.interv*lev>=0:
                    if lev==0:
                        r=initr
                    else:
                        r=ratio
                    auxres=res[-1].copy()
                    ff.scaneigh(self.hog[i-self.interv*lev],
                        self.hog[i-self.interv*lev].shape[0],
                        self.hog[i-self.interv*lev].shape[1],
                        ww[lev],
                        ww[lev].shape[0],ww[lev].shape[1],ww[lev].shape[2],
                        samples[0,:,:],
                        samples[1,:,:],
                        auxres,
                        pparts[-1][0,lev,:,:],
                        pparts[-1][1,lev,:,:],
                        r,r,
                        sshape[0]*sshape[1],trunc)
                    res[i-self.starti]+=auxres
                    samples[:,:,:]=(samples[:,:,:]+pparts[-1][:,lev,:,:])*2+1
                else:#resolution occlusion
                    if len(model["ww"])-1>lev:
                        res[i-self.starti]+=occl[lev-1]
            res[i-self.starti]-=rho
        return res,pparts


    def scanRCFLDef(self,model,initr=1,ratio=1,small=True,usemrf=True,mysamples=None,trunc=0):
        """
        scan the HOG pyramid using the CtF algorithm but using deformations
        """     
        ww=model["ww"]
        rho=model["rho"]
        df=model["df"]
        if model.has_key("occl"):
            print "Occlusions:",model["occl"]
            occl=numpy.array(model["occl"])*SMALL
        else:
            #print "No Occlusions"
            occl=numpy.zeros(len(model["ww"]))
        res=[]#score
        pparts=[]#parts position
        tot=0
        if not(small):
            self.starti=self.interv*(len(ww)-1)
        else:
            if type(small)==bool:
                self.starti=0
            else:
                self.starti=self.interv*(len(ww)-1-small)
        from time import time
        for i in range(self.starti,len(self.hog)):
            if mysamples==None:
                samples=numpy.mgrid[-ww[0].shape[0]+initr:self.hog[i].shape[0]+1:1+2*initr,-ww[0].shape[1]+initr:self.hog[i].shape[1]+1:1+2*initr].astype(c_int)
            else:
                samples=mysamples[i]
            sshape=samples.shape[1:3]
            res.append(numpy.zeros(sshape,dtype=ctypes.c_float))
            pparts.append([])
            nelem=(sshape[0]*sshape[1])
            for l in range(len(ww)):
                pparts[-1].append(numpy.zeros((2**l,2**l,4,sshape[0],sshape[1]),dtype=c_int))
            ff.scaneigh(self.hog[i],
                self.hog[i].shape[0],
                self.hog[i].shape[1],
                ww[0],
                ww[0].shape[0],ww[0].shape[1],ww[0].shape[2],
                samples[0,:,:],
                samples[1,:,:],
                res[-1],
                pparts[-1][0][0,0,0,:,:],
                pparts[-1][0][0,0,1,:,:],
                initr,initr,
                nelem,trunc)
            samples[:,:,:]=(samples[:,:,:]+pparts[-1][0][0,0,:2,:,:])*2+1
            if i-self.interv>=0 and len(model["ww"])-1>0:
                self.scanRCFLPart(model,samples,pparts[-1],res[i-self.starti],i-self.interv,1,0,0,ratio,usemrf,occl,trunc) 
            else:
                res[i-self.starti]+=numpy.sum(occl[1:])
            res[i-self.starti]-=rho
        return res,pparts


    def scanRCFLPart(self,model,samples,pparts,res,i,lev,locy,locx,ratio,usemrf,occl,trunc):
        """
        auxiliary function for the recursive search of the parts
        """     
        locy=locy*2
        locx=locx*2
        fy=model["ww"][0].shape[0]
        fx=model["ww"][0].shape[1]
        ww1=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww2=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        ww3=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww4=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        df1=model["df"][lev][(locy+0):(locy+1),(locx+0):(locx+1),:].copy()
        df2=model["df"][lev][(locy+0):(locy+1),(locx+1):(locx+2),:].copy()
        df3=model["df"][lev][(locy+1):(locy+2),(locx+0):(locx+1),:].copy()
        df4=model["df"][lev][(locy+1):(locy+2),(locx+1):(locx+2),:].copy()
        parts=numpy.zeros((2,2,4,res.shape[0],res.shape[1]),dtype=c_int)
        auxres=numpy.zeros(res.shape,numpy.float32)
        ff.scanDef2(ww1,ww2,ww3,ww4,fy,fx,ww1.shape[2],df1,df2,df3,df4,self.hog[i],self.hog[i].shape[0],self.hog[i].shape[1],samples[0,:,:],samples[1,:,:],parts,auxres,ratio,samples.shape[1]*samples.shape[2],usemrf,numpy.array([],dtype=numpy.float32),0,ctypes.POINTER(c_float)(),0,0,trunc)
        res+=auxres
        pparts[lev][(locy+0):(locy+2),(locx+0):(locx+2),:,:,:]=parts
        if i-self.interv>=0 and len(model["ww"])-1>lev:
            samples1=(samples+parts[0,0,:2,:,:])*2+1
            self.scanRCFLPart(model,samples1.copy(),pparts,res,i-self.interv,lev+1,(locy+0),(locx+0),ratio,usemrf,occl,trunc)
            samples2=((samples.T+parts[0,1,:2,:,:].T+numpy.array([0,fx],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples2.copy(),pparts,res,i-self.interv,lev+1,(locy+0),(locx+1),ratio,usemrf,occl,trunc)
            samples3=((samples.T+parts[1,0,:2,:,:].T+numpy.array([fy,0],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples3.copy(),pparts,res,i-self.interv,lev+1,(locy+1),(locx+0),ratio,usemrf,occl,trunc)
            samples4=((samples.T+parts[1,1,:2,:,:].T+numpy.array([fy,fx],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples4.copy(),pparts,res,i-self.interv,lev+1,(locy+1),(locx+1),ratio,usemrf,occl,trunc)
        else:
            if len(model["ww"])-1>lev:
                res+=numpy.sum(occl[lev+1:])

    def scanRCFLDefThr(self,model,initr=1,ratio=1,small=True,usemrf=True,mythr=0):
        """
        scan the HOG pyramid using the CtF algorithm but using deformations and a pruning threshold
        """    
        ww=model["ww"]
        rho=model["rho"]
        df=model["df"]
        res=[]
        pparts=[]
        tot=0
        if not(small):
            self.starti=self.interv*(len(ww)-1)
        else:
            if type(small)==bool:
                self.starti=0
            else:
                self.starti=self.interv*(len(ww)-1-small)
        from time import time
        for i in range(self.starti,len(self.hog)):
            samples=numpy.mgrid[-ww[0].shape[0]+initr:self.hog[i].shape[0]+1:1+2*initr,-ww[0].shape[1]+initr:self.hog[i].shape[1]+1:1+2*initr].astype(c_int)
            sshape=samples.shape[1:3]
            res.append(numpy.zeros(sshape,dtype=ctypes.c_float))
            pparts.append([])
            nelem=(sshape[0]*sshape[1])
            for l in range(len(ww)):
                pparts[-1].append(numpy.zeros((2**l,2**l,4,sshape[0],sshape[1]),dtype=c_int))
            ff.scaneigh(self.hog[i],
                self.hog[i].shape[0],
                self.hog[i].shape[1],
                ww[0],
                ww[0].shape[0],ww[0].shape[1],ww[0].shape[2],
                samples[0,:,:],
                samples[1,:,:],
                res[-1],
                pparts[-1][0][0,0,0,:,:],
                pparts[-1][0][0,0,1,:,:],
                initr,initr,
                nelem,0)
            samples[:,:,:]=(samples[:,:,:]+pparts[-1][0][0,0,:2,:,:])*2+1
            self.scanRCFLPartThr(model,samples,pparts[-1],res[i-self.starti],i-self.interv,1,0,0,ratio,usemrf,mythr) 
            res[i-self.starti]-=rho
        return res,pparts

    def scanRCFLPartThr(self,model,samples,pparts,res,i,lev,locy,locx,ratio,usemrf,mythr):
        """
        auxiliary function for the recursive search of the parts with pruning threshold
        """   
        locy=locy*2
        locx=locx*2
        fy=model["ww"][0].shape[0]
        fx=model["ww"][0].shape[1]
        ww1=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww2=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        ww3=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww4=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        df1=model["df"][lev][(locy+0):(locy+1),(locx+0):(locx+1),:].copy()
        df2=model["df"][lev][(locy+0):(locy+1),(locx+1):(locx+2),:].copy()
        df3=model["df"][lev][(locy+1):(locy+2),(locx+0):(locx+1),:].copy()
        df4=model["df"][lev][(locy+1):(locy+2),(locx+1):(locx+2),:].copy()
        parts=numpy.zeros((2,2,4,res.shape[0],res.shape[1]),dtype=c_int)
        auxres=numpy.zeros(res.shape,numpy.float32)
        res[res<mythr]=-1000
        samples[:,res==-1000]=-1000
        ff.scanDef2(ww1,ww2,ww3,ww4,fy,fx,ww1.shape[2],df1,df2,df3,df4,self.hog[i],self.hog[i].shape[0],self.hog[i].shape[1],samples[0,:,:],samples[1,:,:],parts,auxres,ratio,samples.shape[1]*samples.shape[2],usemrf,numpy.array([],dtype=numpy.float32),0,ctypes.POINTER(c_float)(),0,0,0)
        res+=auxres
        pparts[lev][(locy+0):(locy+2),(locx+0):(locx+2),:,:,:]=parts
        if i-self.interv>=0 and len(model["ww"])-1>lev:
            samples1=(samples+parts[0,0,:2,:,:])*2+1
            self.scanRCFLPart(model,samples1.copy(),pparts,res,i-self.interv,lev+1,(locy+0),(locx+0),ratio,usemrf)
            samples2=((samples.T+parts[0,1,:2,:,:].T+numpy.array([0,fx],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples2.copy(),pparts,res,i-self.interv,lev+1,(locy+0),(locx+1),ratio,usemrf)
            samples3=((samples.T+parts[1,0,:2,:,:].T+numpy.array([fy,0],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples3.copy(),pparts,res,i-self.interv,lev+1,(locy+1),(locx+0),ratio,usemrf)
            samples4=((samples.T+parts[1,1,:2,:,:].T+numpy.array([fy,fx],dtype=c_int).T)*2+1).T
            self.scanRCFLPart(model,samples4.copy(),pparts,res,i-self.interv,lev+1,(locy+1),(locx+1),ratio,usemrf)

    def scanRCFLDefBU(self,model,initr=1,ratio=1,small=True,usemrf=True,mysamples=None):
        """
        scan the HOG pyramid using the full search and using deformations
        """   
        ww=model["ww"]
        rho=model["rho"]
        df=model["df"]
        res=[]#score
        prec=[]#precomputed scores
        pres=[]
        pparts=[]#parts position
        tot=0
        pady=model["ww"][-1].shape[0]
        padx=model["ww"][-1].shape[1]
        if not(small):
            self.starti=self.interv*(len(ww)-1)
        else:
            if type(small)==bool:
                self.starti=0
            else:
                self.starti=self.interv*(len(ww)-1-small)
        from time import time
        for i in range(self.starti,len(self.hog)):
            if mysamples==None:
                samples=numpy.mgrid[-ww[0].shape[0]+initr:self.hog[i].shape[0]+1:1+2*initr,-ww[0].shape[1]+initr:self.hog[i].shape[1]+1:1+2*initr].astype(c_int)
            else:
                samples=mysamples[i]
            csamples=samples.copy()
            sshape=samples.shape[1:3]
            pres.append(numpy.zeros(((2*initr+1)*(2*initr+1),sshape[0],sshape[1]),dtype=ctypes.c_float))
            res.append(numpy.zeros(sshape,dtype=ctypes.c_float))
            pparts.append([])
            prec=[]#.append([])
            nelem=(sshape[0]*sshape[1])
            #auxpparts=[]
            for l in range(len(ww)):
                prec.append(-100000*numpy.ones((4**l,2**l*(self.hog[i].shape[0]+2)+pady*2,2**l*(self.hog[i].shape[1]+2)+padx*2),dtype=ctypes.c_float))
                pparts[-1].append(numpy.zeros((2**l,2**l,4,sshape[0],sshape[1]),dtype=c_int))                
            auxpparts=(numpy.zeros(((2*initr+1)*(2*initr+1),2,2,4,sshape[0],sshape[1]),dtype=c_int))
            auxptr=numpy.zeros((2*initr+1)*(2*initr+1),dtype=object)
            ct=container(auxpparts,auxptr)
            for l in range((2*initr+1)**2):
                maux=(numpy.zeros((4,(2*ratio+1)*(2*ratio+1),2,2,4,sshape[0],sshape[1]),dtype=c_int))
                auxptr=numpy.zeros((4,(2*ratio+1)*(2*ratio+1)),dtype=object)
                ct.ptr[l]=container(maux,auxptr)
            for dy in range(-initr,initr+1):
                for dx in range(-initr,initr+1):
                    csamples[0,:,:]=samples[0,:,:]+dy
                    csamples[1,:,:]=samples[1,:,:]+dx
                    ff.scaneigh(self.hog[i],
                        self.hog[i].shape[0],
                        self.hog[i].shape[1],
                        ww[0],
                        ww[0].shape[0],ww[0].shape[1],ww[0].shape[2],
                        csamples[0,:,:],
                        csamples[1,:,:],
                        pres[-1][(dy+initr)*(2*initr+1)+(dx+initr),:,:],
                        pparts[-1][0][0,0,0,:,:],
                        pparts[-1][0][0,0,1,:,:],
                        0,0,
                        nelem,0)
                    csamples=csamples[:,:,:]*2+1
                    self.scanRCFLPartBU(model,csamples,pparts[-1],ct.ptr[(dy+initr)*(2*initr+1)+(dx+initr)],pres[i-self.starti][(dy+initr)*(2*initr+1)+(dx+initr),:,:],i-self.interv,1,0,0,ratio,usemrf,prec,pady,padx) 
            res[i-self.starti]=pres[i-self.starti].max(0)
            el=pres[i-self.starti].argmax(0)
            pparts[-1][0][0,0,0,:,:]=el/(initr*2+1)-1
            pparts[-1][0][0,0,1,:,:]=el%(initr*2+1)-1
            for l in range(1,len(ww)):
                elx=numpy.tile(el,(2**l,2**l,4,1,1))
                for pt in range((2*initr+1)*(2*initr+1)):
                    if len(ct.ptr[pt].best)>=l:
                        pparts[-1][l][elx==pt]=ct.ptr[pt].best[l-1][elx==pt]
            res[i-self.starti]-=rho
        return res,pparts


    def scanRCFLPartBU(self,model,samples,pparts,ct,res,i,lev,locy,locx,ratio,usemrf,prec,pady,padx):
        """
        auxiliary function for the recursive search of the parts for the complete search
        """   
        locy=locy*2
        locx=locx*2
        fy=model["ww"][0].shape[0]
        fx=model["ww"][0].shape[1]
        ww1=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww2=model["ww"][lev][(locy+0)*fy:(locy+1)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        ww3=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+0)*fx:(locx+1)*fx,:].copy()
        ww4=model["ww"][lev][(locy+1)*fy:(locy+2)*fy,(locx+1)*fx:(locx+2)*fx,:].copy()
        df1=model["df"][lev][(locy+0):(locy+1),(locx+0):(locx+1),:].copy()
        df2=model["df"][lev][(locy+0):(locy+1),(locx+1):(locx+2),:].copy()
        df3=model["df"][lev][(locy+1):(locy+2),(locx+0):(locx+1),:].copy()
        df4=model["df"][lev][(locy+1):(locy+2),(locx+1):(locx+2),:].copy()
        parts=numpy.zeros((2,2,4,res.shape[0],res.shape[1]),dtype=c_int)
        auxparts=numpy.zeros((4,(2*ratio+1)*(2*ratio+1),2,2,4,res.shape[0],res.shape[1]),dtype=c_int)
        if i-self.interv>=0 and len(model["ww"])-1>lev:
            for l in range(len(ct.ptr)):
                maux=(numpy.zeros((4,(2*ratio+1)*(2*ratio+1),2,2,4,res.shape[0],res.shape[1]),dtype=c_int))
                auxptr=numpy.zeros((4,(2*ratio+1)*(2*ratio+1)),dtype=object)
                ct.ptr[l]=container(maux,auxptr)
        auxres=numpy.zeros(res.shape,numpy.float32)
        pres=numpy.zeros((4,(2*ratio+1),(2*ratio+1),res.shape[0],res.shape[1]),numpy.float32)
        csamples=samples.copy()
        if i-self.interv>=0 and len(model["ww"])-1>lev:
            for dy in range(-ratio,ratio+1):
                for dx in range(-ratio,ratio+1):
                    csamples[0,:,:]=(samples[0,:,:]+dy)
                    csamples[1,:,:]=(samples[1,:,:]+dx)
                    samples1=(csamples)*2+1
                    auxparts[0,(dy+ratio)*(2*ratio+1)+(dx+ratio)]=self.scanRCFLPartBU(model,samples1,pparts,ct.ptr[0,(dy+ratio)*(2*ratio+1)+(dx+ratio)],pres[0,(dy+ratio),(dx+ratio),:,:],i-self.interv,lev+1,(locy+0),(locx+0),ratio,usemrf,prec,pady,padx)
                    samples2=((csamples.T+numpy.array([0,fx],dtype=c_int).T)*2+1).T
                    auxparts[1,(dy+ratio)*(2*ratio+1)+(dx+ratio)]=self.scanRCFLPartBU(model,samples2.copy(),pparts,ct.ptr[1,(dy+ratio)*(2*ratio+1)+(dx+ratio)],pres[1,(dy+ratio),(dx+ratio),:,:],i-self.interv,lev+1,(locy+0),(locx+1),ratio,usemrf,prec,pady,padx)
                    samples3=((csamples.T+numpy.array([fy,0],dtype=c_int).T)*2+1).T
                    auxparts[2,(dy+ratio)*(2*ratio+1)+(dx+ratio)]=self.scanRCFLPartBU(model,samples3.copy(),pparts,ct.ptr[2,(dy+ratio)*(2*ratio+1)+(dx+ratio)],pres[2,(dy+ratio),(dx+ratio),:,:],i-self.interv,lev+1,(locy+1),(locx+0),ratio,usemrf,prec,pady,padx)
                    samples4=((csamples.T+numpy.array([fy,fx],dtype=c_int).T)*2+1).T
                    auxparts[3,(dy+ratio)*(2*ratio+1)+(dx+ratio)]=self.scanRCFLPartBU(model,samples4.copy(),pparts,ct.ptr[3,(dy+ratio)*(2*ratio+1)+(dx+ratio)],pres[3,(dy+ratio),(dx+ratio),:,:],i-self.interv,lev+1,(locy+1),(locx+1),ratio,usemrf,prec,pady,padx)
        
        auxprec=prec[lev][((locy/2)*2+(locx/2))*4:((locy/2)*2+(locx/2)+1)*4]
        ff.scanDef2(ww1,ww2,ww3,ww4,fy,fx,ww1.shape[2],df1,df2,df3,df4,self.hog[i],self.hog[i].shape[0],self.hog[i].shape[1],samples[0,:,:],samples[1,:,:],parts,auxres,ratio,samples.shape[1]*samples.shape[2],usemrf,pres,1,auxprec.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),pady,padx,0)
        res+=auxres
        ct.best=[parts]

        if i-self.interv>=0 and len(model["ww"])-1>lev:            
            for l in range(len(ct.ptr[0,0].best)):
                aux=numpy.zeros((ct.ptr[0,0].best[l].shape[0]*2,ct.ptr[0,0].best[l].shape[1]*2,4,res.shape[0],res.shape[1]))
                ct.best.append(aux)
                for py in range(res.shape[0]):
                    for px in range(res.shape[1]):
                        ps=(parts[0,0,0,py,px]+ratio)*(ratio*2+1)+parts[0,0,1,py,px]+ratio
                        ct.best[-1][locy+0:locy+0+2,locx+0:locx+0+2,:,py,px]=auxparts[0,ps][:,:,:,py,px]
                        ps=(parts[0,1,0,py,px]+ratio)*(ratio*2+1)+parts[0,1,1,py,px]+ratio
                        ct.best[-1][locy+0:locy+0+2,locx+2:locx+2+2,:,py,px]=auxparts[1,ps][:,:,:,py,px]
                        ps=(parts[1,0,0,py,px]+ratio)*(ratio*2+1)+parts[1,0,1,py,px]+ratio
                        ct.best[-1][locy+2:locy+2+2,locx+0:locx+0+2,:,py,px]=auxparts[2,ps][:,:,:,py,px]
                        ps=(parts[1,1,0,py,px]+ratio)*(ratio*2+1)+parts[1,1,1,py,px]+ratio
                        ct.best[-1][locy+2:locy+2+2,locx+2:locx+2+2,:,py,px]=auxparts[3,ps][:,:,:,py,px]
        return parts


class Treat:
    def __init__(self,f,scr,pos,sample,fy,fx,occl=False,trunc=0):
        self.pos=pos
        self.scr=scr
        self.f=f
        self.interv=f.interv
        self.sbin=f.sbin
        self.fy=fy
        self.fx=fx
        self.scale=f.scale
        self.sample=sample
        self.occl=occl
        self.trunc=trunc

    def showBBox(self,allgtbbox,colors=["w","g"],new_alpha=0.15):
        for item in allgtbbox:
            bbox=item["bbox"]
            pylab.fill([bbox[1],bbox[1],bbox[3],bbox[3],bbox[1]],[bbox[0],bbox[2],bbox[2],bbox[0],bbox[0]],colors[0], alpha=new_alpha, edgecolor=colors[0],lw=2)

    def doall(self,thr=-1,rank=1000,refine=True,cluster=0.5,rawdet=False,show=False,inclusion=False,cl=0):
        """
        executes all the detection steps for test
        """        
        #import time
        #t=time.time()
        self.det=self.select_fast(thr,cl=cl)        
        #print len(self.det)
        #print "Select",time.time()-t
        #t=time.time()
        self.det=self.rank_fast(self.det,rank,cl=cl) 
        #print "Rank",time.time()-t
        if refine:
        #    t=time.time()
            self.det=self.refine(self.det)
        #    print "Refine",time.time()-t
        #t=time.time()
        #if occl:
        #    self.det=self.occl(self.det)
        self.det=self.bbox(self.det)
        #print "Bbox",time.time()-t
        #t=time.time()
        if cluster>0:
        #    t=time.time()   
            self.det=self.cluster(self.det,ovr=cluster,maxcl=50,inclusion=inclusion)
        #    print "Cluster",time.time()-t
        if rawdet:
        #    t=time.time()
            self.det=self.rawdet(self.det)
        #    print "Rawdet",time.time()-t
        if show:
        #    t=time.time()
            self.show(self.det)
        #    print "Show",time.time()-t
        if show=="Parts":
        #    t=time.time()
            self.show(self.det,parts=True)
        #    print "Show Parts",time.time()-t
        return self.det
   
    def doalltrain(self,gtbbox,thr=-numpy.inf,rank=numpy.inf,refine=True,rawdet=True,show=False,mpos=0,posovr=0.5,numpos=1,numneg=10,minnegovr=0,minnegincl=0,cl=0,emptybb=False):
        """
        executes all the detection steps for training
        """        
        t=time.time()
        self.det=self.select_fast(thr,cl=cl)
        #print "Select time:",time.time()-t
        t=time.time()
        self.det=self.rank_fast(self.det,rank,cl=cl) 
        #print "Rank time:",time.time()-t
        if refine:
            t=time.time()
            self.det=self.refine(self.det)
        #    print "Refine time:",time.time()-t
        t=time.time()
        self.det=self.bbox(self.det)
        #print "BBox time:",time.time()-t
        t=time.time()
        self.best,self.worste=self.getbestworste(self.det,gtbbox,numpos=numpos,numneg=numneg,mpos=mpos,posovr=posovr,minnegovr=minnegovr,minnegincl=minnegincl,emptybb=emptybb)
        #print "Bestworse time:",time.time()-t
        if rawdet:
            t=time.time()
            self.best=self.rawdet(self.best)
            self.worste=self.rawdet(self.worste)
        #    print "Raw Det time:",time.time()-t
        if show:
            self.show(self.best,colors=["b"])
            self.show(self.worste,colors=["r"])
            self.showBBox(gtbbox)
        if show=="Parts":
            self.show(self.best,parts=True)
            self.show(self.worste,parts=True)
        return self.best,self.worste

    def select(self,thr=0,cl=0,dense=DENSE):
        """
        select the best detections
        """
        det=[]
        initr=self.sample
        for i in range(len(self.scr)):
            if len(self.scr)-i<dense:
                initr=0
            cy,cx=numpy.where(self.scr[i]>thr)
            for l in range(len(cy)):
                mcy=(cy[l])*(2*initr+1)-self.fy+1+initr
                mcx=(cx[l])*(2*initr+1)-self.fx+1+initr
                det.append({"i":i,"py":cy[l],"px":cx[l],"scr":self.scr[i][cy[l],cx[l]],"ry":mcy,"rx":mcx,"scl":self.scale[i+self.f.starti],"fy":self.fy,"fx":self.fx,"cl":cl})
        return det

    def select_fast(self,thr=0,cl=0,dense=DENSE):
        """
        select the best detections in a faster way
        """
        det=[];mcy=[];mcx=[];ii=[];ir=[]
        for i in range(len(self.scr)):
            if len(self.scr)-i<dense:
                initr=0
            else:
                initr=self.sample
            cy,cx=numpy.where(self.scr[i]>thr)
            mcy+=(cy).tolist()
            mcx+=(cx).tolist()
            ii+=(i*numpy.ones(len(cy),dtype=numpy.int)).tolist()
            det+=self.scr[i][cy,cx].tolist()
            ir+=((initr*numpy.ones(len(cy)) ).tolist())
        return det,mcy,mcx,ii,ir

    def compare(self,a, b):
        return cmp(b["scr"], a["scr"]) # compare as integers

    def rank(self,det,maxnum=1000):
        """
           rank detections based on score
        """
        rdet=det[:]
        rdet.sort(self.compare)
        if maxnum==numpy.inf:
            maxnum=len(rdet)
        return rdet[:maxnum]

    def rank_fast(self,detx,maxnum=1000,cl=0,dense=DENSE):
        """
           rank detections based on score fast
        """
        rdet=[]
        det=detx[0]
        cy=detx[1]
        cx=detx[2]
        i=detx[3]
        initr=numpy.array(detx[4])
        pos=numpy.argsort(-numpy.array(det))      
        if maxnum==numpy.inf:
            maxnum=len(rdet)
        mcy=numpy.array(cy)*(2*initr+1)-self.fy+1+initr
        mcx=numpy.array(cx)*(2*initr+1)-self.fx+1+initr
        for l in pos[:maxnum]:
            rdet.append({"i":i[l],"py":cy[l],"px":cx[l],"scr":det[l],"ry":mcy[l],"rx":mcx[l],"scl":self.scale[i[l]+self.f.starti],"fy":self.fy,"fx":self.fx,"cl":cl})
        return rdet

    def refine(self,ldet):
        """
            refine the localization of the object based on higher resolutions
        """
        rdet=[]
        for item in ldet:
            i=item["i"];cy=item["py"];cx=item["px"];
            el=item.copy()
            el["ny"]=el["ry"]
            el["nx"]=el["rx"]
            mov=numpy.zeros(2)
            el["def"]={"dy":numpy.zeros(self.pos[i].shape[1]),"dx":numpy.zeros(self.pos[i].shape[1])}
            for l in range(self.pos[i].shape[1]):
                aux=self.pos[i][:,l,cy,cx]#[cy,cx,:,l]
                el["def"]["dy"][l]=aux[0]
                el["def"]["dx"][l]=aux[1]
                mov=mov+aux*2**(-l)
            el["ry"]+=mov[0]
            el["rx"]+=mov[1]
            rdet.append(el)
        return rdet

    def bbox(self,det,redy=0,redx=0):
        """
        convert a list of detections in (id,y1,x1,y2,x2,scr)
        """
        bb=[]
        for el in det:
            l=el.copy()
            y1=l["ry"]/l["scl"]*self.sbin
            x1=l["rx"]/l["scl"]*self.sbin
            y2=(l["ry"]+self.fy)/l["scl"]*self.sbin
            x2=(l["rx"]+self.fx)/l["scl"]*self.sbin
            if l.has_key("endy"):
                y2=(l["endy"])/l["scl"]*self.sbin
                x2=(l["endx"])/l["scl"]*self.sbin
            l["bbox"]=[y1,x1,y2,x2]
            bb.append(l)
        return bb

    def cluster(self,det,ovr=0.5,maxcl=20,inclusion=False):
        """
        cluster detection with a minimum area k of overlapping
        """
        cllist=[]
        for ls in det:
            found=False
            for cl in cllist:
                for cle in cl:
                    if not(inclusion):
                        myovr=util.overlap(ls["bbox"],cle["bbox"])
                    else:   
                        myovr=util.inclusion(ls["bbox"],cle["bbox"])
                    if myovr>ovr:
                        cl.append(ls)
                        found=True
                        break
            if not(found):
                if len(cllist)<maxcl:
                    cllist.append([ls])
                else:
                    break
        return [el[0] for el in cllist]

    def rawdet(self,det):
        """
        extract features from detections and store in "feat"
        """        
        rdet=det[:]
        hogdim=31
        if self.trunc:
            hogdim=32
        for item in det:
            i=item["i"];cy=item["ny"];cx=item["nx"];
            fy=self.fy
            fx=self.fx
            item["feat"]=[]
            my=0;mx=0;
            for l in range(len(item["def"]["dy"])):
                if i+self.f.starti-(l)*self.interv>=0:
                    my=2*my+item["def"]["dy"][l]
                    mx=2*mx+item["def"]["dx"][l]
                    aux=getfeat(self.f.hog[i+self.f.starti-(l)*self.interv],cy+my-1,cy+my+fy*2**l-1,cx+mx-1,cx+mx+fx*2**l-1,self.trunc)
                    item["feat"].append(aux)
                    cy=(cy)*2
                    cx=(cx)*2
                else:
                    item["feat"].append(numpy.zeros((fy*2**l,fx*2**l,hogdim)))
        return rdet


    def show(self,ldet,parts=False,colors=["w","r","g","b"],thr=-numpy.inf,maxnum=numpy.inf,scr=True,cls=None):
        """
        show the detections in an image
        """        
        ar=[5,4,2]
        count=0
        for item in ldet:
            nlev=0
            if item.has_key("def"):
                nlev=len(item["def"]["dy"])
            if item["scr"]>thr:
                bbox=item["bbox"]
                if parts:
                    d=item["def"]
                    scl=item["scl"]
                    mx=0
                    my=0
                    for l,val in enumerate(d["dy"]):
                        my+=d["dy"][l]*2**-l
                        mx+=d["dx"][l]*2**-l
                        y1=(item["ny"]+my)*self.f.sbin/scl
                        x1=(item["nx"]+mx)*self.f.sbin/scl
                        y2=(item["ny"]+my+item["fy"])*self.f.sbin/scl
                        x2=(item["nx"]+mx+item["fx"])*self.f.sbin/scl
                        pylab.fill([x1,x1,x2,x2,x1],[y1,y2,y2,y1,y1],colors[1+l], alpha=0.1, edgecolor=colors[1+l],lw=ar[l],fill=False)        
                util.box(bbox[0],bbox[1],bbox[2],bbox[3],colors[0],lw=2)
                if item["i"]-(nlev-1)*self.interv>=-self.f.starti:#no occlusion
                    strsmall=""
                else:
                    strsmall="S%d"%(-((item["i"]+self.f.starti-(nlev-1)*self.interv)/self.interv))
                if scr:
                    if cls!=None:
                        pylab.text(bbox[1],bbox[0],"%d %.3f %s"%(item["cl"],item["scr"],cls),bbox=dict(facecolor='w', alpha=0.5),fontsize=10)
                    else:
                        if item["cl"]==0:
                            pylab.text(bbox[1],bbox[0],"%.3f %s"%(item["scr"],strsmall),bbox=dict(facecolor='w',alpha=0.5),fontsize=10)
                        else:
                            pylab.text(bbox[1],bbox[0],"%d %.3f %s"%(item["cl"],item["scr"],strsmall),bbox=dict(facecolor='w', alpha=0.5),fontsize=10)                            
            count+=1
            if count>maxnum:
                break
            
    def descr(self,det,flip=False,usemrf=False,usefather=False,k=0):
        """
        convert each detection in a feature descriptor for the SVM
        """           
        ld=[]
        for item in det:
            d=numpy.array([])
            for l in range(len(item["feat"])):
                if not(flip):
                    aux=item["feat"][l]
                else:
                    aux=hogflip(item["feat"][l])
                d=numpy.concatenate((d,aux.flatten()))
                if self.occl:
                    if item["i"]-l*self.interv>=-self.f.starti:
                        d=numpy.concatenate((d,[0.0]))
                    else:
                        d=numpy.concatenate((d,[1.0*SMALL]))
            ld.append(d.astype(numpy.float32))
        return ld

    def mixture(self,det): 
        """
        returns the mixture number if the detector is a mixture of models
        """    
        ld=[]
        for item in det:
            ld.append(item["cl"])
        return ld

    def model(self,descr,rho,lev,fsz,fy=[],fx=[],usemrf=False,usefather=False):
        """
        build a new model from the weights of the SVM
        """     
        ww=[]  
        p=0
        occl=[0]*lev
        if fy==[]:
            fy=self.fy
        if fx==[]:
            fx=self.fx
        d=descr
        for l in range(lev):
            dp=(fy*fx)*4**l*fsz
            ww.append((d[p:p+dp].reshape((fy*2**l,fx*2**l,fsz))).astype(numpy.float32))
            p+=dp
            if self.occl:
                occl[l]=d[p]
                p+=1
        m={"ww":ww,"rho":rho,"fy":fy,"fx":fx,"occl":occl}
        return m

    def getbestworste(self,det,gtbbox,numpos=1,numneg=10,posovr=0.5,negovr=0.2,mpos=0,minnegovr=0,minnegincl=0,emptybb=True):
        """
        returns the detection that best overlap with the ground truth and also the best not overlapping
        """    
        lpos=[]
        lneg=[]
        lnegfull=False
        for gt in gtbbox:
            lpos.append(gt.copy())
            lpos[-1]["scr"]=-numpy.inf
            lpos[-1]["ovr"]=1.0
        for d in det:
            goodneg=True
            for gt in lpos: 
                ovr=util.overlap(d["bbox"],gt["bbox"])
                incl=util.inclusion(d["bbox"],gt["bbox"])
                if ovr>posovr:
                    if d["scr"]-mpos*(1-ovr)>gt["scr"]-mpos*(1-gt["ovr"]):
                        gt["scr"]=d["scr"]
                        gt["ovr"]=ovr
                        gt["data"]=d.copy()
                if ovr>negovr or ovr<minnegovr or incl<minnegincl:
                    goodneg=False
            if goodneg and not(lnegfull):
                noovr=True
                for n in lneg:
                    ovr=util.overlap(d["bbox"],n["bbox"])
                    if ovr>0.5:
                        noovr=False
                if noovr:
                    if len(lneg)>=numneg:   
                        lnegfull=True
                    else:
                        lneg.append(d)
        lpos2=[]
        for idbbox,gt in enumerate(lpos):
            if gt["scr"]>-numpy.inf:
                lpos2.append(gt["data"])
                lpos2[-1]["ovr"]=gt["ovr"]
                lpos2[-1]["gtbb"]=gt["bbox"]
                lpos2[-1]["bbid"]=idbbox
                if gt.has_key("img"):
                    lpos2[-1]["img"]=gt["img"]
            else:
                if emptybb:
                    lpos2.append({"scr":-10,"bbox":gt["bbox"],"notfound":True})#not detected bbox
        return lpos2,lneg

    def goodsamples(self,det,initr,ratio):
        f=self.f
        samples=[]
        for i in range(0,len(f.hog)):
            samples.append(numpy.mgrid[-self.fy+initr:f.hog[i].shape[0]+1:1+2*initr,-self.fx+initr:f.hog[i].shape[1]+1:1+2*initr].astype(c_int))
            csamples=samples[-1][0,:,:].copy()
            samples[-1][0,:,:]=-1000
            for d in det:
                if d["i"]==i-f.starti:
                    samples[-1][0,d["py"],d["px"]]=csamples[d["py"],d["px"]]      
        return samples

class TreatDef(Treat):

    def refine(self,ldet):
        """
            refine the localization of the object based on higher resolutions
        """
        rdet=[]
        for item in ldet:
            i=item["i"];cy=item["py"];cx=item["px"];
            el=item.copy()
            el["ny"]=el["ry"]
            el["nx"]=el["rx"]
            mov=numpy.zeros((1,1,2))
            el["def"]={"dy":[],"dx":[],"ddy":[],"ddx":[],"party":[],"partx":[]}
            for l in range(len(self.pos[i])):
                aux=self.pos[i][l][:,:,:,cy,cx]
                el["def"]["dy"].append(aux[:,:,0])
                el["def"]["dx"].append(aux[:,:,1])
                el["def"]["ddy"].append(aux[:,:,2])
                el["def"]["ddx"].append(aux[:,:,3])
                mov=mov+aux[:,:,:2]*2**(-l)
                el["def"]["party"].append(el["ny"]+mov[:,:,0])
                el["def"]["partx"].append(el["nx"]+mov[:,:,1])
                aux1=numpy.kron(mov.T,[[1,1],[1,1]]).T
                aux2=numpy.zeros((2,2,2))
                aux2[:,:,0]=numpy.array([[0,0],[self.fy*2**-(l+1),self.fy*2**-(l+1)]])
                aux2[:,:,1]=numpy.array([[0,self.fx*2**-(l+1)],[0,self.fx*2**-(l+1)]])
                aux3=numpy.kron(numpy.ones((2**l,2**l)),aux2.T).T
                mov=aux1+aux3
            el["ry"]=numpy.min(el["def"]["party"][-1])
            el["rx"]=numpy.min(el["def"]["partx"][-1])
            el["endy"]=numpy.max(el["def"]["party"][-1])+self.fy*(2**-(l))
            el["endx"]=numpy.max(el["def"]["partx"][-1])+self.fx*(2**-(l))
            rdet.append(el)
        return rdet

    def rawdet(self,det):
        """
        extract features from detections and store in "feat"
        """        
        rdet=det[:]
        hogdim=31
        if self.trunc:
            hogdim=32
        for item in det:
            i=item["i"];cy=item["ny"];cx=item["nx"];
            fy=self.fy
            fx=self.fx
            item["feat"]=[]
            mov=numpy.zeros((1,1,2))
            for l in range(len(item["def"]["party"])):
                sz=2**l
                aux=numpy.zeros((fy*sz,fx*sz,hogdim))
                if i+self.f.starti-(l)*self.interv>=0:
                    for py in range(sz):
                        for px in range(sz):
                            mov[py,px,0]=2*mov[py,px,0]+item["def"]["dy"][l][py,px]
                            mov[py,px,1]=2*mov[py,px,1]+item["def"]["dx"][l][py,px]
                            aux[py*fy:(py+1)*fy,px*fx:(px+1)*fx,:]=getfeat(self.f.hog[i+self.f.starti-(l)*self.interv],cy+mov[py,px,0]-1,cy+mov[py,px,0]+fy-1,cx+mov[py,px,1]-1,cx+mov[py,px,1]+fx-1,self.trunc)
                    cy=(cy)*2
                    cx=(cx)*2
                    aux1=numpy.kron(mov.T,[[1,1],[1,1]]).T
                    aux2=numpy.zeros((2,2,2))
                    aux2[:,:,0]=numpy.array([[0,0],[self.fy/2.0,self.fy/2.0]])
                    aux2[:,:,1]=numpy.array([[0,self.fx/2.0],[0,self.fx/2.0]])
                    aux3=numpy.kron(numpy.ones((2**l,2**l)),aux2.T).T
                    mov=aux1+aux3
                item["feat"].append(aux)
        return rdet


    def show(self,ldet,parts=False,colors=["w","r","g","b"],thr=-numpy.inf,maxnum=numpy.inf,scr=True,cls=None):
        """
        show the detections in an image
        """  
        ar=[5,4,2]
        count=0
        if parts:
            for item in ldet:
                if item["scr"]>thr:
                    scl=item["scl"]
                    for l in range(len(item["def"]["dy"])):
                        py=item["def"]["party"][l]
                        px=item["def"]["partx"][l]
                        for lpy in range(py.shape[0]):
                            for lpx in range(px.shape[1]):
                                y1=py[lpy,lpx]*self.f.sbin/scl
                                y2=(py[lpy,lpx]+item["fy"]*2**-l)*self.f.sbin/scl
                                x1=px[lpy,lpx]*self.f.sbin/scl
                                x2=(px[lpy,lpx]+item["fx"]*2**-l)*self.f.sbin/scl
                                pylab.fill([x1,x1,x2,x2,x1],[y1,y2,y2,y1,y1],colors[1+l], alpha=0.1, edgecolor=colors[1+l],lw=ar[l],fill=False)                               
                count+=1
                if count>maxnum:
                    break
        Treat.show(self,ldet,colors=colors,thr=thr,maxnum=maxnum,scr=scr,cls=cls)        

    def descr(self,det,flip=False,usemrf=True,usefather=True,k=K):
        """
        convert each detection in a feature descriptor for the SVM
        """      
        ld=[]
        for item in det:
            d=numpy.array([])
            for l in range(len(item["feat"])):
                if not(flip):
                    d=numpy.concatenate((d,item["feat"][l].flatten()))       
                    if l>0: #skip deformations level 0
                        if usefather:
                            d=numpy.concatenate((d, k*k*(item["def"]["dy"][l].flatten()**2)  ))
                            d=numpy.concatenate((d, k*k*(item["def"]["dx"][l].flatten()**2)  ))
                        if usemrf:
                            d=numpy.concatenate((d,k*k*item["def"]["ddy"][l].flatten()))
                            d=numpy.concatenate((d,k*k*item["def"]["ddx"][l].flatten()))
                else:
                    d=numpy.concatenate((d,hogflip(item["feat"][l]).flatten()))        
                    if l>0: #skip deformations level 0
                        if usefather:
                            aux=(k*k*(item["def"]["dy"][l][:,::-1]**2))#.copy()
                            d=numpy.concatenate((d,aux.flatten()))
                            aux=(k*k*(item["def"]["dx"][l][:,::-1]**2))#.copy()
                            d=numpy.concatenate((d,aux.flatten()))
                        if usemrf:
                            aux=defflip(k*k*item["def"]["ddy"][l])
                            d=numpy.concatenate((d,aux.flatten()))
                            aux=defflip(k*k*item["def"]["ddx"][l])
                            d=numpy.concatenate((d,aux.flatten()))
                if self.occl:
                    if item["i"]-l*self.interv>=-self.f.starti:
                        d=numpy.concatenate((d,[0.0]))
                    else:
                        d=numpy.concatenate((d,[1.0*SMALL]))
            ld.append(d.astype(numpy.float32))
        return ld

    def model(self,descr,rho,lev,fsz,fy=[],fx=[],mindef=0.001,usemrf=True,usefather=True): 
        """
        build a new model from the weights of the SVM
        """     
        ww=[]  
        df=[]
        occl=[0]*lev
        if fy==[]:
            fy=self.fy
        if fx==[]:
            fx=self.fx
        p=0
        d=descr
        for l in range(lev):
            dp=(fy*fx)*4**l*fsz
            ww.append((d[p:p+dp].reshape((fy*2**l,fx*2**l,fsz))).astype(numpy.float32))
            p+=dp
            if l>0: #skip level 0
                ddp=4**l
                aux=numpy.zeros((2**l,2**l,4))
                if usefather:
                    aux[:,:,0]=d[p:p+ddp].reshape((2**l,2**l))
                    p+=ddp
                    aux[:,:,1]=d[p:p+ddp].reshape((2**l,2**l))
                    p+=ddp
                if usemrf:
                    aux[:,:,2]=d[p:p+ddp].reshape((2**l,2**l))
                    p+=ddp
                    aux[:,:,3]=d[p:p+ddp].reshape((2**l,2**l))
                    p+=ddp
                df.append(aux.astype(numpy.float32))
            else:
                df.append(numpy.zeros((2**l,2**l,4),dtype=numpy.float32))
            if self.occl:
                occl[l]=d[p]
                p+=1
        m={"ww":ww,"rho":rho,"fy":fy,"fx":fx,"df":df,"occl":occl}
        return m

import time

def detect(f,m,gtbbox=None,auxdir=".",hallucinate=1,initr=1,ratio=1,deform=False,bottomup=False,usemrf=False,numneg=0,thr=-2,posovr=0.7,minnegincl=0.5,small=True,show=False,cl=0,mythr=-10,nms=0.5,inclusion=False,usefather=True,mpos=1,emptybb=False,useprior=False,K=1.0,occl=False,trunc=0):
    """Detect objects in an image
        used for both test --> gtbbox=None
        and trainig --> gtbbox = list of bounding boxes
    """
    ff.setK(K)#set the degree of deformation
    if useprior:
        numrank=200
    else:
        numrank=1000
    if gtbbox!=None and gtbbox!=[] and useprior:
        t1=time.time()
        pr=f.buildPrior(gtbbox,m["fy"],m["fx"])
        print "Prior Time:",time.time()-t1
    else:
        pr=None
    t=time.time()        
    f.resetHOG()
    if deform:
        if bottomup:
            scr,pos=f.scanRCFLDefBU(m,initr=initr,ratio=ratio,small=small,usemrf=usemrf)
        else:
            #scr,pos=f.scanRCFLDefThr(m,initr=initr,ratio=ratio,small=small,usemrf=usemrf,mythr=mythr)
            scr,pos=f.scanRCFLDef(m,initr=initr,ratio=ratio,small=small,usemrf=usemrf,trunc=trunc)
        tr=TreatDef(f,scr,pos,initr,m["fy"],m["fx"],occl=occl,trunc=trunc)
    else:
        scr,pos=f.scanRCFL(m,initr=initr,ratio=ratio,small=small,trunc=trunc)
        tr=Treat(f,scr,pos,initr,m["fy"],m["fx"],occl=occl,trunc=trunc)
    print "Scan: %.3f s"%(time.time()-t)    
    if gtbbox==None:#test
        if show==True:
            showlabel="Parts"
        else:
            showlabel=False
        ref=0
        if ref:
            t1=time.time()
            det=tr.doall(thr=thr,rank=200,refine=True,rawdet=False,cluster=False,show=False,inclusion=inclusion,cl=cl)
            samples=tr.goodsamples(det,initr=initr,ratio=ratio)
            scr,pos=f.scanRCFLDefBU(m,initr=initr,ratio=ratio,small=small,usemrf=usemrf,mysamples=samples)
            print "Refine Time:",time.time()-t1
            tr=TreatDef(f,scr,pos,initr,m["fy"],m["fx"])
            det=tr.doall(thr=thr,rank=100,refine=True,rawdet=False,cluster=nms,show=False,inclusion=inclusion,cl=cl)
        else:
            det=tr.doall(thr=thr,rank=100,refine=True,rawdet=False,cluster=nms,show=False,inclusion=inclusion,cl=cl)
        numhog=f.getHOG()
        dettime=time.time()-t

        if show==True:
            tr.show(det,parts=showlabel,thr=-1.0,maxnum=5)           
        return tr,det,dettime,numhog
    else:#training
        t2=time.time()
        best1,worste1=tr.doalltrain(gtbbox,thr=thr,rank=1000,show="Parts",mpos=mpos,numpos=1,posovr=posovr,numneg=numneg,minnegovr=0,minnegincl=minnegincl,cl=cl,emptybb=emptybb)        
        ipos=[];ineg=[]
        print "Treat Time:",time.time()-t2
        print "Detect: %.3f s"%(time.time()-t)
        return tr,best1,worste1,ipos,ineg

