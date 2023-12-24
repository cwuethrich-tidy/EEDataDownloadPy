import os 
import zipfile

dir = 'C:/Users/Cameron/Documents/geog5092/final/evPy'
dir1 = 'C:/Users/Cameron/Documents/geog5092/final/eV23'
text = '3KM'
NDVI = '_NDVI.001'

def file_cleaning(directory_path, text):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path) and text not in filename:
            os.remove(file_path)

def unzip(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(directory_path)
            os.remove(file_path)





ev_sevenDay = [f for f in os.listdir(dir1) if os.path.isfile(os.path.join(dir1, f))]

all_files = os.listdir(dir)

for file in all_files:
    file_path = os.path.join(dir, file)
    if os.path.isfile(file_path) and file not in ev_sevenDay:
        os.remove(file_path)

#file_cleaning(dir, text)

#unzip(dir)

#file_cleaning(dir, NDVI)
