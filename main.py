import configparser
import logging
import os

import image_downloaders.image_library as image_library
import trainer as tr
import sendmail as s

try:
    import predictors.from_webcam_beta as pweb
except Exception as e:
    print(str(e))
import argparse

import sys

def setup_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('log.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger

logger = setup_logger('image_classifier')

parser = argparse.ArgumentParser(description='Train an image classifier.')
parser.add_argument('--config', help='Get a new set of images', default='config.ini')
parser.add_argument('--new', help='Get a new set of images', action='store_true')
parser.add_argument('--split', help='Get images from images from image library and split in to train and test data', action='store_true')
parser.add_argument('--train', help='Train the model from data in test and train directories', action='store_true')
parser.add_argument('--predictcam', help='Run predictions from webcam', action='store_true')
parser.add_argument('--count', help='Counts files in s3', action='store_true')

args = parser.parse_args()

root_dir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.sections()
config.read(os.path.join(root_dir,args.config)) 

classes = config['classes']['class_names']
resize_width = int(config['classes']['resize_width'])
resize_height = int(config['classes']['resize_height'])
nb_train_samples = int(config['hyperparameters']['nb_train_samples'])
nb_validation_samples = int(config['hyperparameters']['nb_validation_samples'])
epochs = int(config['hyperparameters']['epochs'])
batch_size = int(config['hyperparameters']['batch_size'])
im_lib_height = int(config['image_library']['image_height'])
im_lib_width = int(config['image_library']['image_width'])
s3_image_library=config['image_library']['s3']

try:
    im_lib = image_library.ImageLibrary(logger, s3_image_library)    
    # get some files from google
    
    if args.new:
        im_lib.download(classes, (nb_validation_samples + nb_train_samples))
        #tidies up files that aren't big enough to use as training data
        im_lib.s3_publish(os.path.join(root_dir,'image_library'),s3_image_library,classes, [im_lib_width, im_lib_height],  (nb_validation_samples + nb_train_samples)) 
        s.send_notification("Get Test and Train data")

    if args.split:
        im_lib.s3_train_test_split(root_dir, classes, nb_train_samples, nb_validation_samples)
        s.send_notification("Train Test Split")

    #train
    if args.train:
        t = tr.trainer(root_dir, classes.split(','))
        t.train(nb_train_samples=nb_train_samples, nb_validation_samples=nb_validation_samples, epochs=epochs, batch_size=batch_size,img_width=resize_width, img_height=resize_height)
        s.send_notification("Training")

    if args.count:
        logger.info(im_lib.count_files_in_s3(classes))

    if args.predictcam:
        pweb.predict(os.path.join(root_dir, "resources"), resize_width, resize_height)
except Exception as e:
    logger.error((str(e)))
    s.send_notification("Error", str(e))        