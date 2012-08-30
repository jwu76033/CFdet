import matplotlib
matplotlib.use("Agg") #if run out of ipython do not show any graph
#from procedures import *
from database import *
from multiprocessing import Pool
import util
import pyrHOG2
import pyrHOG2RL
import VOCpr
import model
import time
import copy
import itertools

approx=0.0001 #there should be some problem with BOW because it should be 0.0001

class config(object):
    pass

class stats(object):
    """
    keep track of interesting variables    
    """
    def __init__(self,l):
        self.l=l

    def listvar(self,l):
        """
        set the list of variables [{"name":name1,"fct":fct1,"txt":descr1},[name2,fct2,descr2],..,[nameN,fctN,descrN]]
        """
        self.l=l

    def report(self,filename,mode="a",title=None):
                
        f=open(filename,mode)
        if title!=None:
            f.write("---%s "%title+time.asctime()+"------\n")
        else:
            f.write("---Stats on "+time.asctime()+"------\n")
        for v in self.l:     
            #if v["name"] in dir()       
            if v.has_key("fnc"):
                exec("value=str(%s(%s))"%(v["fnc"],v["name"]))
            else:
                if v["name"][-1]=="*":
                    exec("value=str(%s.__dict__)"%(v["name"][:-1]))
                else:
                    exec("value=str(%s)"%(v["name"]))
            #else 
            #    value="Not Exists!"
            if v.has_key("txt"):
                f.write("%s=%s\n"%(v["txt"],value))
            else:
                f.write("%s=%s\n"%(v["name"],value))
        f.close()

def remove_empty(seq):
    newseq=[]
    for l in seq:
        if l!=[]:
            newseq.append(l)
    return newseq

#get image name and bbox
def extractInfo(trPosImages,maxnum=-1,usetr=True,usedf=False):
    bb=numpy.zeros((len(trPosImages)*20,4))#as maximum 5 persons per image in average
    name=[]
    cnt=0
    tot=0
    if maxnum==-1:
        tot=len(trPosImages)
    else:
        tot=min(maxnum,trPosImages)
    for idx in range(tot):
        #print trPosImages.getImageName(idx)
        #img=trPosImages.getImage(idx)
        rect=trPosImages[idx]["bbox"]#.getBBox(idx,usetr=usetr,usedf=usedf)
        for r in rect:
            bb[cnt,:]=r[:4]
            name.append(trPosImages[idx]["name"])#.getImageName(idx))
            cnt+=1
        #img=pylab.imread("circle.png")
        util.pdone(idx,tot)
    ratio=(bb[:,2]-bb[:,0])/(bb[:,3]-bb[:,1])
    area=(bb[:,2]-bb[:,0])*(bb[:,3]-bb[:,1])
    return name,bb[:cnt,:],ratio[:cnt],area[:cnt]

#def initalPos(model,name,ratio,area,cfg):
#    bb=numpy.zeros((len(trPosImages)*20,4))#as maximum 5 persons per image in average
#    name=[]
#    cnt=0
#    tot=0
#    if maxnum==-1:
#        tot=len(trPosImages)
#    else:
#        tot=min(maxnum,trPosImages)
#    for idx in range(tot):
#        #print trPosImages.getImageName(idx)
#        #img=trPosImages.getImage(idx)
#        rect=trPosImages[idx]["bbox"]#.getBBox(idx,usetr=usetr,usedf=usedf)
#        for r in rect:
#            bb[cnt,:]=r[:4]
#            name.append(trPosImages[idx]["name"])#.getImageName(idx))
#            cnt+=1
#        #img=pylab.imread("circle.png")
#        util.pdone(idx,tot)
#    ratio=(bb[:,2]-bb[:,0])/(bb[:,3]-bb[:,1])
#    area=(bb[:,2]-bb[:,0])*(bb[:,3]-bb[:,1])
#    ######
#    import scipy.misc.pilutil as pil
#    masp=[]
#    for l in model:
#        masp.append(model[0]["ww"].shape[0]/float(model[0]["ww"].shape[1]))
#    for l,idl in enumerate(name):
#        im=util.myimread(l)
#        #cim=im[bb[idl,0]-cfg.sbin:bb[idl,1]+cfg.sbin,bb[idl,2]-cfg.sbin:bb[idl,3]+cfg.sbin]
#        sy=bb[idl,2]-bb[idl,0]
#        sx=bb[idl,3]-bb[idl,1]
#        #cim=getfeat(im,bb[idl,0]-*0.1,bb[idl,1]+cfg.sbin,bb[idl,2]-cfg.sbin,bb[idl,3]+cfg.sbin)
#        cim=im[:,:]
#        asp=nump.argmin(masp-ratio)
#        rim=pil.imresize(cim,(model[asp]["ww"][-1].shape[0]*cfg.sbin,model[asp]["ww"][-1].shape[1]*cfg.sbin))
#        fhog=
#    return 


def buildense(trpos,trposcl,cumsize,bias):
    ftrpos=[]
    for iel,el in enumerate(trpos):
        ftrpos.append(numpy.zeros(cumsize[-1],dtype=numpy.float32))
        ftrpos[-1][cumsize[trposcl[iel]]:cumsize[trposcl[iel]+1]-1]=trpos[iel]
        #bias
        ftrpos[-1][cumsize[trposcl[iel]+1]-1]=bias
    return ftrpos    

def clear(keep=("__builtins__", "clear")):
    keeps = {}
    for name, value in globals().iteritems():
        if name in keep: keeps[name] = value
        globals().clear()
        for name, value in keeps.iteritems():
            globals()[name] = value

#def detectWrap(a):
#    i=a[0]
#    imname=a[1]
#    bbox=a[2]
#    models=a[3]
#    cfg=a[4]
#    if len(a)<=5:
#        imageflip=False
#    else:
#        imageflip=a[5]
#    img=util.myimread(imname,resize=cfg.resize)
#    if imageflip:
#        img=util.myimread(imname,True,resize=cfg.resize)
#        if bbox!=None:
#             bbox = util.flipBBox(img,bbox)
#    if bbox!=None:
#        gtbbox=[{"bbox":x,"img":imname.split("/")[-1]} for x in bbox]   
#    else:
#        gtbbox=None
#    if cfg.show:
#        img=util.myimread(imname,imageflip,resize=cfg.resize)
#        pylab.figure(10)
#        pylab.ioff()
#        pylab.clf()
#        pylab.axis("off")
#        pylab.imshow(img,interpolation="nearest",animated=True) 
#    notsave=False
#    #if cfg.__dict__.has_key("test"):
#    #    notsave=cfg.test
#    #f=pyrHOG2.pyrHOG(imname,interv=10,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=cfg.hallucinate,cformat=True,flip=imageflip,resize=cfg.resize)
#    f=pyrHOG2.pyrHOG(img,interv=10,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=cfg.hallucinate,cformat=True)#,flip=imageflip,resize=cfg.resize)
#    res=[]
#    for clm,m in enumerate(models):
#        if cfg.useRL:
#            res.append(pyrHOG2RL.detectflip(f,m,gtbbox,hallucinate=cfg.hallucinate,initr=cfg.initr,ratio=cfg.ratio,deform=cfg.deform,bottomup=cfg.bottomup,usemrf=cfg.usemrf,numneg=cfg.numneg,thr=cfg.thr,posovr=cfg.posovr,minnegincl=cfg.minnegincl,small=cfg.small,show=cfg.show,cl=clm,mythr=cfg.mythr,mpos=cfg.mpos,usefather=cfg.usefather,useprior=cfg.useprior,K=cfg.k))
#        else:
#            res.append(pyrHOG2.detect(f,m,gtbbox,hallucinate=cfg.hallucinate,initr=cfg.initr,ratio=cfg.ratio,deform=cfg.deform,bottomup=cfg.bottomup,usemrf=cfg.usemrf,numneg=cfg.numneg,thr=cfg.thr,posovr=cfg.posovr,minnegincl=cfg.minnegincl,small=cfg.small,show=cfg.show,cl=clm,mythr=cfg.mythr,mpos=cfg.mpos,usefather=cfg.usefather,useprior=cfg.useprior,emptybb=False,K=cfg.k))
#    if cfg.show:
#        pylab.draw()
#        pylab.show()
#    return res

def rundet(img,cfg,models,gtbbox):
    if cfg.show:
        #img=util.myimread(imname,imageflip,resize=cfg.resize)
        pylab.figure(10)
        pylab.ioff()
        pylab.clf()
        pylab.axis("off")
        pylab.imshow(img,interpolation="nearest",animated=True) 
    notsave=False
    #if cfg.__dict__.has_key("test"):
    #    notsave=cfg.test
    #f=pyrHOG2.pyrHOG(imname,interv=10,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=cfg.hallucinate,cformat=True,flip=imageflip,resize=cfg.resize)
    f=pyrHOG2.pyrHOG(img,interv=10,savedir=cfg.auxdir+"/hog/",notsave=not(cfg.savefeat),notload=not(cfg.loadfeat),hallucinate=cfg.hallucinate,cformat=True)#,flip=imageflip,resize=cfg.resize)
    res=[]
    for clm,m in enumerate(models):
        if cfg.useRL:
            res.append(pyrHOG2RL.detectflip(f,m,gtbbox,hallucinate=cfg.hallucinate,initr=cfg.initr,ratio=cfg.ratio,deform=cfg.deform,
bottomup=cfg.bottomup,usemrf=cfg.usemrf,numneg=cfg.numneg,thr=cfg.thr,posovr=cfg.posovr,
minnegincl=cfg.minnegincl,small=cfg.small,show=cfg.show,cl=clm,mythr=cfg.mythr,mpos=cfg.mpos,
usefather=cfg.usefather,useprior=cfg.useprior,K=cfg.k,occl=cfg.occl,fastBU=cfg.fastBU,usebow=cfg.usebow,ranktr=cfg.ranktr,CRF=cfg.CRF,small2=cfg.small2))
        else:
            res.append(pyrHOG2.detect(f,m,gtbbox,hallucinate=cfg.hallucinate,initr=cfg.initr,ratio=cfg.ratio,deform=cfg.deform,
bottomup=cfg.bottomup,usemrf=cfg.usemrf,numneg=cfg.numneg,thr=cfg.thr,posovr=cfg.posovr,
minnegincl=cfg.minnegincl,small=cfg.small,show=cfg.show,cl=clm,mythr=cfg.mythr,mpos=cfg.mpos,
usefather=cfg.usefather,useprior=cfg.useprior,K=cfg.k,occl=cfg.occl,fastBU=cfg.fastBU,usebow=cfg.usebow,ranktr=cfg.ranktr,CRF=cfg.CRF,small2=cfg.small2))
    if cfg.show:
        pylab.draw()
        pylab.show()
    return res

