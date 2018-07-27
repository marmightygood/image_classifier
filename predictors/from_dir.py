import os
import pickle
import uuid

import cv2
import keras
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from keras import backend as K
from keras.datasets import mnist
from keras.layers import (Activation, Conv2D, Dense, Dropout, Flatten,
                          MaxPooling2D)
from keras.models import Sequential, load_model
from keras.optimizers import SGD
from keras.preprocessing import image
from keras.preprocessing.image import (ImageDataGenerator, array_to_img,
                                       img_to_array, load_img)


def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)      

def get_classname(classes, index):
    for class_name, lindex in classes.items():    # for name, age in list.items():  (for Python 3.x)
        if lindex == index:
            return class_name                              

model = load_model('model.please')
model.load_weights('weights.please')
classes = load_obj('classes')

# dimensions of our images.
img_width, img_height = 120, 90

train_data_dir = 'train'
validation_data_dir = 'test'
predict_data_dir = 'predict'
nb_train_samples = 400
nb_validation_samples = 200
epochs = 250
batch_size = 80
predict_data_dir = 'predict'
resize_to = img_width, img_height

for file in os.listdir(predict_data_dir):
    from_file = os.path.join(predict_data_dir,file)
    to_file =   os.path.join(predict_data_dir, str(uuid.uuid4())[:4]) + '.png'           
    print ("Rename {} to {}".format(from_file, to_file))
    try:
        print("File size = {}".format(os.path.getsize(from_file)))
        im = Image.open(from_file) 
        im = im.convert("RGBA")             
        width, height = im.size
        if width >= 100 or height >= 100:
            im.thumbnail(resize_to, Image.ANTIALIAS)
            im.save(to_file, "png")
        else:
            print ("File {} is too small".format(from_file))                
    except Exception as ex:
        print ("Failed: {}".format(str(ex)))
    os.remove(from_file) 
    print ("Removed: {}".format(from_file)) 

for image_ in os.listdir(predict_data_dir):
    img_orig = cv2.imread(os.path.join(predict_data_dir,image_))
    img_resize = cv2.resize(img_orig, (img_height,img_width))
    img_tensor = np.expand_dims(img_resize, axis=0) 
    img_tensor = img_tensor.astype("float32")
    img_tensor /= 255.

    predicted_class = model.predict_classes(img_tensor)
    probabilities = model.predict_proba(img_tensor)
    print (image_, get_classname(classes, predicted_class), probabilities)

