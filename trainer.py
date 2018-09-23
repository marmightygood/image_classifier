from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
import os
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras import backend as K
import matplotlib
import matplotlib.pyplot as plt
import pickle

import configparser

class trainer():

    root_dir = ''
    train_data_dir = ''
    validation_data_dir  = ''
    predict_data_dir = ''
    visualisation_dir = ''
    resource_dir = ''
    classes=''

    def __init__(self, root_dir, classes):
        self.root_dir  = root_dir
        self.train_data_dir = os.path.join(root_dir,'train')
        self.validation_data_dir = os.path.join(root_dir,'test')
        self.predict_data_dir = os.path.join(root_dir,'predict')
        self.visualisation_dir = os.path.join(root_dir, 'visualisations')
        self.resource_dir = os.path.join(root_dir, 'resources')
        self.classes = classes

    def save_obj(self, obj, name ):
        with open(os.path.join(self.root_dir,"resources",name + '.pkl'), 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self, name ):
        with open(name + '.pkl', 'rb') as f:
            return pickle.load(f)

    def plot_history(self,series1, series2, title, ylabel, xlabel, legend):
        plt.switch_backend('agg')
        plt.plot(series1)
        plt.plot(series2)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.legend(legend, loc='upper left')
        print("{}.jpg".format(title))
        plt.savefig(os.path.join(self.root_dir, "visualisations","{}.jpg".format(title)))
        plt.clf()        

    def train(self, nb_train_samples, nb_validation_samples, epochs, batch_size, img_width, img_height):

        input_shape = (img_width, img_height, 1)

        model = Sequential()

        model.add(Conv2D(32, (3, 3), input_shape=input_shape))
        model.add(Activation('relu'))       
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.1))

        model.add(Conv2D(64, (3, 3)))
        model.add(Activation('relu'))       
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.1))

        model.add(Conv2D(128, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.1))

        # first (and only) set of FC => RELU layers
        model.add(Flatten())
        model.add(Dense(250))
        model.add(Activation("relu"))
        model.add(Dropout(0.1))    

        # softmax classifier - class_count
        model.add(Dense(len(self.classes)))
        model.add(Activation("softmax"))

        model.compile(loss='categorical_crossentropy',
                    optimizer='rmsprop',
                    metrics=['accuracy'])

        # this is the augmentation configuration we will use for training
        train_datagen = ImageDataGenerator(
            rescale=1. / 255,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True)

        # this is the augmentation configuration we will use for testing:
        # only rescaling
        test_datagen = ImageDataGenerator(rescale=1. / 255)

        train_generator = train_datagen.flow_from_directory(
            self.train_data_dir,
            target_size=(img_width, img_height),
            batch_size=batch_size,
            class_mode='categorical',
            color_mode='grayscale',
            horizontal_flip=True
            )

        print(train_generator.class_indices)

        self.save_obj(train_generator.class_indices, 'classes')

        validation_generator = test_datagen.flow_from_directory(
            self.validation_data_dir,
            target_size=(img_width, img_height),
            batch_size=batch_size,
            class_mode='categorical',
            color_mode='grayscale')

        history = model.fit_generator(
            train_generator,
            steps_per_epoch=nb_train_samples // batch_size,
            epochs=epochs,
            validation_data=validation_generator,
            validation_steps=nb_validation_samples // batch_size,
            verbose=2)

        model.save(os.path.join(self.root_dir, 'resources','model.please'))
        model.save_weights(os.path.join(self.root_dir, 'resources','weights.please'))

        #plot accuracy
        self.plot_history(
            history.history['acc'],
            history.history['val_acc'],
            'Accuracy',
            'model_accuracy',
            'epoch',
            ['train', 'validation']
        )

        #plot loss
        self.plot_history(
            history.history['loss'],
            history.history['val_loss'],
            'Loss',
            'model_loss',
            'epoch',
            ['train', 'validation']
        )

if __name__ == "__main__":

    root_dir = os.path.dirname(os.path.realpath(__file__))

    config = configparser.ConfigParser()
    config.sections()
    config.read(os.path.join(root_dir,'config.ini')) 

    nb_train_samples = int(config['hyperparameters']['nb_train_samples'])
    nb_validation_samples = int(config['hyperparameters']['nb_validation_samples'])
    epochs = int(config['hyperparameters']['epochs'])
    batch_size = int(config['hyperparameters']['batch_size'])
    resize_width = int(config['classes']['resize_width'])
    resize_height = int(config['classes']['resize_height'])
    classes = config['classes']['class_names']

    trainer = trainer(root_dir, classes.split(','))
    trainer.train (nb_train_samples, nb_validation_samples, epochs, batch_size, resize_width, resize_height)