def detectWrap(a):
    i=a[0]
    imname=a[1]
    bbox=a[2]
    models=a[3]
    cfg=a[4]
    if len(a)<=5:
        imageflip=False
    else:
        imageflip=a[5]
    img=util.myimread(imname,resize=cfg.resize)
    if imageflip:
        img=util.myimread(imname,True,resize=cfg.resize)
        if bbox!=None:
             bbox = util.flipBBox(img,bbox)
    if bbox!=None:
        if bbox!=[]:#positive
            cfg.usecrop=False
            gtbbox=[{"bbox":numpy.array(x[:6])*cfg.resize,"img":imname.split("/")[-1]} for x in bbox]   
            if cfg.usecrop:          
                tres=[]
                res=[]
                for x in bbox:
                    margin=0.3
                    dy=x[2]-x[0];dx=x[3]-x[1]
                    dd=max(dy,dx)
                    ny1=max(0,x[0]-margin*dd);ny2=min(x[2]+margin*dd,img[0].shape)
                    nx1=max(0,x[1]-margin*dd);nx2=min(x[3]+margin*dd,img.shape[1])
                    img1=img[ny1:ny2,nx1:nx2]
                    #gt1=[{"bbox":[ny1-x[0]+2*margin*dy,nx1-x[1]+2*margin*dx,ny2-x[0],nx2-x[1],0,0],"img":imname.split("/")[-1]}]
                    gt1=[{"bbox":[x[0]-ny1,x[1]-nx1,x[0]-ny1+dy,x[1]-nx1+dx,0,0],"img":imname.split("/")[-1]}]
                    tres.append(rundet(img1,cfg,models,gt1))
                for cl,mod in enumerate(tres):
                    res.append([[],[],[],[],[]])
                    #tr,best1,worste1,ipos,ineg
                    res[cl][0]=mod[0][0]
                    for el in mod:
                        res[cl][1]+=el[1]
                        res[cl][2]+=el[2]
                        res[cl][3]+=el[3]
                        res[cl][4]+=el[4]
                        if res[cl][1]!=[]:
                            res[cl][1][0]["bbid"]=cl
                        if res[cl][2]!=[]:
                            res[cl][2][0]["bbid"]=cl                
            else:
                res=rundet(img,cfg,models,gtbbox)        
        else:
            res=rundet(img,cfg,models,[])    
    else:
        gtbbox=None
        res=rundet(img,cfg,models,gtbbox)
    return res


def myunique(old,new,oldcl,newcl,numcl):
    if old==[]:
        return new,newcl
    unew=[]
    unewcl=[]
    #mold=numpy.array(old)
    clst=[]
    for c in range(numcl):
        select=numpy.arange(len(oldcl))[numpy.array(oldcl)==c]
        clst.append(numpy.array([old[i] for i in select]))
    for ep,e in enumerate(new):
        #print ep,"/",len(new)
        print ".",
        #check the cluster
        #selec=numpy.arange(len(oldcl))[numpy.array(oldcl)==newcl[ep]]
        apr=numpy.sum(numpy.abs(e[::100]-clst[newcl[ep]][:,::100]),1)
        #print apr
        #raw_input()
        if numpy.all(apr>0.1):
            unew.append(e)
            unewcl.append(newcl[ep])    
        else:
            if numpy.all(numpy.sum(numpy.abs(e-clst[newcl[ep]][apr<=0.1,:]),1)>0.1):
                unew.append(e)
                unewcl.append(newcl[ep]) 
                print ep,"/",len(new)
    print "Doules",len(new)-len(unew)
    #raw_input()
    return [unew,unewcl]

def extract_feat(tr,dtrpos,cumsize,useRL):
    ls=[];lscl=[]
    for el in dtrpos:
        aux=(tr.descr(dtrpos[el],flip=False,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow))
        ls+=aux
        auxcl=tr.mixture(dtrpos[el])
        lscl+=auxcl
        if not(useRL):
            ls+=(tr.descr(dtrpos[el],flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow))
            lscl+=tr.mixture(dtrpos[el])
        if cumsize!=None:
            dns=buildense(aux,auxcl,cumsize,cfg.bias)
            #print "Det:",dtrpos[el][0]["img"],[x["scr"] for x in dtrpos[el]],tr.mixture(dtrpos[el])
            #print "Det:",dtrpos[el][0]["img"],[numpy.sum(x*w)-r for x in dns],tr.mixture(dtrpos[el])
    #if cumsize!=None:    
    #    raw_input()
    return ls,lscl

def extract_feat2(tr,dtrpos,cumsize,useRL):
    ls=[];lscl=[]
    for el in dtrpos:
        aux=(tr.descr(dtrpos[el],flip=False,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow))
        #ls+=aux
        auxcl=tr.mixture(dtrpos[el])
        #lscl+=auxcl
        if not(useRL):
            aux2=(tr.descr(dtrpos[el],flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow))
            auxcl2=tr.mixture(dtrpos[el])
        for l in range(len(aux)):
            ls.append(aux[l])
            lscl.append(auxcl[l])
            if not(useRL):
                ls.append(aux2[l])
                lscl.append(auxcl2[l])
        if cumsize!=None:
            dns=buildense(aux,auxcl,cumsize,cfg.bias)
            #print "Det:",dtrpos[el][0]["img"],[x["scr"] for x in dtrpos[el]],tr.mixture(dtrpos[el])
            #print "Det:",dtrpos[el][0]["img"],[numpy.sum(x*w)-r for x in dns],tr.mixture(dtrpos[el])
    #if cumsize!=None:    
    print "Number descr:",len(ls)
    #raw_input()
    return ls,lscl

def loss_pos(trpos,trposcl,cumsize,w):
    dns=buildense(trpos,trposcl,cumsize,cfg.bias)
    loss=0
    lscr=[]
    for l in dns:
        scr=numpy.sum(l*w)
        print "Scr:",scr
        loss+=max(0,1-scr)
        lscr.append(scr)
    return loss,lscr

import pegasos

def train(a):
    #import pegasos
    trpos=a[0]
    trneg=a[1]
    trposcl=a[2]
    trnegcl=a[3]
    w=a[4]
    testname=a[5]
    svmc=a[6]
    #k=a[7]
    #numthr=a[8]
    w,r,prloss=pegasos.trainComp(trpos,trneg,testname+"loss.rpt.txt",trposcl,trnegcl,oldw=w,dir="",pc=svmc,eps=0.01)
    return w,r,prloss

def trainParallel(trpos,trneg,testname,trposcl,trnegcl,w,svmc,multipr,parallel=True,numcore=4):
    
    if not(parallel):
        w,r,prloss=pegasos.trainComp(trpos,trneg,testname+"loss.rpt.txt",trposcl,trnegcl,oldw=w,dir="",pc=svmc)
    else:
        #atrpos=numpy.array(trpos,dtype=object)
        #atrposcl=numpy.array(trposcl,dtype=object)
        #atrneg=numpy.array(trneg,dtype=object)
        #atrnegcl=numpy.array(trnegcl,dtype=object)
        ltrpos=len(trpos);ltrneg=len(trneg)
        reordpos=range(ltrpos);numpy.random.shuffle(reordpos)
        reordneg=range(ltrneg);numpy.random.shuffle(reordneg)
        ltr=[]
        litpos=ltrpos/numcore;litneg=ltrneg/numcore
        atrpos=[];atrposcl=[]
        atrneg=[];atrnegcl=[]
        for ll in range(ltrpos):
            atrpos.append(trpos[reordpos[ll]])                   
            atrposcl.append(trposcl[reordpos[ll]])                   
        for ll in range(ltrneg):
            atrneg.append(trneg[reordneg[ll]])                   
            atrnegcl.append(trnegcl[reordneg[ll]])                   
        for gr in range(numcore-1):
            ltr.append([atrpos[litpos*gr:litpos*(gr+1)],atrneg[litneg*gr:litneg*(gr+1)],atrposcl[litpos*gr:litpos*(gr+1)],atrnegcl[litneg*gr:litneg*(gr+1)],w,testname,svmc])        
        ltr.append([atrpos[litpos*(gr+1):],atrneg[litneg*(gr+1):],atrposcl[litpos*(gr+1):],atrnegcl[litneg*(gr+1):],w,testname,svmc])        
        if not(multipr):
            itr=itertools.imap(train,ltr)        
        else:
            itr=mypool.map(train,ltr)
        waux=numpy.zeros((numcore,len(w)),dtype=numpy.float32)
        raux=numpy.zeros((numcore))
        #lprloss=[]
        #lenprloss=[]
        for ii,res in enumerate(itr):
            waux[ii]=res[0]
            raux[ii]=res[1]    
        prloss=res[2]#take the last one
        w=numpy.mean(waux,0)
        r=numpy.mean(raux)
    return w,r,prloss

#def trainParallel2(trpos,trneg,testname,trposcl,trnegcl,w,svmc,multipr,parallel=True,numcore=4,mypool=None):
#    
#    if not(parallel):
#        w,r,prloss=pegasos.trainComp(trpos,trneg,testname+"loss.rpt.txt",trposcl,trnegcl,oldw=w,dir="",pc=svmc)
#    else:
#        #atrpos=numpy.array(trpos,dtype=object)
#        #atrposcl=numpy.array(trposcl,dtype=object)
#        #atrneg=numpy.array(trneg,dtype=object)
#        #atrnegcl=numpy.array(trnegcl,dtype=object)
#        ltrpos=len(trpos);ltrneg=len(trneg)
#        reordpos=range(ltrpos);numpy.random.shuffle(reordpos)
#        reordneg=range(ltrneg);numpy.random.shuffle(reordneg)
#        ltr=[]
#        litpos=ltrpos/numcore;litneg=ltrneg/numcore
#        atrpos=[];atrposcl=[]
#        atrneg=[];atrnegcl=[]
#        for ll in range(ltrpos):
#            atrpos.append(trpos[reordpos[ll]])                   
#            atrposcl.append(trposcl[reordpos[ll]])                   
#        for ll in range(ltrneg):
#            atrneg.append(trneg[reordneg[ll]])                   
#            atrnegcl.append(trnegcl[reordneg[ll]])                   
#        for gr in range(numcore-1):
#            ltr.append([atrpos[litpos*gr:litpos*(gr+1)],atrneg[litneg*gr:litneg*(gr+1)],atrposcl[litpos*gr:litpos*(gr+1)],atrnegcl[litneg*gr:litneg*(gr+1)],w,testname,svmc])        
#        ltr.append([atrpos[litpos*(gr+1):],atrneg[litneg*(gr+1):],atrposcl[litpos*(gr+1):],atrnegcl[litneg*(gr+1):],w,testname,svmc])        
#        if not(multipr):
#            itr=itertools.imap(train,ltr)        
#        else:
#            itr=mypool.map(train,ltr)
#        waux=numpy.zeros((numcore,len(w)))
#        raux=numpy.zeros((numcore))
#        #lprloss=[]
#        #lenprloss=[]
#        for ii,res in enumerate(itr):
#            waux[ii]=res[0]
#            raux[ii]=res[1]    
#        prloss=res[2]#take the last one
#        w=numpy.mean(waux,0)
#        r=numpy.mean(raux)
#    return w,r,prloss


