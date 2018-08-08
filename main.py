import configparser
import os

import image_downloaders.google_image_download as gim
import image_downloaders.train_test_split as tt
import trainer as tr

import sys

config_file = 'config.ini'
if len(sys.argv)==1:
    config_file = sys.argv[0]


root_dir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.sections()
config.read(os.path.join(root_dir,config_file)) 

classes = config['classes']['class_names']
resize_width = int(config['classes']['resize_width'])
resize_height = int(config['classes']['resize_height'])
files_per_class =  int(config['classes']['files_per_class'])
nb_train_samples = int(config['hyperparameters']['nb_train_samples'])
nb_validation_samples = int(config['hyperparameters']['nb_validation_samples'])
epochs = int(config['hyperparameters']['epochs'])
batch_size = int(config['hyperparameters']['batch_size'])
im_lib_height = int(config['image_library']['image_height'])
im_lib_width = int(config['image_library']['image_width'])
image_libary_location=config['image_library']['location']
s3_image_library=config['image_library']['s3']

# get some files from google
# gim.download(classes, (nb_validation_samples + nb_train_samples) * 1.5)

#tidies up files that aren't big enough to use as training data
# gim.publish(os.path.join(root_dir,'image_library'),image_libary_location,classes, [im_lib_width, im_lib_height]) 

#move files to train and test dirs
tt.s3_train_test_split(s3_image_library, root_dir, classes, nb_train_samples, nb_validation_samples)

#train
t = tr.trainer(root_dir, classes.split(','))
t.train(nb_train_samples=nb_train_samples, nb_validation_samples=nb_validation_samples, epochs=epochs, batch_size=batch_size,img_width=resize_width, img_height=resize_height)
