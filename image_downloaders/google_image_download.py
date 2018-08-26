import configparser
from image_downloaders import directory
import io
import os
import pathlib
import platform
import shutil
import tempfile
import uuid
from shutil import copy2

import boto3
import botocore
from PIL import Image

import image_downloaders.im as im  # importing the library


def publish(source_directory_name, target_directory_name, classes, resize_to):
    for class_ in classes.split(','):
        directory.prime(target_directory_name + class_)        
        for file in os.listdir(os.path.join(source_directory_name,class_)):

            from_file = os.path.join(source_directory_name,class_,file)
            to_file = os.path.join(target_directory_name, class_ ,os.path.splitext (file)[0] + '.png')           
            print ("Rename {} to {}".format(from_file,to_file))
            try:
                print("File size = {}".format(os.path.getsize(from_file)))
                im = Image.open(from_file)
                im = im.convert("RGBA")             
                width,height = im.size
                if width > resize_to[0] and height > resize_to[1]:
                    im.thumbnail(resize_to,Image.ANTIALIAS)
                    im.save(to_file,"png")
                    print("Saved")
            except Exception as ex:
                print ("Failed: {}".format(str(ex)))

#moves files from temporary directories to s3 if they're big enough
def s3_publish(source_directory_name, bucket_name, classes, resize_to):

    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket_name)

    for class_ in classes.split(','):     
        for file in os.listdir(os.path.join(source_directory_name,class_)):
            from_file = os.path.join(source_directory_name,class_,file)
            to_file = os.path.join(tempfile.gettempdir(),os.path.splitext (file)[0] + '.png')           
            print ("Rename {} to {}".format(from_file,to_file))
            try:
                print("File size = {}".format(os.path.getsize(from_file)))
                im = Image.open(from_file)
                im = im.convert("RGBA")             
                width,height = im.size
                if width > resize_to[0] and height > resize_to[1]:
                    im.thumbnail(resize_to,Image.ANTIALIAS)
                    im.save(to_file,"png")
                    my_bucket.upload_file(to_file, "{}/{}".format(class_,os.path.splitext (file)[0] + '.png'))
                    os.remove(to_file)
                os.remove(from_file)
                print("Saved to {}/{}".format(class_,os.path.splitext (file)[0] + '.png'))
            except Exception as ex:
                print ("Failed: {}".format(str(ex)))

#retrieves files_per_class images from google images for each class in classes
def download(classes, files_per_class):             

    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    train = os.path.join(project_dir,'image_library')
    response = im.googleimagesdownload()   #class instantiation

    print (platform.system())
    if platform.system() == 'Darwin':
        chromedriver = os.path.join(project_dir,'chromedriver_osx')
    elif platform.system() == 'Linux':
        chromedriver = os.path.join(project_dir,'chromedriver_linux')
    elif platform.system() == 'Windows':
        chromedriver = os.path.join(project_dir,'chromedriver_win32')
    else:
        print ('OS not supported')
        exit()

    salt = str(uuid.uuid4())[:4]    
    print ("Image search salt: {}".format(salt))
    arguments = {"keywords":classes,"suffix_keywords":salt,"limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','format':'png','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments
    return response.download(arguments)   