if __name__=="__main__":

    import sys
    
    batch=""
    if len(sys.argv)>2: #batch configuration
        batch=sys.argv[2]

    #cfg=config()
    try:
        if batch=="batch":
            print "Loading Batch configuration"
            if len(sys.argv)>3: #batch configuration
                import_name=sys.argv[3]
                #print "The argument is",import_name
                #raw_input()
                exec "from config_%s import *"%import_name
            else:
                from config_local_batch import * #your own configuration
        else:
            print "Loading Normal configuration"
            from config_local_pascal import * #your own configuration    
    except:
        print "config_local.py is not present loading configdef.py"
        from config import * #default configuration  
    
    if len(sys.argv)>1: #class
        cfg.cls=sys.argv[1]
    
    #if cfg.savedir=="":
        #cfg.savedir=InriaPosData(basepath=cfg.dbpath).getStorageDir() #where to save
        #cfg.savedir=VOC07Data(basepath=cfg.dbpath).getStorageDir()

    cfg.testname=cfg.testpath+cfg.cls+("%d"%cfg.numcl)+"_"+cfg.testspec
    cfg.train="keep2"
    util.save(cfg.testname+".cfg",cfg)

    cfg.auxdir=cfg.savedir
    testname=cfg.testname

    if cfg.multipr==1:
        numcore=None
    else:
        numcore=cfg.multipr

    mypool = Pool(numcore)

    stcfg=stats([{"name":"cfg*"}])
    stcfg.report(testname+".rpt.txt","w","Initial Configuration")

    sts=stats(
        [{"name":"it","txt":"Iteration"},
        {"name":"nit","txt":"Negative Iteration"},
        {"name":"trpos","fnc":"len","txt":"Positive Examples"},
        {"name":"trneg","fnc":"len","txt":"Negative Examples"}]
        )

    rpres=stats([{"name":"tinit","txt":"Time from the beginning"},
                {"name":"tpar","txt":"Time last iteration"},
                {"name":"ap","txt":"Average precision: "}])

    clst=stats([{"name":"l","txt":"Cluster "},
                {"name":"npcl","txt":"Positive Examples"},
                {"name":"nncl","txt":"Negative Examples"}])

    stloss=stats([{"name":"output","txt":""},
                {"name":"negratio[-1]","txt":"Ratio Neg loss:"},
                {"name":"nexratio[-1]","txt":"Ratio Examples: "},
                {"name":"posratio[-1]","txt":"Ratio Pos loss: "},
                {"name":"rpoldloss","txt":"Old Pos Loss: "},
                {"name":"rpnewloss","txt":"New Pos Loss: "}])

    stpos=stats([{"name":"cntadded","txt":"Added"},
                {"name":"cntnochange","txt":"No Change"},
                {"name":"cntgoodchnage","txt":"Good Change"},
                {"name":"cntkeepoldscr","txt":"Keep old scr"}])


    #trPosImages=InriaPosData(basepath="/home/databases/")
    #trNegImages=InriaNegData(basepath="/home/databases/")
    #tsImages=InriaTestFullData(basepath="/home/databases/")
    #training
    if cfg.db=="VOC":
        if cfg.year=="2007":
            trPosImages=getRecord(VOC07Data(select="pos",cl="%s_trainval.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",
                            usetr=True,usedf=False),cfg.maxpos)
            trNegImages=getRecord(VOC07Data(select="neg",cl="%s_trainval.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxneg)
            trNegImagesFull=getRecord(VOC07Data(select="neg",cl="%s_trainval.txt"%cfg.cls,
                            basepath=cfg.dbpath,usetr=True,usedf=False),5000)
            #test
            tsPosImages=getRecord(VOC07Data(select="pos",cl="%s_test.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxtest)
            tsNegImages=getRecord(VOC07Data(select="neg",cl="%s_test.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxneg)
            tsImages=numpy.concatenate((tsPosImages,tsNegImages),0)
            tsImagesFull=getRecord(VOC07Data(select="all",cl="%s_test.txt"%cfg.cls,
                            basepath=cfg.dbpath,
                            usetr=True,usedf=False),5000)
        elif cfg.year=="2011":
            trPosImages=getRecord(VOC11Data(select="pos",cl="%s_train.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",
                            usetr=True,usedf=False),cfg.maxpos)
            trNegImages=getRecord(VOC11Data(select="neg",cl="%s_train.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxneg)
            trNegImagesFull=getRecord(VOC11Data(select="neg",cl="%s_train.txt"%cfg.cls,
                            basepath=cfg.dbpath,usetr=True,usedf=False),30000)
            #test
            tsPosImages=getRecord(VOC11Data(select="pos",cl="%s_val.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxtest)
            tsNegImages=getRecord(VOC11Data(select="neg",cl="%s_val.txt"%cfg.cls,
                            basepath=cfg.dbpath,#"/home/databases/",#"/share/ISE/marcopede/database/",
                            usetr=True,usedf=False),cfg.maxneg)
            tsImages=numpy.concatenate((tsPosImages,tsNegImages),0)
            tsImagesFull=getRecord(VOC11Data(select="all",cl="%s_val.txt"%cfg.cls,
                            basepath=cfg.dbpath,
                            usetr=True,usedf=False),30000)
            
    elif cfg.db=="ivan":
        trPosImages=getRecord(ImgFile("/media/OS/data/PVTRA101/CLEAR06_PVTRA101a01_502_BboxROI.txt",imgpath="/media/OS/data/PVTRA101/images/",sort=True,amin=400),cfg.maxpos)[:1000:10]
        #trPosImages=getRecord(ImgFile("/media/OS/data/PVTRA101/CLEAR06_PVTRA101a01_PDT_vis1_objid-1_pres-1_occl0_syncat-1_amb0_mob-1.txt",imgpath="/media/OS/data/PVTRA101/images/"),cfg.maxpos)##pedestrian
        #trPosImages=getRecord(ImgFile("/media/OS/data/PVTRA101/CLEAR06_PVTRA101a01_VDT_vis1_objid-1_pres-1_occl0_syncat-1_amb0_mob-1.txt",imgpath="/media/OS/data/PVTRA101/images/"),cfg.maxpos)##cars
        #trPosImages=getRecord(ImgFile("/media/OS/data/PVTRA101/CLEAR06_PVTRA101a01_PVDT_vis1_objid-1_pres-1_occl0_syncat-1_amb0_mob-1.txt",imgpath="/media/OS/data/PVTRA101/images/"),cfg.maxpos)##car+person
        #trNegImages=getRecord(InriaNegData(basepath=cfg.dbpath),cfg.maxneg)
        trNegImages=getRecord(DirImages(imagepath="/media/OS/data/PVTRA101/neg/"),cfg.maxneg)
        trNegImagesFull=trNegImages
        #test
        #tsImages=getRecord(ImgFile("/media/OS/data/PVTRA101/CLEAR06_PVTRA101a01_502_Bbox.txt",imgpath="/media/OS/data/PVTRA101/images/"),10000+cfg.maxtest)[10000:]
        #tsImages=getRecord(ImgFile("/media/OS/data/PVTRA101/GrTr_CLEAR06_PVTRA101a01.txt",imgpath="/media/OS/data/PVTRA101/images/"),10000+cfg.maxtest)[10000:]
        #tsImages=getRecord(ImgFile("/media/OS/data/PVTRA101a19/GrTr_CLEAR06_PVTRA101a19_only12.txt",imgpath="/media/OS/data/PVTRA101a19/CLEAR06_PVTRA101a19/",sort=True,amin=100),cfg.maxtest)[:(1950/12)]#the other frames
        tsImages=getRecord(ImgFile("/media/OS/data/PVTRA101a19/CLEAR06_PVTRA101a19_PV_Celik_allfr.txt",imgpath="/media/OS/data/PVTRA101a19/CLEAR06_PVTRA101a19/",sort=True,amin=100),cfg.maxtest)#pedestrian+vechicles
        tsImagesFull=tsImages
    elif cfg.db=="adondemand":
        trPosImages=getRecord(ImgFile("/home/marcopede/databases/videos/bigbang/%s.txt"%cfg.cls,imgpath="/home/marcopede/databases/videos/bigbang/images/",sort=True),cfg.maxpos)#[:1000:10]
        trNegImages=getRecord(DirImages(imagepath="/media/OS/data/PVTRA101/neg/"),cfg.maxneg)
        #trNegImages=getRecord(DirImages(imagepath="/home/marcopede/databases/videos/bigbang/images/"),10000)[1000:1000+cfg.maxneg*10:10]
        trNegImagesFull=trNegImages
        #tsImages=getRecord(ImgFile("/home/marcopede/databases/videos/bigbang/annotations.txt",imgpath="/home/marcopede/databases/videos/bigbang/images/",sort=True),cfg.maxtest)#[:1000:10]
        tsImages=[]#getRecord(DirImages(imagepath="/home/marcopede/databases/videos/bigbang/images/"))[200:]
        tsImagesFull=getRecord(DirImages(imagepath="/home/marcopede/databases/videos/bigbang/images/"))[200:200+cfg.maxtest]#tsImages
    elif cfg.db=="inria":
        trPosImages=getRecord(InriaPosData(basepath=cfg.dbpath),cfg.maxpos)
        trNegImages=getRecord(InriaNegData(basepath=cfg.dbpath),cfg.maxneg)#check if it works better like this
        trNegImagesFull=getRecord(InriaNegData(basepath=cfg.dbpath),5000)
        #test
        tsImages=getRecord(InriaTestFullData(basepath=cfg.dbpath),cfg.maxtest)
        tsImagesFull=tsImages

    #compute simple vocabulary
    from PySegment import *
    maxsift=10000
    siftsize=2
    numbin=6
    numbow=numbin**(siftsize**2)#625
    recVOC=False
    name=testname+"_book%d_%d_%s_"%(siftsize,numbow,cfg.cls)
#    fdgfd
#    try:
#	    rbook=numpy.load('%s.npz'%(name))["arr_0"]
#    except:
#        print "Computing Vocabulary"
#        recVOC=True
#    if recVOC:
#        pos=0
#        svect=numpy.zeros((2*maxsift,siftsize**2*9))
#        for l in trPosImages:
#            img=util.myimread(l["name"])
#            feat=pyrHOG2.pyrHOG(img,interv=1)
#            him=feat.hog[1]
#            feat=hogtosift(feat.hog[1][:,:,:9],siftsize)
#            himy=him.shape[0]-siftsize+1
#            himx=him.shape[1]-siftsize+1
#            svect[pos:pos+himy*himx]=feat
#            pos+=himy*himx
#            print pos
#            if pos>maxsift:
#                pos-=himy*himx
#                break
#        print "Kmaens"
#        rbook,di=vq.kmeans(svect[:pos],numbow,3)
#        numpy.savez('%s.npz'%(name), rbook) 
    #rbook=numpy.zeros((numbow,9*siftsize*siftsize))

##    r2book=numpy.concatenate((rbook,numpy.zeros((numbow,22))),1)
##    showBook(r2book,siftsize)
#    #generate samples
#    table2=-numpy.ones((10000,10),dtype=numpy.int)
#    table=-numpy.ones((10000),dtype=numpy.int)
#    tablep=-numpy.zeros((10000),dtype=numpy.int)
#    tablen=-numpy.zeros((10000),dtype=numpy.int)
#    dtable=-numpy.ones(10000)
##    for c in range(siftsize*siftsize):
##        for z in range(10):
##            desc=numpy.zeros((9,siftsize*siftsize),dtype=numpy.float32)
##            if z!=9:
##                descr[z,c]=1.0;
#    pos=0
#    maxsift=50000
#    svect=numpy.zeros((2*maxsift,siftsize**2*9))
#    for l in trPosImages:
#        img=util.myimread(l["name"])
#        feat=pyrHOG2.pyrHOG(img,interv=1)
#        him=feat.hog[1]
#        feat=hogtosift(feat.hog[1][:,:,:9],siftsize)
#        himy=him.shape[0]-siftsize+1
#        himx=him.shape[1]-siftsize+1
#        svect[pos:pos+himy*himx]=feat
#        pos+=himy*himx
#        print pos
#        if pos>maxsift:
#            pos-=himy*himx
#            break

#    svect2=numpy.zeros((2*maxsift,siftsize**2*9))
#    neg=0
#    for l in trNegImages:
#        img=util.myimread(l["name"])
#        feat=pyrHOG2.pyrHOG(img,interv=1)
#        him=feat.hog[1]
#        feat=hogtosift(feat.hog[1][:,:,:9],siftsize)
#        himy=him.shape[0]-siftsize+1
#        himx=him.shape[1]-siftsize+1
#        svect2[neg:neg+himy*himx]=feat
#        neg+=himy*himx
#        print neg
#        if neg>maxsift:
#            neg-=himy*himx
#            break
#        
#    for val in range(pos):
#        desc=svect[val].reshape((siftsize*siftsize,9))
#        aa=numpy.argmax(desc,1)
#        bb=numpy.max(desc,1)
#        pp=0
#        auxdesc=numpy.zeros((4,9))
#        for c in range(siftsize*siftsize):
#            if bb[c]<0.1:
#                aa[c]=9
#            else:
#                auxdesc[c,aa[c]]=1.0
#            pp+=aa[c]*10**c
#        tablep[pp]+=1
#        
#    for val in range(neg):
#        desc=svect2[val].reshape((siftsize*siftsize,9))
#        aa=numpy.argmax(desc,1)
#        bb=numpy.max(desc,1)
#        pp=0
#        auxdesc=numpy.zeros((4,9))
#        for c in range(siftsize*siftsize):
#            if bb[c]<0.1:
#                aa[c]=9
#            else:
#                auxdesc[c,aa[c]]=1.0
#            pp+=aa[c]*10**c
#        tablen[pp]+=1

#    dis=tablep/(tablep+tablen+0.0001)
#    print dis
#    raw_input()

#    descr2=numpy.zeros((2,31*4))
#    rbook2=numpy.zeros(rbook.shape)
#    for idel,el in enumerate(rbook):
#        desc=el.reshape((siftsize*siftsize,9))
#        descr2[0]=numpy.concatenate((desc,numpy.zeros((4,22))),1).flatten()
#        aa=numpy.argmax(desc,1)
#        bb=numpy.max(desc,1)
#        pp=0
#        auxdesc=numpy.zeros((4,9))
#        for c in range(siftsize*siftsize):
#            if bb[c]<0.1:
#                aa[c]=9
#            else:
#                auxdesc[c,aa[c]]=1.0
#            pp+=aa[c]*10**c
#        rbook2[idel]=auxdesc.flatten()
#    
#    coll=0
#    descr2=numpy.zeros((2,31*4))
#    for val in range(pos):
#        desc=svect[val].reshape((siftsize*siftsize,9))
#        descr2[0]=numpy.concatenate((desc,numpy.zeros((4,22))),1).flatten()
#        aa=numpy.argmax(desc,1)
#        bb=numpy.max(desc,1)
#        pp=0
#        auxdesc=numpy.zeros((4,9))
#        for c in range(siftsize*siftsize):
#            if bb[c]<0.1:
#                aa[c]=9
#            else:
#                auxdesc[c,aa[c]]=1.0
#            pp+=aa[c]*10**c
#        descr2[1]=numpy.concatenate((auxdesc,numpy.zeros((4,22))),1).flatten()
#        #showBook(descr2,siftsize)
#        #raw_input()
##        print pp
##        print aa,bb
##        raw_input()
##            if pp<9:
##                desc[c,pp]=0.3
#        fdesc=desc.flatten()
#        #dd=numpy.sum((fdesc-rbook)**2,1)
#        dd=numpy.sum((auxdesc.flatten()-rbook)**2,1)
#        cc=0
#        while (table2[pp,cc]!=-1 and cc<9):
#            cc+=1
#        table2[pp,cc]=numpy.argmin(dd)
#        table[pp]=numpy.argmin(dd)
#        dtable[pp]=numpy.min(dd)
##        if table[pp]==-1:
##            table[pp]=numpy.argmin(dd)
##        else:   
##            if table[pp]!=numpy.argmin(dd):
##                coll+=1    
##            table[pp]=numpy.argmin(dd)    
##        dtable[pp]=numpy.min(dd)
#        print pp,dtable[pp]    
#    print coll

##    for val in range(10000):
##        desc=numpy.zeros((siftsize*siftsize,9),dtype=numpy.float32)
##        strval="%04d"%val
##        for c in range(siftsize*siftsize):
##            pp=int(strval[c])
##            if pp<9:
##                desc[c,pp]=0.3
##        fdesc=desc.flatten()
##        dd=numpy.sum((fdesc-rbook)**2,1)
##        table[val]=numpy.argmin(dd)
##        dtable[val]=numpy.min(dd)
##        print val,dtable[val]

#    maux=-numpy.zeros(numbow)
#    maux2=-numpy.ones(numbow)
#    for c in range(numbow):
#        maux[c]=numpy.any(table==c)
#        if maux[c]==True:
#            maux2[c]=numpy.min(dtable[table==c])
#    print int(numpy.sum(maux)),"/",numbow
#    print maux2
#    raw_input()
    
    #cluster bounding boxes
    name,bb,r,a=extractInfo(trPosImages)
    trpos={"name":name,"bb":bb,"ratio":r,"area":a}
    import scipy.cluster.vq as vq
    numcl=cfg.numcl
    perc=cfg.perc#10
    minres=10
    minfy=3
    minfx=3
    #maxArea=25*(4-cfg.lev[0])
    maxArea=15*(4-cfg.lev[0])
    usekmeans=False

    #using kmeans
#    clc,di=vq.kmeans(r,numcl,3)
#    cl=vq.vq(r,clc)[0]
#    for l in range(numcl):
#        print "Cluster kmeans",l,":"
#        print "Samples:",len(a[cl==l])
#        print "Mean Area:",numpy.mean(a[cl==l])/16.0
#        sa=numpy.sort(a[cl==l])
#        print "Min Area:",numpy.mean(sa[int(len(sa)*perc)])/16.0
#        print "Aspect:",numpy.mean(r[cl==l])
#        print
    #using same number per cluster
    sr=numpy.sort(r)
    spl=[]
    lfy=[];lfx=[]
    cl=numpy.zeros(r.shape)
    for l in range(numcl):
        spl.append(sr[round(l*len(r)/float(numcl))])
    spl.append(sr[-1])
    for l in range(numcl):
        cl[numpy.bitwise_and(r>=spl[l],r<=spl[l+1])]=l
    for l in range(numcl):
        print "Cluster same number",l,":"
        print "Samples:",len(a[cl==l])
        #meanA=numpy.mean(a[cl==l])/16.0/(0.5*4**(cfg.lev[l]-1))#4.0
        meanA=numpy.mean(a[cl==l])/16.0/(4**(cfg.lev[l]-1))#4.0
        print "Mean Area:",meanA
        sa=numpy.sort(a[cl==l])
        #minA=numpy.mean(sa[len(sa)/perc])/16.0/(0.5*4**(cfg.lev[l]-1))#4.0
        minA=numpy.mean(sa[int(len(sa)*perc)])/16.0/(4**(cfg.lev[l]-1))#4.0
        print "Min Area:",minA
        aspt=numpy.mean(r[cl==l])
        print "Aspect:",aspt
        if minA>maxArea:
            minA=maxArea
        #minA=10#for bottle
        if aspt>1:
            fx=(max(minfx,numpy.sqrt(minA/aspt)))
            fy=(fx*aspt)
        else:
            fy=(max(minfy,numpy.sqrt(minA*(aspt))))
            fx=(fy/(aspt))        
        print "Fy:%.2f"%fy,"~",round(fy),"Fx:%.2f"%fx,"~",round(fx)
        lfy.append(round(fy))
        lfx.append(round(fx))
        print

    #raw_input()

    cfg.fy=lfy#[7,10]#lfy
    cfg.fx=lfx#[11,7]#lfx
    
    import time
    initime=time.time()
    #intit model

    #mypool = Pool(numcore)
    
    models=[]
    for c in range(cfg.numcl):      
        models.append(model.initmodel(cfg.fy[c],cfg.fx[c],cfg.lev[c],cfg.useRL,cfg.deform,numbow,CRF=cfg.CRF,small2=cfg.small2))
#check model
    #pyrHOG2.BOW=cfg.usebow
    #BOW=pyrHOG2.BOW
    import model
    #useCRF=True
    waux=[]
    w=numpy.array([])
    rr=[]
###just for a test
    #models=util.load("./data/CRF/12_04_27/bicycle2_CRFfull4.model")
    #cfg.k=0.3
    #from model to w
    for l in range(cfg.numcl):
        if cfg.deform:
            waux.append(model.model2wDef(models[l],cfg.k,deform=cfg.deform,usemrf=cfg.usemrf,usefather=cfg.usefather,usebow=cfg.usebow))
        else:
            waux.append(model.model2w(models[l],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2))
        rr.append(models[l]["rho"])
        w=numpy.concatenate((w,waux[-1],numpy.array([models[l]["rho"]])))
    #from w to model m1
    m1=[]
    for l in range(cfg.numcl):
        if cfg.deform:
            m1.append(model.w2modelDef(waux[l],rr[l],cfg.lev[0],31,siftsize=siftsize,bin=numbin,fy=models[l]["fy"],fx=models[l]["fx"],usemrf=cfg.usemrf,usefather=cfg.usefather,useoccl=cfg.occl,usebow=cfg.usebow))
        else:
            m1.append(model.w2model(waux[l],rr[l],cfg.lev[0],31,siftsize=siftsize,bin=numbin,fy=models[l]["fy"],fx=models[l]["fx"],k=cfg.k,usemrf=cfg.usemrf,usefather=cfg.usefather,useoccl=cfg.occl,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2))

    #from m1 to w1
    waux1=[]
    w1=numpy.array([])
    for l in range(cfg.numcl):
        if cfg.deform:
            waux1.append(model.model2wDef(m1[l],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow))
        else:
            waux1.append(model.model2w(m1[l],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2))
        w1=numpy.concatenate((w1,waux1[-1],numpy.array([m1[l]["rho"]])))
    
    assert(numpy.all(w1==w))
    #models=m1

    if 0:        
        print "Show model"
        for idm,m in enumerate(models):    
            pylab.figure(100+idm)
            pylab.clf()
            util.drawModel(m["ww"])
            pylab.draw()
            pylab.show()
        raw_input()

    #fulltrpos=[]
    #fulltrposcl=[]
    trneg=[]
    trpos=[]
    trposcl=[]
    dtrpos={}
    trnegcl=[]
    newtrneg=[]
    newtrnegcl=[]
    negratio=[-1]
    posratio=[-1]
    nexratio=[-1]
    fobj=[]
    rpnewloss=0.0
    rpoldloss=0.0
    #cumsize=None
    cumsize=numpy.zeros(numcl+1,dtype=numpy.int)
    for idl,l in enumerate(waux):
        cumsize[idl+1]=cumsize[idl]+len(l)+1
    last_round=False
    #w=None
    oldprloss=numpy.zeros((0,6))
    totPosEx=0
    for i in range(len(trPosImages)):
            totPosEx += len(trPosImages[i]["bbox"])  
    print "TOT POS EX:",totPosEx
    #raw_input()
    #if cfg.useRL:
    totPosEx*=2 #double number of bboxes because of flip

    #now chache is 10 times positive examples
    if cfg.variablecache:
        cfg.maxexamples= min(cfg.maxexamples,totPosEx*10)
        print "Real cache:",cfg.maxexamples
        #raw_input()

    pyrHOG2.setK(cfg.k)
    #pyrHOG2.setDENSE(cfg.dense)
    for it in range(cfg.posit):
        if cfg.checkpoint:
            try:
                m1=util.load("%s%d.model"%(testname,it))
                m1=util.load("%s%d.model"%(testname,it+1))
                continue
            except:
                if it==0:
                    print "Starting from scracth!!"
                else:
                    print "Using model %d for it %d because it is the last complete"%(it-1,it)
                    m1=util.load("%s%d.model"%(testname,it-1))
                    w1=numpy.array([])
                    waux1=[]
                    for l in range(cfg.numcl):
                        if cfg.deform:
                            waux1.append(model.model2wDef(m1[l],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow))
                        else:
                            waux1.append(model.model2w(m1[l],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2))
                        w1=numpy.concatenate((w1,waux1[-1],numpy.array([-m1[l]["rho"]/float(cfg.bias)])))
                    w=w1
                    models=m1
        if last_round:
            print "Finished!!!!"
            break
        #trpos=[]
        #numoldtrpos=len(trpos)
        #trpos=fulltrpos
        #trposcl=fulltrposcl
        #numoldtrposcl=len(trposcl)
        #trposcl=[]
        #just for test
        newtrneg=[]
        newtrnegcl=[]
        cntnochange=0
        cntgoodchnage=0
        cntkeepoldscr=0
        cntkeepoldbb=0
        cntnotused=0
        cntadded=0
        #clear()
        partime=time.time()
        print "Positive Images:"
        if cfg.bestovr and it==0:#force to take best overlapping
            cfg.mpos=10
            auxinitr=cfg.initr
            temprank=cfg.ranktr
            if cfg.denseinit:
                if cfg.CRF:
                    cfg.ranktr=1000
                    cfg.initr=1
                else:
                    cfg.ranktr=20000 #should be at least 1000
                    cfg.initr=0
        else:
            cfg.mpos=0#0.5
            #not necessary they are done at negative stage
            #cfg.ranktr=temprank 
            #cfg.initr=auxinitr
        cfgpos=copy.copy(cfg)
        cfgpos.numneg=cfg.numneginpos
        #arg=[[i,trPosImages[i]["name"],trPosImages[i]["bbox"],models,cfgpos] for i in range(len(trPosImages))]
        if cfg.useRL:      
            arg = []
            for i in range(len(trPosImages)):
                arg.append([i,trPosImages[i]["name"],trPosImages[i]["bbox"],models,cfgpos,False]) 
                arg.append([i,trPosImages[i]["name"],trPosImages[i]["bbox"],models,cfgpos,True])
        else:
            arg=[[i,trPosImages[i]["name"],trPosImages[i]["bbox"],models,cfgpos] for i in range(len(trPosImages))]
        t=time.time()
        #mypool = Pool(numcore)
        if not(cfg.multipr):
            itr=itertools.imap(detectWrap,arg)        
        else:
            #res=mypool.map(detectWrap,arg)
            itr=mypool.imap(detectWrap,arg)
        numbb=0
        for ii,res in enumerate(itr):
            totneg=0
            fuse=[]
            fuseneg=[]
            for mix in res:
                #trpos+=res[3]
                tr=mix[0]
                fuse+=mix[1]
                fuseneg+=mix[2]
                #ineg=tr.descr(mix[2],flip=False)
                #newtrneg+=ineg
                #totneg+=len(ineg)
                #newtrnegcl+=tr.mixture(mix[2])
                #if cfg.useflineg:
                #    inegflip=tr.descr(mix[2],flip=True)
                #    newtrneg+=inegflip
                #    newtrnegcl+=tr.mixture(mix[2])
            #for h in fuse:
            #    h["scr"]+=models[h["cl"]]["ra"]
            rfuse=tr.rank(fuse,maxnum=1000)
            rfuseneg=tr.rank(fuseneg,maxnum=1000)
            nfuse=tr.cluster(rfuse,ovr=cfg.ovrasp)
            nfuseneg=tr.cluster(rfuseneg,ovr=cfg.ovrasp)
            #imname=arg[ii][1].split("/")[-1]
            flipstr=""
            if len(arg[ii])>5:
                if arg[ii][5]:
                    flipstr="_filp"
            imname=arg[ii][1].split("/")[-1]+flipstr
            ineg=tr.descr(nfuseneg,flip=False,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)
            newtrneg+=ineg
            if not(cfg.useRL):
                inegflip=tr.descr(nfuseneg,flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)
                newtrneg+=inegflip
                newtrnegcl+=tr.mixture(nfuseneg)     
            newtrnegcl+=tr.mixture(nfuseneg)     
            if it==0:
                poscl=tr.mixture(nfuse)
                if nfuse!=[]:
                    print "Added %d examples!"%(len(nfuse))
                    dtrpos[imname]=nfuse#[:]
                    cntadded+=len(nfuse)
                else:
                    print "Example not used!"
                    
            #datamining positives
            else:
                nb=len(nfuse)
                #dns=buildense(ipos,poscl,cumsize)
                for idel,dt in enumerate(nfuse):
                    #print "BBox:",numbb
                    if dt!=[] and not(dt.has_key("notfound")): #if got a detection for the bbox
                        #if not(dtrpos.has_key(dt["img"])): 
                        if not(dtrpos.has_key(imname)): 
                            print "Added example previuosly empty!"
                            dtrpos[imname]=[dt]#copy.deepcopy(dt)]
                            cntadded+=1
                        else:
                            exmatch=False
                            print "DET BB ID:",dt["bbid"]
                            for idold,dtold in enumerate(dtrpos[imname]):
                                if dt["bbid"]==dtold["bbid"]:
                                    print "OLD BB ID:",dtold["bbid"]
                                    exmatch=True
                                    aux=tr.descr([dtold],flip=False,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                                    auxcl=tr.mixture([dtold])[0]
                                    dns=buildense([aux],[auxcl],cumsize,cfg.bias)
                                    oldscr=numpy.sum(dns*w)#-r
                                    dtaux=tr.descr([dt],flip=False,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                                    dtauxcl=tr.mixture([dt])[0]
                                    dtdns=buildense([dtaux],[dtauxcl],cumsize,cfg.bias)
                                    newscr=numpy.sum(dtdns*w)#-r
                                    if abs(newscr-dt["scr"])>approx:
                                        print "Warning dense score and scan score are different!!!!"
                                        raw_input() 
                                    print "New:",dt["scr"],"Old",oldscr
                                    if abs(dt["scr"]-oldscr)<approx:
                                        print "No change between old and new labeling! (%f)"%(dt["scr"])
                                        cntnochange+=1
                                        dtrpos[imname][idold]["scr"]=oldscr
                                    elif dt["scr"]-oldscr>approx:
                                        print "New score (%f) higher than previous (%f)!"%(dt["scr"],oldscr)
                                        cntgoodchnage+=1
                                        #dtold=dt
                                        dtrpos[imname][idold]=dt#copy.deepcopy(dt)
                                        #dtrpos[imname][idold]["dns"]=dtdns
                                    else:
                                        print "Keep old example (%f) because better score than new (%f)!"%(oldscr,dt["scr"])                      
                                        cntkeepoldscr+=1     
                                        dtrpos[imname][idold]["scr"]=oldscr
                                    
                            if not(exmatch):    
                                print "Added example!!!!"
                                cntadded=0
                                dtrpos[imname].append(dt)#copy.deepcopy(dt))
                    else: #or skip and keep the old
                        if dtrpos.has_key(imname):
                            for ll in dtrpos[imanme]:
                                if ll["bbid"]==dt["bbid"]:
                                    print "***Keep old example because better overlapping!"
                                    cntkeepoldbb+=1
                            else:
                                print "***Example not used!"
                                cntnotused+=1
                        else:       
                            print "****Example not used!"
                            cntnotused+=1
                numbb+=len(nfuse)*2
                #raw_input()    
            print "----Pos Image %d(%s)----"%(ii,imname)
            print "Pos:",len(nfuse),"Neg:",len(nfuseneg)
            print "Tot Pos:",len(dtrpos)," Neg:",len(trneg)+len(newtrneg)
            #check score
            if (nfuse!=[] and not(nfuse[0].has_key("notfound")) and it>=0):
                #if cfg.deform:
                aux=tr.descr(nfuse,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                #else:
                #    aux=tr.descr(nfuse)[0]
                auxcl=tr.mixture(nfuse)[0]
                dns=buildense([aux],[auxcl],cumsize,cfg.bias)[0]
                dscr=numpy.sum(dns*w)
                print "Approx:",abs(nfuse[0]["scr"]-dscr)
                #print "Scr:",nfuse[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuse[0]["scr"]-dscr)
                if abs(nfuse[0]["scr"]-dscr)>approx:
                    print "Warning: the two scores must be the same!!!"
                    print "Scr:",nfuse[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuse[0]["scr"]-dscr)
#                    import ctypes
#                    #bowsize=numbin**(siftsize**2)
#                    descr=numpy.sum(dns[-1-numbow*3+cumsize[auxcl+1]:-1+cumsize[auxcl+1]]*w[-1-numbow*3+cumsize[auxcl+1]:-1+cumsize[auxcl+1]])
#                    hogd=numpy.sum(dns[cumsize[auxcl]:cumsize[auxcl+1]-numbow*3-1]*w[cumsize[auxcl]:cumsize[auxcl+1]-numbow*3-1])
#                    bbias=numpy.sum(100*w[cumsize[auxcl+1]-1])
#                    descr2=numpy.sum(aux[-numbow*3:]*numpy.concatenate(models[auxcl]["hist"]))
#                    shy=nfuse[0]["feat"][0].shape[0] 
#                    shx=nfuse[0]["feat"][0].shape[1] 
##                    if nfuse[0]["rl"]==1:
##                        mm=[]
##                        for l in models:
##                            mm.append(pyrHOG2RL.flip(l))
##                    else:
#                    mm=models
#                    aa=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][0]).astype(numpy.float32),shy,shx,mm[auxcl]["ww"][0],shy,shx,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,pyrHOG2.hog2bow(nfuse[0]["feat"][0],code=True),shx-1,mm[auxcl]["hist"][0])
#                    bb=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][1]).astype(numpy.float32),shy*2,shx*2,mm[auxcl]["ww"][1],shy*2,shx*2,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,pyrHOG2.hog2bow(nfuse[0]["feat"][1],code=True),shx*2-1,mm[auxcl]["hist"][1])
#                    cc=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][2]).astype(numpy.float32),shy*4,shx*4,mm[auxcl]["ww"][2],shy*4,shx*4,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,pyrHOG2.hog2bow(nfuse[0]["feat"][2],code=True),shx*4-1,mm[auxcl]["hist"][2])
##                    else:
##                        aa=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][0]).astype(numpy.float32),shy,shx,models[auxcl]["ww"][0],shy,shx,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,625,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][0][pyrHOG2.histflip()])
##                        bb=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][1]).astype(numpy.float32),shy*2,shx*2,models[auxcl]["ww"][1],shy*2,shx*2,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,625,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][1][pyrHOG2.histflip()])
##                        cc=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuse[0]["feat"][2]).astype(numpy.float32),shy*4,shx*4,models[auxcl]["ww"][2],shy*4,shx*4,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,625,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][2][pyrHOG2.histflip()])
#                    print "BOW dense:",aa+bb+cc,"descr",descr,"descr2",descr2
#                    print "HOG dense",hogd
#                    print "Scr:",nfuse[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuse[0]["scr"]-dscr)
                    raw_input()
            #raw_input()
            #check score
            if (nfuseneg!=[] and it>=0):
                if cfg.deform:
                    aux=tr.descr(nfuseneg,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                else:
                    aux=tr.descr(nfuseneg,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                auxcl=tr.mixture(nfuseneg)[0]
                dns=buildense([aux],[auxcl],cumsize,cfg.bias)[0]
                dscr=numpy.sum(dns*w)
                #print "Scr:",nfuseneg[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuseneg[0]["scr"]-dscr)
                if abs(nfuseneg[0]["scr"]-dscr)>approx:
                    print "Warning: the two scores must be the same!!!"
                    print "Scr:",nfuseneg[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuseneg[0]["scr"]-dscr)
                    raw_input()
            if cfg.show and 0:
                pylab.figure(20)
                pylab.ioff()
                pylab.clf()
                pylab.axis("off")
                #pylab.axis("image")
                #img=util.myimread(trPosImages[ii/2]["name"],flip=ii%2)
                img=util.myimread(arg[ii][1],flip=ii%2)
                pylab.imshow(img,interpolation="nearest",animated=True)
                tr.show(nfuse,parts=cfg.show)      
                pylab.show()
                raw_input()
        del itr
    
        #fulltrpos=trpos
        #fulltrposcl=trposcl
        #trpos=remove_empty(fulltrpos)
        #trposcl=remove_empty(fulltrposcl)
        numoldtrpos=len(trpos)
        if it>0:
            moldloss,oldscr=loss_pos(trpos,trposcl,cumsize,w)
        else:
            moldloss=1
        oldtrpos=trpos;oldtrposcl=trposcl
        trpos,trposcl=extract_feat(tr,dtrpos,cumsize,cfg.useRL)
        if it>0:
            mnewloss,newscr=loss_pos(trpos,trposcl,cumsize,w)
        else:
            mnewloss=0
        if it>0:
            oldscr=numpy.array(oldscr)
            newscr=numpy.array(newscr)
            if len(oldscr)==len(newscr):
                if numpy.any(newscr-oldscr)<0:
                    print "Error, score is decreasing"
                    print newscr-oldscr

        print "Added",cntadded
        print "No change",cntnochange
        print "Good change",cntgoodchnage
        print"Keep old small scr",cntkeepoldscr
        print "Keep old bbox",cntkeepoldbb
        print "Not used",cntnotused
        print "Total:",cntnochange+cntgoodchnage+cntkeepoldscr+cntkeepoldbb+cntnotused+cntadded
        stpos.report(cfg.testname+".rpt.txt","a","Positive Datamaining")
        #raw_input()

        #if it==0 and cfg.kmeans:#clustering for LR
        if it==0 and cfg.kmeans:#clustering for LR
            trpos=[];trposcl=[]
            trpos2,trposcl2=extract_feat2(tr,dtrpos,cumsize,False)
            for l in range(numcl):
                mytrpos=[]            
                for c in range(len(trpos2)):
                    if trposcl2[c]==l:
                        mytrpos.append(trpos2[c])
                mytrpos=numpy.array(mytrpos)
                cl1=range(0,len(mytrpos),2)
                cl2=range(1,len(mytrpos),2)
                #rrnum=len(mytrpos)
                rrnum=min(len(mytrpos),1000)#to avoid too long clustering
                #rrnum=3*len(mytrpos)
                #if cfg.cls=="person": #speed-up the clustering for person because too many examples
                #    rrnum=len(mytrpos)
                for rr in range(rrnum):
                #for rr in range(1000):
                    print "Clustering iteration ",rr
                    oldvar=numpy.sum(numpy.var(mytrpos[cl1],0))+numpy.sum(numpy.var(mytrpos[cl2],0))
                    #print "Variance",oldvar
                    #print "Var1",numpy.sum(numpy.var(mytrpos[cl1],0))
                    #print "Var2",numpy.sum(numpy.var(mytrpos[cl2],0))
                    #c1=numpy.mean(mytrpos[cl1])
                    #c2=numpy.mean(mytrpos[cl1])
                    rel=numpy.random.randint(len(cl1))
                    tmp=cl1[rel]
                    cl1[rel]=cl2[rel]
                    cl2[rel]=tmp
                    newvar=numpy.sum(numpy.var(mytrpos[cl1],0))+numpy.sum(numpy.var(mytrpos[cl2],0))
                    if newvar>oldvar:#go back
                        tmp=cl1[rel]
                        cl1[rel]=cl2[rel]
                        cl2[rel]=tmp
                    else:
                        print "Variance",newvar
                print "Elements Cluster ",l,": ",len(cl1)
                trpos+=(mytrpos[cl1]).tolist()
                trposcl+=([l]*len(cl1))
                    
        if len(trneg)>0:#it>0
            
            #lambd=1.0/(len(trpos)*cfg.svmc)
            #trpos,trneg,trposcl,trnegcl,clsize,w,lamda
            posl,negl,reg,nobj,hpos,hneg=pegasos.objective(trpos,trneg,trposcl,trnegcl,clsize,w,cfg.svmc)
            #oldloss=prloss[-1][0]*numoldtrpos+(totPosEx-numoldtrpos)*(1-cfg.thr)
            #newloss=posl*len(trpos)+(totPosEx-len(trpos))*(1-cfg.thr)
            oldloss=moldloss+(totPosEx-numoldtrpos)*(1-cfg.thr)
            newloss=mnewloss+(totPosEx-len(trpos))*(1-cfg.thr)
            print "IT:",it,"OLDPOSLOSS",oldloss,"NEWPOSLOSS:",newloss
            print "NO BOUND: OLDPOSLOSS",moldloss,"NEWPOSLOSS",mnewloss
            print "TOT EX POS:",totPosEx
            posratio.append((oldloss-newloss)/oldloss)
            nexratio.append(float(abs(len(trpos)-numoldtrpos))/numoldtrpos)
            print "RATIO: abs(oldpos-newpos)/oldpos:",posratio
            print "N old examples:",numoldtrpos,"N new examples",len(trpos),"ratio",nexratio
            #raw_input()
            #fobj.append(nobj)
            #print "OBj:",fobj
            #raw_input()
            output="Not converging yet!"
            if newloss>oldloss:
                output+="Warning increasing positive loss\n"
                print output
                raw_input()
            #if (posratio[-1]<0.0001) and nexratio[-1]<0.01:
            if (posratio[-1]<cfg.convPos) and nexratio[-1]<0.01:
                output="Very small positive improvement: convergence at iteration %d!"%it
                output+="Last iteration with all negatives!!!"
                print output
                #now it really checks for convergency pos loss
                last_round=True 
            rpnewloss=newloss  
            rpoldloss=oldloss             
            stloss.report(cfg.testname+".rpt.txt","a","Positive Convergency")
            #if (posratio[-1]<0.0001) and nexratio[-1]<0.01:
                #continue

        if it==cfg.posit-1:#last iteration
            last_round=True #use all examples
        #delete doubles
        newtrneg2,newtrnegcl2=myunique(trneg,newtrneg,trnegcl,newtrnegcl,cfg.numcl)
        trneg=trneg+newtrneg2
        trnegcl=trnegcl+newtrnegcl2

        if it==0:
            #reset initr to the configuration
            cfg.initr=auxinitr     
            cfg.ranktr=temprank

        #negative retraining
        trneglen=1
        newPositives=True
        if last_round:
            trNegImages=trNegImagesFull
            #cfg.maxneg=5000
        for nit in range(cfg.negit):
            if nit==0 and len(trneg)>0:#it>0:
                print "Skipping searching more negatives in the first iteration"
            else:
                newtrneg=[]
                newtrnegcl=[]
                print "Negative Images Iteration %d:"%nit
                #print numpy.who()
                #raw_input()
                limit=False
                cfgneg=copy.copy(cfg)
                cfgneg.numneg=10#cfg.numneginpos
                cfgneg.thr=-1
                nparts=10
                if cfg.maxneg<40:#nparts*cfg.multipr:
                    nparts=4
                #nparts=cfg.maxneg/16
                t=time.time()
                order=range(nparts)#numpy.random.permutation(range(nparts))
                for rr in order:
                    arg=[[i,trNegImages[i]["name"],trNegImages[i]["bbox"],models,cfgneg] for i in range(rr*len(trNegImages)/nparts,(rr+1)*len(trNegImages)/nparts)]
                    print "PART:%d Elements:%d"%(rr,len(arg))
                    #arg=[[i,trNegImages[i]["name"],trNegImages[i]["bbox"],models,cfgneg] for i in range((it+1)*len(trNegImages)/(10))]
                    t=time.time()
                    if not(cfg.multipr):
                        itr=itertools.imap(detectWrap,arg)        
                    else:
                        itr=mypool.imap(detectWrap,arg)
                    for ii,res in enumerate(itr):
                        totneg=0
                        fuse=[]
                        fuseneg=[]
                        for mix in res:
                            #trpos+=res[3]
                            tr=mix[0]
                            fuse+=mix[1]
                            fuseneg+=mix[2]
                            #ineg=tr.descr(mix[2],flip=False)
                            #newtrneg+=ineg
                            #totneg+=len(ineg)
                            #newtrnegcl+=tr.mixture(mix[2])
                            #if cfg.useflineg:
                            #    inegflip=tr.descr(mix[2],flip=True)
                            #    newtrneg+=inegflip
                            #    newtrnegcl+=tr.mixture(mix[2])
                        rfuse=tr.rank(fuse,maxnum=1000)
                        rfuseneg=tr.rank(fuseneg,maxnum=1000)
                        nfuse=tr.cluster(rfuse,ovr=cfg.ovrasp)
                        nfuseneg=tr.cluster(rfuseneg,ovr=cfg.ovrasp)
                        #if cfg.deform:
                        #trpos+=tr.descr(nfuse,usemrf=cfg.usemrf,usefather=cfg.usefather)         
                        newtrneg+=tr.descr(nfuseneg,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)
                        #else:
                        #trpos+=tr.descr(nfuse)         
                        #    newtrneg+=tr.descr(nfuseneg)
                        #trposcl+=tr.mixture(nfuse)
                        newtrnegcl+=tr.mixture(nfuseneg)
                        #if cfg.useflipos:
                        #    if cfg.deform:
                        #        iposflip=tr.descr(nfuse,flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather)
                        #    else:
                        #        iposflip=tr.descr(nfuse,flip=True)
                        #    trpos+=iposflip
                        #    trposcl+=tr.mixture(nfuse)
                        if cfg.useflineg and not(cfg.useRL):
                            if cfg.deform:
                                inegflip=tr.descr(nfuseneg,flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)
                            else:
                                inegflip=tr.descr(nfuseneg,flip=True,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)
                            newtrneg+=inegflip
                            newtrnegcl+=tr.mixture(nfuseneg)
                        #check score
                        if (nfuseneg!=[] and nit>=0):
                            if cfg.deform:
                                aux=tr.descr(nfuseneg,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                            else:
                                aux=tr.descr(nfuseneg,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow)[0]
                            auxcl=tr.mixture(nfuseneg)[0]
                            dns=buildense([aux],[auxcl],cumsize,cfg.bias)[0]
                            dscr=numpy.sum(dns*w)
                            if abs(nfuseneg[0]["scr"]-dscr)>approx:
                                print "Warning: the two scores must be the same!!!"
                                print "Scr:",nfuseneg[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuseneg[0]["scr"]-dscr)
#                                import ctypes
#                                descr=numpy.sum(dns[-1-numbow*3+cumsize[auxcl+1]:-1+cumsize[auxcl+1]]*w[-1-numbow*3+cumsize[auxcl+1]:-1+cumsize[auxcl+1]])
#                                hogd=numpy.sum(dns[cumsize[auxcl]:cumsize[auxcl+1]-numbow*3-1]*w[cumsize[auxcl]:cumsize[auxcl+1]-numbow*3-1])
#                                bbias=numpy.sum(100*w[cumsize[auxcl+1]-1])
#                                descr2=numpy.sum(aux[-numbow*3:]*numpy.concatenate(models[auxcl]["hist"]))
#                                shy=nfuseneg[0]["feat"][0].shape[0] 
#                                shx=nfuseneg[0]["feat"][0].shape[1] 
#                                aa=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuseneg[0]["feat"][0]).astype(numpy.float32),shy,shx,models[auxcl]["ww"][0],shy,shx,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][0])
#                                bb=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuseneg[0]["feat"][1]).astype(numpy.float32),shy*2,shx*2,models[auxcl]["ww"][1],shy*2,shx*2,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][1])
#                                cc=pyrHOG2.ff.corr3dpadbow(pyrHOG2.hogflip(nfuseneg[0]["feat"][2]).astype(numpy.float32),shy*4,shx*4,models[auxcl]["ww"][2],shy*4,shx*4,31,0,0,ctypes.POINTER(ctypes.c_float)(),0,0,0,2,numbow,numpy.ones(10,dtype=numpy.float32)*10,models[auxcl]["hist"][2])

#                                print "BOW dense:",aa+bb+cc,"descr",descr,"descr2",descr2
#                                print "HOG dense",hogd
#                                print "Scr:",nfuseneg[0]["scr"],"DesneSCR:",dscr,"Diff:",abs(nfuseneg[0]["scr"]-dscr)
                                raw_input()

                        print "----Neg Image %d----"%ii
                        print "Pos:",0,"Neg:",len(nfuseneg)
                        print "Tot Pos:",len(trpos)," Neg:",len(trneg)+len(newtrneg)
                    if len(newtrneg)+len(trneg)+len(trpos)>cfg.maxexamples:
                        print "Cache Limit Reached!"
                        limit=True
                        break
                del itr
            ##print len(trneg),trneglen
            ##if len(trneg)/float(trneglen)<1.2 and not(limit):
            ##    print "Not enough negatives, convergence!"
            ##    break

            #delete doubles
            newtrneg2,newtrnegcl2=myunique(trneg,newtrneg,trnegcl,newtrnegcl,cfg.numcl)
            trneg=trneg+newtrneg2
            trnegcl=trnegcl+newtrnegcl2

            #if len(trneg)/float(trneglen)<1.05 and not(limit):
            if len(newtrneg2)==0 and not(newPositives) and not(limit):
                print "Not enough negatives, convergence!"
                break
            newPositives=False

            print "Building Feature Vector"
            clsize=numpy.zeros(numcl,dtype=numpy.int)#get clusters sizes
            #cumsize=numpy.zeros(numcl+1,dtype=numpy.int)
            for l in range(numcl):
                npcl=(l,numpy.sum(numpy.array(trposcl)==l))
                nncl=(l,numpy.sum(numpy.array(trnegcl)==l))
                print "Pos Samples Cluster %d: %d"%npcl
                print "Neg Samples Cluster %d: %d"%nncl
                clst.report(testname+".rpt.txt","a","Cluster Statistics:")
                c=0
                while trnegcl[c]!=l:
				    c+=1
                clsize[l]=len(trneg[c])+1
                #cumsize[l+1]=numpy.sum(clsize[:l+1])

            #show pos examples
            if 0:
                pylab.figure(23)
                pylab.clf()
                util.showExamples(ftrpos,fy,fx)
                pylab.draw()
                pylab.show()
                #raw_input()

            #check negative loss
            if nit>0 and not(limit):
                #lambd=1.0/(len(trpos)*cfg.svmc)
                #trpos,trneg,trposcl,trnegcl,clsize,w,lamda
                posl,negl,reg,nobj,hpos,hneg=pegasos.objective(trpos,trneg,trposcl,trnegcl,clsize,w,cfg.svmc)
                print "NIT:",nit,"OLDLOSS",old_nobj,"NEWLOSS:",nobj
                negratio.append(nobj/(old_nobj+0.000001))
                print "RATIO: newobj/oldobj:",negratio
                output="Negative not converging yet!"
                #if (negratio[-1]<1.05):
                if (negratio[-1]<cfg.convNeg):
                    output= "Very small negative newloss: convergence at iteration %d!"%nit
                    #raw_input()
                    #break
                stloss.report(cfg.testname+".rpt.txt","a","Negative Convergency")
                if (negratio[-1]<cfg.convNeg):
                    break
            #else:
            #    negl=1

            print "SVM learning"
            svmname="%s.svm"%testname
            #lib="libsvm"
            lib="linear"
            #lib="linearblock"
            #pc=0.008 #single resolution
            #pc=cfg.svmc #high res
            #util.trainSvmRaw(ftrpos,ftrneg,svmname,dir="",pc=pc,lib=lib)
            #util.trainSvmRaw(ftrneg,ftrpos,svmname,dir="",pc=pc,lib=lib)
            #w,r=util.loadSvm(svmname,dir="",lib=lib)
            #w,r=util.trainSvmRawPeg(ftrpos,ftrneg,testname+".rpt.txt",dir="",pc=pc)

            import pegasos
            if w==None: 
                #w=numpy.zeros(cumsize[-1])
                w=numpy.random.rand(cumsize[-1])
                w=w/numpy.sqrt(numpy.sum(w**2))

            noise=False
            if noise:
                noiselev=0.5*(1-float(it)/(cfg.posit-1))+cfg.noiselev*(float(it)/(cfg.posit-1))
                atrpos=numpy.array(trpos,dtype=object)
                atrposcl=numpy.array(trposcl,dtype=object)
                oldoutlyers=numpy.zeros(len(trpos),dtype=numpy.int)
                newoutlyers=numpy.zeros(len(trpos),dtype=numpy.int)
                for ii in range(10):
                    lscr=[]
                    dns=buildense(trpos,trposcl,cumsize,cfg.bias)
                    for f in dns:
                        lscr.append(numpy.sum(f*w))
                    ordered=numpy.argsort(lscr)             
                    ntrpos=atrpos[ordered][len(trpos)*noiselev:len(trpos)]
                    ntrposcl=atrposcl[ordered][len(trposcl)*noiselev:len(trposcl)]
                    #w,r,prloss=pegasos.trainComp(ntrpos,trneg,testname+"loss.rpt.txt",ntrposcl,trnegcl,oldw=w,dir="",pc=cfg.svmc,k=10,numthr=numcore)
                    w,r,prloss=trainParallel(trpos,trneg,testname,trposcl,trnegcl,w,cfg.svmc,cfg.multipr,parallel=True,numcore=numcore)
                    newoutlyers[ordered[:len(trpos)*noiselev]]=1
                    numout=numpy.sum(numpy.bitwise_and(newoutlyers,oldoutlyers))
                    print ordered
                    print ordered[:len(trpos)*noiselev]#ntrpos[:len(trpos)*noiselev]
                    print numout
                    if numout>=int(len(trpos)*noiselev*0.95):
                        print 'Converging because ',numout,'/',int(len(trpos)*noiselev*0.95) 
                        break
                    else:
                        print 'Not congergin yet because',numout,'/',int(len(trpos)*noiselev*0.95) 
                    oldoutlyers=newoutlyers.copy()
                    #raw_input()
            else:
                #w,r,prloss=trainParallel(trpos,trneg,testname,trposcl,trnegcl,w,cfg.svmc,cfg.multipr,parallel=True,numcore=numcore)
                #mypool.close() you can close the workers to get more memory...
                myk=4*numcore
                if numcore==False:
                    myk=1
                w,r,prloss=pegasos.trainComp(trpos,trneg,testname+"loss.rpt.txt",trposcl,trnegcl,oldw=w,dir="",pc=cfg.svmc,k=myk,numthr=numcore,eps=0.01)

            old_posl,old_negl,old_reg,old_nobj,old_hpos,old_hneg=pegasos.objective(trpos,trneg,trposcl,trnegcl,clsize,w,cfg.svmc)            
            #pylab.figure(300)
            #pylab.clf()
            #pylab.plot(w)
            pylab.figure(500)
            pylab.clf()
            oldprloss=numpy.concatenate((oldprloss,prloss),0)
            pylab.plot(oldprloss)
            pylab.semilogy()
            pylab.legend(["loss+","loss-","reg","obj","hard+","hard-"],loc='upper left')
            pylab.savefig("%s_loss%d.pdf"%(cfg.testname,it))
            pylab.draw()
            pylab.show()

            #bias=100
            waux=[];rr=[];w1=numpy.array([])
            for idm,m in enumerate(models):
                #models[idm]=tr.model(w[cumsize[idm]:cumsize[idm+1]-1],-w[cumsize[idm+1]-1]*bias,len(m["ww"]),31,m["fy"],m["fx"],usemrf=cfg.usemrf,usefather=cfg.usefather,usebow=cfg.usebow)
                #from w to model
                if cfg.deform:
                    models[idm]=model.w2modelDef(w[cumsize[idm]:cumsize[idm+1]-1],-w[cumsize[idm+1]-1]*cfg.bias,len(m["ww"]),31,m["fy"],m["fx"],bin=numbin,siftsize=siftsize,usemrf=cfg.usemrf,usefather=cfg.usefather,usebow=cfg.usebow)
                else:
                    models[idm]=model.w2model(w[cumsize[idm]:cumsize[idm+1]-1],-w[cumsize[idm+1]-1]*cfg.bias,len(m["ww"]),31,m["fy"],m["fx"],bin=numbin,siftsize=siftsize,usemrf=cfg.usemrf,usefather=cfg.usefather,k=cfg.k,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2)
                #models[idm]["ra"]=w[cumsize[idm+1]-1]
                #from model to w #changing the clip...
                if cfg.deform:
                    waux.append(model.model2wDef(models[idm],cfg.k,deform=cfg.deform,usemrf=cfg.usemrf,usefather=cfg.usefather,usebow=cfg.usebow))
                else:
                    waux.append(model.model2w(models[idm],cfg.deform,cfg.usemrf,cfg.usefather,cfg.k,usebow=cfg.usebow,useCRF=cfg.CRF,small2=cfg.small2))
                rr.append(models[idm]["rho"])
                w1=numpy.concatenate((w1,waux[-1],-numpy.array([models[idm]["rho"]])/cfg.bias))
            w2=w
            w=w1
            util.save("%s%d.model"%(testname,it),models)
            if cfg.deform:
                print m["df"]

            if True:
                print "Show model"
                for idm,m in enumerate(models):    
                    pylab.figure(100+idm)
                    pylab.clf()
                    util.drawModel(m["ww"])
                    pylab.title("Bias:%f"%(m["rho"]))
                    pylab.draw()
                    pylab.show()
                    pylab.savefig("%s_hog%d_cl%d.png"%(testname,it,idm))
                    if cfg.CRF:
                        pylab.figure(120+idm)
                        pylab.clf()
                        pylab.subplot(2,2,1)
                        pylab.imshow(m["cost"][0][:-1],interpolation="nearest")
                        pylab.xlabel("Vertical Edge Y")
                        pylab.subplot(2,2,2)
                        pylab.imshow(m["cost"][1][:-1],interpolation="nearest")
                        pylab.xlabel("Vertical Edge X")
                        pylab.subplot(2,2,3)
                        pylab.imshow(m["cost"][2][:,:-1],interpolation="nearest")
                        pylab.xlabel("Horizontal Edge Y")
                        pylab.subplot(2,2,4)
                        pylab.imshow(m["cost"][3][:,:-1],interpolation="nearest")
                        pylab.xlabel("Horizontal Edge X")
                        pylab.draw()
                        pylab.show()
                        pylab.savefig("%s_def%d_cl%d.png"%(testname,it,idm))
                    
                    if cfg.deform:
                        pylab.figure(110+idm)
                        pylab.clf()
                        util.drawDeform(m["df"])
                        pylab.draw()
                        pylab.show()
                        pylab.savefig("%s_def%d_cl%d.png"%(testname,it,idm))

            sts.report(testname+".rpt.txt","a","Before Filtering")
            #sort based on score
            #sort=True
            if cfg.sortneg:
                order=[]
                for p,d in enumerate(trneg):
                    order.append(numpy.dot(buildense([d],[trnegcl[p]],cumsize,cfg.bias)[0],w))
                order=numpy.array(order)
                sorder=numpy.argsort(order)
                strneg=[]
                strnegcl=[]
                for p in sorder:
                    strneg.append(trneg[p])
                    strnegcl.append(trnegcl[p])
                trneg=strneg
                trnegcl=strnegcl
            #else:
            #    sorder=range(len(trneg))

            print "Filter Data"
            print "Length before:",len(trneg)
            for p,d in enumerate(trneg):
            #for p in sorder:
                aux=buildense([trneg[p]],[trnegcl[p]],cumsize,cfg.bias)[0]
                if numpy.sum(aux*w)<-1:
                    if len(trneg)+len(trpos)>(cfg.maxexamples)/2:
                        trneg.pop(p)
                        trnegcl.pop(p)
            print "Length after:",len(trneg)
            trneglen=len(trneg)
            sts.report(testname+".rpt.txt","a","After Filtering")
     
        print "Test"
        if last_round:
            tsImages=tsImagesFull
        detlist=[]
        mycfg=copy.copy(cfg)
        mycfg.numneg=0
        arg=[[i,tsImages[i]["name"],None,models,mycfg] for i in range(len(tsImages))]
        t=time.time()
        if not(cfg.multipr):
            itr=itertools.imap(detectWrap,arg)        
        else:
            itr=mypool.imap(detectWrap,arg)
        for ii,res in enumerate(itr):
            totneg=0
            fuse=[]
            for mix in res:
                tr=mix[0]
                fuse+=mix[1]
            #for h in fuse:
            #    h["scr"]+=models[h["cl"]]["ra"]
            rfuse=tr.rank(fuse,maxnum=300)
            nfuse=tr.cluster(rfuse,ovr=cfg.ovrasp)
            print "----Test Image %d----"%ii
            for l in nfuse:
                detlist.append([tsImages[ii]["name"].split("/")[-1].split(".")[0],l["scr"],l["bbox"][1],l["bbox"][0],l["bbox"][3],l["bbox"][2]])
            print "Detections:",len(nfuse)
            if cfg.show:
                if cfg.show==True:
                    showlabel="Parts"
                else:
                    showlabel=False
                pylab.figure(20)
                pylab.ioff()
                pylab.clf()
                pylab.axis("off")
                img=util.myimread(tsImages[ii]["name"])
                pylab.imshow(img,interpolation="nearest",animated=True)
                pylab.gca().set_ylim(0,img.shape[0])
                pylab.gca().set_xlim(0,img.shape[1])
                pylab.gca().set_ylim(pylab.gca().get_ylim()[::-1])
                tr.show(nfuse,parts=showlabel,thr=-0.97,maxnum=10)           
                pylab.show()
        del itr
        
        #tp,fp,scr,tot=VOCpr.VOCprlistfastscore(tsImages,detlist,numim=cfg.maxpostest,show=False,ovr=0.5)
        tp,fp,scr,tot=VOCpr.VOCprRecord(tsImages,detlist,show=False,ovr=0.5)
        pylab.figure(15)
        pylab.clf()
        rc,pr,ap=VOCpr.drawPrfast(tp,fp,tot)
        pylab.draw()
        pylab.show()
        if last_round:
            pylab.savefig("%s_finalap%d.png"%(testname,it))        
        else:
            pylab.savefig("%s_ap%d.png"%(testname,it))
        #util.savemat("%s_ap%d.mat"%(testname,it),{"tp":tp,"fp":fp,"scr":scr,"tot":tot,"rc":rc,"pr":pr,"ap":ap})
        tinit=((time.time()-initime)/3600.0)
        tpar=((time.time()-partime)/3600.0)
        print "AP(it=",it,")=",ap
        print "Training Time: %.3f h"%(tinit)
        rpres.report(testname+".rpt.txt","a","Results")



