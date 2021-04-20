import os
import pickle
import uuid

from cv2 import cv2
import keras
import matplotlib.pyplot as plt
import numpy as np
from keras import backend as K
from keras.datasets import mnist
from keras.layers import (Activation, Conv2D, Dense, Dropout, Flatten,
                          MaxPooling2D)
from keras.models import Sequential, load_model
from keras.optimizers import SGD
from keras.preprocessing import image
from keras.preprocessing.image import (ImageDataGenerator, array_to_img,
                                       img_to_array, load_img)
from PIL import Image


def converter(x):
    #x has shape (batch, width, height, channels)
    return (0.21 * x[:,:,:,:1]) + (0.72 * x[:,:,:,1:2]) + (0.07 * x[:,:,:,-1:])

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)      

def get_classname(classes, index):
    for class_name, lindex in classes.items():    # for name, age in list.items():  (for Python 3.x)
        if lindex == index:
            return class_name     

def predict(resources_dir, img_width, img_height):

    # 0 means the default video capture device in OS
    video_capture = cv2.VideoCapture(0)

    model = load_model(os.path.join(resources_dir))

    classes = load_obj(os.path.join(resources_dir,'classes'))



    # infinite loop, break by key ESC
    while True:
        # Capture frame-by-frame
        ret, img_orig = video_capture.read()

        img_resize = cv2.resize(img_orig, (img_height,img_width))
        img_grey = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
        img_tensor = image.img_to_array(img_grey)                    # (height, width, channels)
        img_tensor = np.expand_dims(img_tensor, axis=0)         # (1, height, width, channels), add a dimension because the model expects this shape: (batch_size, height, width, channels)
        img_tensor /= 255.

        predicted_class = model.predict_classes(img_tensor)
        predictions = model.predict(img_tensor)
        prediction_prob = predictions[0][predicted_class]
        print (predictions[0])
        #predicted_probas = model.
        class_name = get_classname(classes, predicted_class)
        try:
            boxes = get_bb_candidates(img_tensor)
            #print (boxes)
            im_to_display = img_resize
            color = 0
            for box in boxes:
                try:
                    cv2.rectangle(img=im_to_display, pt1=(box[0], box[1]), pt2 =(box[2], box[3]),color=(0,color,0),thickness=1)
                    #cv2.imshow("boxes",im_to_display)
                    color+=1
                except:
                    pass

            img_grey = cv2.cvtColor(img_grey, cv2.COLOR_GRAY2RGB) 
            #im_to_display = np.concatenate((im_to_display, img_grey), axis=1) 
            im_to_display = cv2.resize(im_to_display, (640, 480))  
            if prediction_prob > 0.4:
                cv2.putText(im_to_display,class_name,(10,430),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),2)            
            else:
                cv2.putText(im_to_display,"Unknown Class",(10,430),cv2.FONT_HERSHEY_SIMPLEX ,0.5,(0,255,255),2)                            
                
            cv2.putText(im_to_display,str(prediction_prob),(10,475),cv2.FONT_HERSHEY_SIMPLEX ,0.5,(0,255,255),2)                            
            cv2.imshow("Guesstimator", im_to_display)

        except Exception as e:
            print (str(e))
        if cv2.waitKey(1) == 27: 
            break 
    cv2.destroyAllWindows()      

def get_bb_candidates (image):

    squares = []
    #get image size
    #print (image.shape)
    height = image.shape[1]
    width = image.shape[2]
    box_width = int(width / 10)
    box_height = int(height / 10)

    #print ("box dims = {} x {}".format(box_width, box_height))

    startx = 0
    while startx < width:
        starty = 0
        while starty < height:
            endx = startx + box_width
            endy = starty + box_height        
            boxdim = (startx, starty, endx, endy)
#            print(boxdim)
            try:
                squares.append (boxdim)
               #squares.append ({image[startx: starty, endx: endy], boxdim})
            except Exception as e:
                print (str(e))
            starty = starty + box_height
        startx = startx + box_width    

    return squares    

