#scan an image with the standard method and with our CtF way

import util2
import pyrHOG2
import time

def showImage(img,title=""):
    import pylab
    pylab.figure()
    pylab.ioff()
    pylab.clf()
    pylab.axis("off")
    pylab.title(title)
    pylab.imshow(img,interpolation="nearest",animated=True) 

modelname="./data/INRIA/inria_bothfull";it=7
import sys
if len(sys.argv)>1:
    imname=sys.argv[1]
else:
    imname="test1.png"

#load the model
m=util2.load("%s%d.model"%(modelname,it))

import pylab

#show the model
if True:
    print "Show model"
    pylab.figure(100)
    pylab.clf()
    util2.drawModel(m["ww"])
    pylab.draw()

print "---- Image %s----"%imname
print
img=util2.myimread(imname)
#compute the HOG pyramid
f=pyrHOG2.pyrHOG(img,interv=10,savedir="",notload=True,notsave=True,hallucinate=True,cformat=True)
print
print "Complete search"
showImage(img,title="Complete search")
res=pyrHOG2.detect(f,m,bottomup=True,deform=True,usemrf=True,small=False,show=True)
pylab.axis((0,img.shape[1],img.shape[0],0))
dettime1=res[2]
numhog1=res[3]
print "Number of computed HOGs:",numhog1
print
print "Coarse-to-Fine search"
import pylab
showImage(img,title="Coarse-to-Fine")
res=pyrHOG2.detect(f,m,bottomup=False,deform=True,usemrf=True,small=False,show=True)
pylab.axis((0,img.shape[1],img.shape[0],0))
pylab.draw()
pylab.show()
dettime2=res[2]
numhog2=res[3]
print "Number of computed HOGs:",numhog2
print 
print "Time Speed-up: %.3f "%(dettime1/dettime2)
print "HOG Speed-up: %.3f "%(numhog1/float(numhog2))




