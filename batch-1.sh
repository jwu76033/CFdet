#!/bin/bash 

apply() 
{ 
    for ARG in "$@" 
    do 
        echo "Training on " $ARG 
        python trainPASCAL_MC.py $ARG batch
    done 
} 

#apply cat chair tvmonitor
apply cow aeroplane bicycle bird boat bottle bus cat chair car

