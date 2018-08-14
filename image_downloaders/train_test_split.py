import os
import configparser

import boto3
import botocore

import random

from shutil import copy2

def directory_prime (directory_path):
    if not os.path.exists(directory_path):
        os.mkdir (directory_path)  
    else:
        for file in os.listdir(directory_path):
            try:
                os.remove(os.path.join(directory_path,file))
            except Exception as e:
                print (str(e))
def train_test_split(image_library, project_dir,classes,train_images = 10,test_images = 5):

    train_class_dir = os.path.join(project_dir,"train")
    test_class_dir = os.path.join(project_dir,"test")
    directory_prime(train_class_dir)
    directory_prime(test_class_dir)

    for class_ in random.shuffle(classes.split(',')): 

        train_class_dir = os.path.join(project_dir,"train",class_)
        test_class_dir = os.path.join(project_dir,"test",class_)
        directory_prime(train_class_dir)
        directory_prime(test_class_dir)

    for class_ in random.shuffle(classes.split(',')): 

        copied = 0
        class_dir =os.path.join(image_library,class_)
        for file in os.listdir(class_dir):
            if copied < train_images:   
                from_ = os.path.join(image_library,class_,file)
                to = os.path.join(train_class_dir,file)
                print("{} -> {}".format(from_, to))
                try:
                    copy2(from_ ,to)
                    copied += 1
                except Exception as e:
                    print ("    -Copy failed: {}".format(str(e)))
            elif copied < (train_images + test_images):   
                from_ = os.path.join(project_dir,"image_library",class_,file)
                to = os.path.join(test_class_dir,file)                
                print("{} -> {}".format(from_, to))
                try:
                    copy2(from_ ,to)
                    copied += 1
                except Exception as e:
                    print ("    -Copy failed: {}".format(str(e)))
            else:
                print("done")
                break      

def s3_train_test_split(image_library, project_dir,classes,train_images = 10,test_images = 5):

    bucket_name = image_library
    s3 = boto3.resource('s3')

    train_dir = os.path.join(project_dir,"train") 
    test_dir = os.path.join(project_dir,"test")
    directory_prime(train_dir)
    directory_prime(test_dir)    

    my_bucket = s3.Bucket(bucket_name)
    for class_ in classes.split(','):
        try:
            train_class_dir = os.path.join(train_dir, class_)
            test_class_dir = os.path.join(test_dir, class_)
            directory_prime(train_class_dir)
            directory_prime(test_class_dir)
            copied = 0

            for file_ in my_bucket.objects.filter(Prefix=class_):
                print(file_)
                if copied < train_images:                 
                    print("{} -> {}".format(file_.key, os.path.join(train_dir, file_.key)))
                    try:
                        my_bucket.download_file(file_.key, os.path.join(train_dir, file_.key))
                        copied += 1
                    except Exception as e:
                        print ("    -Copy failed: {}".format(str(e)))
                elif copied < (train_images + test_images):                 
                    print("{} -> {}".format(file_.key, os.path.join(test_dir, file_.key)))
                    try:
                        my_bucket.download_file(file_.key, os.path.join(test_dir, file_.key))                        
                        copied += 1
                    except Exception as e:
                        print ("    -Copy failed: {}".format(str(e)))
                else:
                    print("done")
                    break 
        except Exception as e:
              print ("-Class failed: {}, {}".format(class_,str(e)))          

if __name__ == "__main__":             

    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config = configparser.ConfigParser()
    config.sections()
    config.read(os.path.join(root_dir,'config.ini')) 
    classes = config['classes']['class_names']
    s3_train_test_split('marginal-image-library', root_dir,classes,10,10)