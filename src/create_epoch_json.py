#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 14:55:18 2021

@author:
"""

from PIL import Image
def create_nft_template(img_size=128):
    img = Image.new("RGB", (img_size, img_size), (255, 0, 255))
    img.save("../public/nft_temp_draft.png", "PNG")

import json
start_time= 1641474000*1000
short_duration = 1*3600*1000
long_duration  = 2*3600*1000
between_duration = 10*60*1000
                    
def create_epoch_px_lookup(img=128,epoch_base=8):
    epoch=dict()
    px_list=list()
    step_size=img/epoch_base
    step_size_old=0
    counter=0
    loops=2
    shift=0
    for loop in range(loops):
        shift=step_size_old+shift
        #first horizontal row
        for n in range(int((img-loop*step_size_old)/step_size)):
            top_left_corner=(n*step_size+shift,0+shift)
            bottom_right_corner=((n+1)*step_size-1+shift,step_size-1+shift)
            px_list=[top_left_corner,bottom_right_corner]
            epoch["epoch_"+str(counter)]={}
            epoch["epoch_"+str(counter)]["px"]=px_list
            create_epoch_time_lookup(step_size,counter,epoch)
            counter=counter+1
        #right vertical colum    
        for n in range(int((img-loop*step_size_old)/step_size)-2):
            top_left_corner=(img-step_size-shift,(1+n)*step_size+shift)
            bottom_right_corner=(img-1-shift,(n+2)*step_size-1+shift)
            px_list=[top_left_corner,bottom_right_corner]
            epoch["epoch_"+str(counter)]={}
            epoch["epoch_"+str(counter)]["px"]=px_list
            create_epoch_time_lookup(step_size,counter,epoch)
            counter=counter+1
        #last horizontal row
        for n in range(int((img-loop*step_size_old)/step_size)):
            top_left_corner=(img-(1+n)*step_size-shift,img-step_size-shift)
            bottom_right_corner=(img-n*step_size-1-shift,img-1-shift)
            px_list=[top_left_corner,bottom_right_corner]
            epoch["epoch_"+str(counter)]={}
            epoch["epoch_"+str(counter)]["px"]=px_list
            create_epoch_time_lookup(step_size,counter,epoch)
            counter=counter+1
        #right vertical colum    
        for n in range(int((img-loop*step_size_old)/step_size)-2):
            top_left_corner=(0+shift,img-(n+2)*step_size-shift)
            bottom_right_corner=(step_size-1+shift,img-(n+1)*step_size-1-shift)
            px_list=[top_left_corner,bottom_right_corner]
            epoch["epoch_"+str(counter)]={}
            epoch["epoch_"+str(counter)]["px"]=px_list
            create_epoch_time_lookup(step_size,counter,epoch)
            counter=counter+1
        step_size_old=step_size
        step_size=step_size*2
    
    top_left_corner=(shift+step_size_old,0+shift+step_size_old)
    bottom_right_corner=(step_size/2-1+shift+step_size_old,step_size/2-1+shift+step_size_old)
    px_list=[top_left_corner,bottom_right_corner]
    epoch["epoch_"+str(counter)]={}
    epoch["epoch_"+str(counter)]["px"]=px_list
    create_epoch_time_lookup(step_size,counter,epoch)
    return epoch

def create_epoch_time_lookup(stepsize,counter,epoch):
    end_last_epoch= epoch.get("epoch_"+str(counter-1),{}).get("time",{}).get("end_epoch",0)
    if end_last_epoch==0:
        end_last_epoch=start_time-between_duration
    epoch_string="epoch_"+str(counter)
    if(stepsize > 8):
        epoch[epoch_string]["time"]={"start_epoch":end_last_epoch+between_duration,"end_epoch":int(end_last_epoch+long_duration+between_duration)}
    else:
        epoch[epoch_string]["time"]={"start_epoch":end_last_epoch+between_duration,"end_epoch":int(end_last_epoch+short_duration+between_duration)}

  
def show_epochs(epoch,img_size=256):
    from PIL import ImageDraw  
    out = Image.new("RGB", (img_size, img_size), (255, 255, 255))
    draw = ImageDraw.Draw(out)
    for key in epoch.keys():
        draw.rectangle(epoch[key]["px"], fill=None, outline=(0,0,0), width=1)
        ep=key[-2:]
        if("_" in ep):
          ep=ep[1:]  
        til_size=min((epoch[key]["px"][1][0]-epoch[key]["px"][0][0]+1)/2-5,0)
        print(til_size)
        draw.text([epoch[key]["px"][0][0]+til_size,epoch[key]["px"][0][1]+til_size],ep,fill=(0,0,0))
    out.show()        


def main():
   img=64
   #create_nft_template(img_size=img)
   epoch=create_epoch_px_lookup(img=img,epoch_base=8)
   show_epochs(epoch,img_size=img)
   epoch["epoch"]=0
   with open("../public/epoch.json", 'w') as f:
        json.dump(epoch, f)

if __name__ == "__main__":
    main()

