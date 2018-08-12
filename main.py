import configparser
import os

import image_downloaders.google_image_download as gim
import image_downloaders.train_test_split as tt
import trainer as tr

try:
    import predictors.from_webcam as pweb
except Exception as e:
    print(str(e))
import argparse

import sys

parser = argparse.ArgumentParser(description='Train an image classifier.')
parser.add_argument('--config', help='Get a new set of images', default='config.ini')
parser.add_argument('--new', help='Get a new set of images', action='store_true')
parser.add_argument('--split', help='Get images from images from image library and split in to train and test data', action='store_true')
parser.add_argument('--train', help='Train the model from data in test and train directories', action='store_true')
parser.add_argument('--predictcam', help='Run predictions from webcam', action='store_true')

args = parser.parse_args()

root_dir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.sections()
config.read(os.path.join(root_dir,args.config)) 

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
if args.new:
    gim.download(classes, (nb_validation_samples + nb_train_samples) * 1.5)
    #tidies up files that aren't big enough to use as training data
    gim.s3_publish(os.path.join(root_dir,'image_library'),s3_image_library,classes, [im_lib_width, im_lib_height]) 

if args.split:
    tt.s3_train_test_split(s3_image_library, root_dir, classes, nb_train_samples, nb_validation_samples)

#train
if args.train:
    t = tr.trainer(root_dir, classes.split(','))
    t.train(nb_train_samples=nb_train_samples, nb_validation_samples=nb_validation_samples, epochs=epochs, batch_size=batch_size,img_width=resize_width, img_height=resize_height)

if args.predictcam:
    pweb.predict(os.path.join(root_dir, "resources"))