import configparser
import io
import os
import pathlib
import platform
import shutil
import tempfile
import uuid
from shutil import copy2

from datetime import date
from datetime import timedelta

import threading
from image_downloaders import directory
from image_downloaders import im 

from PIL import Image


class ImageLibrary():

    logger = None
    library_directory = None
    project_dir = ""

    def __init__(self, logger,):

        self.logger = logger 
        self.project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.library_directory = os.path.join(self.project_dir,'image_library')   

    #retrieves files_per_class images from google images for each class in classes
    def download(self, classes, files_per_class,prime=True):             

        
        if prime:
            directory.prime(self.library_directory)
        response = im.googleimagesdownload()   #class instantiation

        self.logger.info (platform.system())
        if platform.system() == 'Darwin':
            chromedriver = os.path.join(self.project_dir,'chromedriver_osx')
        elif platform.system() == 'Linux':
            chromedriver = os.path.join(self.project_dir,'chromedriver_linux')
        elif platform.system() == 'Windows':
            chromedriver = os.path.join(self.project_dir,'chromedriver_win32')
        else:
            self.logger.error ('OS not supported')
            exit()

        prefix = "lego"

        threads = []
        threadid = 0

        for class_ in classes.split(','):
            
            self.logger.info ("Searching for {}".format(class_))
            if prime:
                directory.prime(os.path.join(self.library_directory,class_))

            #arguments = {"proxy":"192.168.1.63:3128","keywords":class_,"prefix_keywords":site,"suffix_keywords":salt,"limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments
            #arguments = {"keywords":class_,"prefix_keywords":prefix,"suffix-keywords":"none","limit":files_per_class,'output_directory':train,'chromedriver':chromedriver,'size':'>640*480','socket_timeout':'3', 'no_numbering':True,'time_range':'{"time_min":"09/20/2018","time_max":"09/23/2018"}'}   #creating list of arguments
            arguments = {"keywords":class_,"prefix_keywords":prefix,"limit":files_per_class,'output_directory':self.library_directory,'chromedriver':chromedriver,'size':'>640*480','socket_timeout':'3', 'no_numbering':True}   #creating list of arguments


            thread = downloader_thread(threadid, self.logger, self, arguments, response, class_, self.library_directory)
            thread.start()
            threads.append(thread)
            threadid+=1

                # Wait for all threads to complete
        for t in threads:
            t.join()
        self.logger.info("All downloader threads finished")            

    def split_class (self,class_,train_dir, test_dir, train_images, test_images):
        try:
            train_class_dir = os.path.join(train_dir, class_)
            test_class_dir = os.path.join(test_dir, class_)
            directory.prime(train_class_dir)
            directory.prime(test_class_dir)
            copied = 0
            source_dir = os.path.join(self.library_directory, "lego " + class_)
            for file_ in os.listdir(source_dir):
                self.logger.info(file_)
                target = None
                if copied < train_images:                 
                    target = os.path.join(train_dir,class_, file_)
                elif copied < (train_images + test_images):                 
                    target = os.path.join(test_dir,class_, file_)    
                else:
                    self.logger.info("Done")
                    break 
                try:
                    copy2(os.path.join(source_dir,file_), target)
                    copied += 1
                except Exception as e:
                    self.logger.error ("Class [{}] image {} failed. Exception: {}".format(class_,copied,str(e)))

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
        time_max = date.today()
        time_min = time_max - timedelta(days=180)
        image_limit = int(self.arguments["limit"])
        files_downloaded = 0
        
        while files_downloaded < image_limit:
            
            # while True:
            #     salt = str(uuid.uuid4())[:5]    
            #     if not salt.isdigit():
            #         break
            #     else:
            #         self.logger.info ("Salt {} is a digit, which is not allowed".format(salt))

            #self.arguments["suffix_keywords"] = salt
            
            #format time range
            str_min = time_min.strftime("%m/%d/%Y")
            str_max = time_max.strftime("%m/%d/%Y")
            str_range = '{"time_min":"' +str_min + '","time_max":"'+str_max+'"}'
            self.arguments['time_range'] = str_range

            self.logger.info ("{} [{}] images downloaded so far. Downloading images from {} to {}".format(files_downloaded,self.class_,str_min, str_max)) 

            downloaded = self.response.download (self.arguments)
            # #folder = "{} {} {}".format(self.arguments["prefix_keywords"], self.class_, self.arguments["suffix_keywords"])
            # folder = "{}".format(self.class_)


            # for file_ in downloaded[folder]:
            #     #self.logger.info ("Move {} to {}".format(file_, os.path.join(self.train,self.class_)))
            #     try:
            #         shutil.move(file_, moveto)
            #     except:
            #         pass      


            time_max = time_max - timedelta(days=180)    
            time_min = time_min - timedelta(days=180)     
            files_downloaded += len(os.listdir(moveto))   

        self.logger.info("Exiting {}. {} images downloaded".format(self.name, files_downloaded) )    