import configparser
import io
import os
import pathlib
import platform
import uuid
from shutil import copy2

from PIL import Image

import image_downloaders.im  as im # importing the library
import image_downloaders.train_test_split as train_test_split


def rename_and_delete(directory_name,classes, resize_to):
    for class_ in classes.split(','):
        for file in os.listdir(os.path.join(directory_name,class_)):
            from_file = os.path.join(directory_name,class_,file)
            to_file = os.path.join(directory_name,class_,os.path.splitext (from_file)[0]) + '.png'           
            print ("Rename {} to {}".format(from_file,to_file))
            try:
                print("File size = {}".format(os.path.getsize(from_file)))
                im = Image.open(from_file)
                im = im.convert("RGBA")             
                width,height = im.size
                if width > 110 and height > 80:
                    im.thumbnail(resize_to,Image.ANTIALIAS)
                    im.save(to_file,"png")
                else:
                    print ("File {} is too small - deleting".format(from_file))                
                if (from_file!=to_file):
                    os.remove(from_file)
            except Exception as ex:
                print ("Failed: {}".format(str(ex)))
                os.remove(from_file) 
                print ("Removed: {}".format(from_file)) 

def directory_prime (directory_path):
    if not os.path.exists(directory_path):
        os.mkdir (directory_path)  
    else:
        for file in os.listdir(directory_path):
            os.remove(os.path.join(directory_path,file))

def download(classes, files_per_class):             

    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    train = os.path.join(project_dir,'image_library')
    response = im.googleimagesdownload()   #class instantiation

    print (platform.system())
    if platform.system() == 'Darwin':
        chromedriver = os.path.join(project_dir,'chromedriver_osx')
    elif platform.system() == 'Linux':
        chromedriver = os.path.join(project_dir,'chromedriver_linux')
    else:
        print ('OS not supported')
        exit()
    
    arguments = {"keywords":classes,"limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','format':'png','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments
    return response.download(arguments)   


if __name__ == "__main__":    
    download('car,boat', 5)    
