import os
import configparser
from shutil import copy2

def directory_prime (directory_path):
    if not os.path.exists(directory_path):
        os.mkdir (directory_path)  
    else:
        for file in os.listdir(directory_path):
            os.remove(os.path.join(directory_path,file))

def train_test_split(project_dir,classes,train_images = 10,test_images = 5):
    for class_ in classes.split(','): 

        train_class_dir = os.path.join(project_dir,"train",class_)
        test_class_dir = os.path.join(project_dir,"test",class_)
        directory_prime(train_class_dir)
        directory_prime(test_class_dir)

        copied = 0
        for file in os.listdir(os.path.join(project_dir,"image_library",class_)):
            if copied < train_images:   
                from_ = os.path.join(project_dir,"image_library",class_,file)
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

if __name__ == "__main__":             

    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    config = configparser.ConfigParser()
    config.sections()
    config.read(os.path.join(root_dir,'config.ini')) 
    classes = config['classes']['class_names']
    train_test_split(root_dir,classes,10,10)