from PIL import Image
import os

classes = "people,furniture,cars,appliances".split(',')
project_dir = os.path.dirname(os.path.realpath(__file__))

for _type in ['test', 'train']:
    for _class in classes:
        path = os.path.join(project_dir,_type, _class)
        print(path)
        for file in os.listdir(path):
            filepath = os.path.join(path, file)
            print (filepath)
            if os.path.getsize(filepath)==0:
                os.remove(filepath)
                print(" Removed")