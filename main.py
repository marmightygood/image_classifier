import configparser
import os

import image_downloaders.google_image_download as gim
import image_downloaders.train_test_split as tt
import trainer as tr

root_dir = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.sections()
config.read(os.path.join(root_dir,'config.ini')) 

classes = config['classes']['class_names']
resize_width = int(config['classes']['resize_width'])
resize_height = int(config['classes']['resize_height'])
files_per_class =  int(config['classes']['files_per_class'])
nb_train_samples = int(config['hyperparameters']['nb_train_samples'])
nb_validation_samples = int(config['hyperparameters']['nb_validation_samples'])
epochs = int(config['hyperparameters']['epochs'])
batch_size = int(config['hyperparameters']['batch_size'])
resize_to = [resize_width, resize_height]

# get some files from google
gim.download(classes, (nb_validation_samples + nb_train_samples) * 1.5)

#tidies up files that aren't big enough to use as training data
gim.rename_and_delete(os.path.join(root_dir,'image_library'),classes, resize_to) 

#move files to train and test dirs
tt.train_test_split(root_dir, classes, nb_train_samples, nb_validation_samples)

#train
t = tr.trainer(root_dir, classes.split(','))
t.train(nb_train_samples=nb_train_samples, nb_validation_samples=nb_validation_samples, epochs=epochs, batch_size=batch_size,img_width=resize_width, img_height=resize_height)
