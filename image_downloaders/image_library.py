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

import threading

import boto3
import botocore
from PIL import Image

import image_downloaders.im as im  # importing the library

class ImageLibrary():

    logger = None
    s3_bucket_name = None
    bucket = None

    def __init__(self, logger, s3_bucket_name):
        self.s3_bucket_name = s3_bucket_name
        self.logger = logger

        s3 = boto3.resource('s3')
        self.bucket = s3.Bucket(s3_bucket_name)

    #moves files from temporary directories to s3 if they're big enough
    def s3_publish(self, source_directory_name, bucket_name, classes, resize_to, files_per_class, files_published=0):

        for class_ in classes.split(','):    
            uploaded = 0 
            for file in os.listdir(os.path.join(source_directory_name,class_)):
                from_file = os.path.join(source_directory_name,class_,file)
                to_file = os.path.join(tempfile.gettempdir(),os.path.splitext (file)[0] + '.png')           
                self.logger.info("Rename {} to {}".format(from_file,to_file))
                try:
                    self.logger.info("File size = {}".format(os.path.getsize(from_file)))
                    im = Image.open(from_file)
                    im = im.convert("RGBA")             
                    width,height = im.size
                    if width > resize_to[0] and height > resize_to[1]:
                        im.thumbnail(resize_to,Image.ANTIALIAS)
                        im.save(to_file,"png")
                        self.bucket.upload_file(to_file, "{}/{}".format(class_,os.path.splitext (file)[0] + '.png'))
                        self.logger.info("Publish to {}".format(class_,os.path.splitext (file)[0] + '.png'))
                        os.remove(to_file)
                    os.remove(from_file)
                    self.logger.info("Saved to {}/{}".format(class_,os.path.splitext (file)[0] + '.png'))
                    uploaded += 1
                except Exception as ex:
                    self.logger.info ("Failed: {}".format(str(ex)))
            if uploaded + files_published < files_per_class :
                #there weren't enough files, download some more and try again
                self.logger.info("Not enough files found ({} so far), downloading more".format(uploaded + files_published))
                self.download(class_, files_per_class, False)
                self.s3_publish(source_directory_name, bucket_name, class_, resize_to, files_per_class, uploaded + files_published)    

    def count_files_in_s3 (self, classes):
        self.logger.info("Class    Images")
        object_count_dict = dict()

        # Count available images
        for class_ in classes.split(','):
            object_count = 0
            for object_ in self.bucket.objects.filter(Prefix=class_):
                object_count += 1
            self.logger.info("{} {}".format (class_,object_count))    
            object_count_dict[class_] = object_count          

        return object_count_dict          

    #retrieves files_per_class images from google images for each class in classes
    def download(self, classes, files_per_class,prime=True):             

        project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        train = os.path.join(project_dir,'image_library')
        if prime:
            directory.prime(train)
        response = im.googleimagesdownload()   #class instantiation

        self.logger.info (platform.system())
        if platform.system() == 'Darwin':
            chromedriver = os.path.join(project_dir,'chromedriver_osx')
        elif platform.system() == 'Linux':
            chromedriver = os.path.join(project_dir,'chromedriver_linux')
        elif platform.system() == 'Windows':
            chromedriver = os.path.join(project_dir,'chromedriver_win32')
        else:
            self.logger.error ('OS not supported')
            exit()

        prefix = "photo"

        threads = []
        threadid = 0

        for class_ in classes.split(','):
            
            self.logger.info ("Searching for {}".format(class_))
            if prime:
                directory.prime(os.path.join(train,class_))

            #arguments = {"proxy":"192.168.1.63:3128","keywords":class_,"prefix_keywords":site,"suffix_keywords":salt,"limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments
            arguments = {"keywords":class_,"prefix_keywords":prefix,"suffix-keywords":"none","limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments

            thread = downloader_thread(threadid, self.logger, self, arguments, response, class_, train)
            thread.start()
            threads.append(thread)
            threadid+=1

                # Wait for all threads to complete
        for t in threads:
            t.join()
        self.logger.info("All downloader threads finished")            

    def s3_train_test_split(self, project_dir, classes, train_images = 10, test_images = 5):

        insufficient_images = False

        # Count available images
        for class_,count_ in self.count_files_in_s3(classes).items():
            if count_ < train_images + test_images:
                insufficient_images = True
                self.logger.error("Not enough images for class {}".format(class_))

        if insufficient_images:
            raise Exception("Not enough images in the image library to support this model")

        train_dir = os.path.join(project_dir,"train") 
        test_dir = os.path.join(project_dir,"test")
        directory.prime(train_dir)
        directory.prime(test_dir)    

        threadid = 0
        threads = []

        for class_ in classes.split(','):
            thread = spliiter_thread(threadid, self.logger, self, class_,train_dir, test_dir, train_images, test_images)
            thread.start()
            threads.append(thread)
            threadid+=1

        # Wait for all threads to complete
        for t in threads:
            t.join()
        self.logger.info("All threads finished")

    def split_class (self,class_,train_dir, test_dir, train_images, test_images):
            try:
                train_class_dir = os.path.join(train_dir, class_)
                test_class_dir = os.path.join(test_dir, class_)
                directory.prime(train_class_dir)
                directory.prime(test_class_dir)
                copied = 0
                for file_ in self.bucket.objects.filter(Prefix=class_):
                    self.logger.info(file_)
                    target = None
                    if copied < train_images:                 
                        target = os.path.join(train_dir, file_.key)
                    elif copied < (train_images + test_images):                 
                        target = os.path.join(test_dir, file_.key)    
                    else:
                        self.logger.info("Done")
                        break 
                    try:
                        self.logger.info("Class [{}] image {}: {} -> {}".format(class_,copied,file_.key,target))                        
                        self.bucket.download_file(file_.key, target)
                        im = Image.open(target)
                        im.load()
                        copied += 1
                    except Exception as e:
                        self.logger.error ("Class [{}] image {} failed. Exception: {}".format(class_,copied,str(e)))
                        if os.path.exists(target) and not os.path.isdir(target):
                            os.remove(target) 

            except Exception as e:
                self.logger.error ("Class [{}] failed, exception: {}".format(class_,str(e))) 
                raise Exception ("Train test split failed for class [{}]. Error Message: {}".format(class_,str(e)))                     

class spliiter_thread (threading.Thread):
    def __init__(self, threadID, logger, image_library, class_,train_dir, test_dir, train_images, test_images):
        threading.Thread.__init__(self)
        self.logger = logger
        self.threadID = threadID
        self.image_library = image_library
        self.class_ = class_
        self.train_dir = train_dir
        self.test_dir = test_dir
        self.train_images = train_images
        self.test_images = test_images
    def run(self):
        self.logger.info ("Starting " + self.name)
        self.image_library.split_class(self.class_,self.train_dir, self.test_dir, self.train_images, self.test_images)
        self.logger.info("Exiting " + self.name)            


class downloader_thread (threading.Thread):
    def __init__(self, threadID, logger, image_library, arguments, response, class_, train):
        threading.Thread.__init__(self)
        self.logger = logger
        self.threadID = threadID
        self.image_library = image_library
        self.arguments = arguments
        self.response = response
        self.class_ = class_
        self.train = train
        self.name = "Image-Download-Thread-[{}]".format(self.class_)
    def run(self):
        self.logger.info ("Starting " + self.name)
        moveto =  os.path.join(self.train,self.class_)
        image_limit = int(self.arguments["limit"])
        files_downloaded = 0
        while files_downloaded < image_limit:
            self.logger.info ("{} [{}] images downloaded so far".format(files_downloaded,self.class_))
            while True:
                salt = str(uuid.uuid4())[:5]    
                if not salt.isdigit():
                    break
                else:
                    self.logger.info ("Salt {} is a digit, which is not allowed".format(salt))
            self.arguments["suffix_keywords"] = salt
            downloaded = self.response.download (self.arguments)
            folder = "{} {} {}".format(self.arguments["prefix_keywords"], self.class_, self.arguments["suffix_keywords"])
            for file_ in downloaded[folder]:
                self.logger.info ("Move {} to {}".format(file_, os.path.join(self.train,self.class_)))
                try:
                    shutil.move(file_, moveto)
                except:
                    pass      
            files_downloaded += len(os.listdir(moveto))   

        self.logger.info("Exiting {}. {} images downloaded".format(self.name, files_downloaded) )    