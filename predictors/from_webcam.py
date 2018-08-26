import os
import pickle
import uuid

import cv2
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
    model = load_model(os.path.join(resources_dir,'model.please'))
    model.load_weights(os.path.join(resources_dir,'weights.please'))
    classes = load_obj(os.path.join(resources_dir,'classes'))

    # 0 means the default video capture device in OS
    video_capture = cv2.VideoCapture(0)

    # infinite loop, break by key ESC
    while True:
        if not video_capture.isOpened():
            sleep(5)
        # Capture frame-by-frame
        ret, img_orig = video_capture.read()

        img_resize = cv2.resize(img_orig, (img_height,img_width))
        img_grey = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
        img_tensor = image.img_to_array(img_grey)                    # (height, width, channels)
        img_tensor = np.expand_dims(img_tensor, axis=0)         # (1, height, width, channels), add a dimension because the model expects this shape: (batch_size, height, width, channels)
        img_tensor /= 255.

        predicted_class = model.predict_classes(img_tensor)
        class_name = get_classname(classes, predicted_class)
        try:

            print (class_name)
            img_grey = cv2.cvtColor(img_grey, cv2.COLOR_GRAY2RGB) 
            im_to_display = np.concatenate((img_resize, img_grey), axis=1) 
            im_to_display = cv2.resize(im_to_display, (1280, 480))  
            cv2.putText(im_to_display,class_name,(10,460),cv2.FONT_HERSHEY_SIMPLEX ,1,(0,255,255),2)            
            cv2.imshow("Guesstimator", im_to_display)


        except Exception as e:
            print (str(e))
        if cv2.waitKey(1) == 27: 
                break  # esc to quitCOLOR_BAYER_BGCOLOR_BAYER_BG2RGB
    cv2.destroyAllWindows()        

