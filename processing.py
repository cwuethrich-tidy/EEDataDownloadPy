import pandas as pd
import geopandas as gpd
import fiona
import numpy as np
import rasterio
from rasterio.plot import show
import rasterio.mask
from shapely.geometry import mapping
import os

path = 'C:/Users/Cameron/Documents/geog5092/final/Shapefiles/ffbound/ffbound.shp'
dir = 'C:/Users/Cameron/Documents/geog5092/final/evPy'


print('hello')


'''
rast_list = []

for filename in os.listdir(dir):
    path = os.path.join(dir, filename)
    if path.endswith(".tif"):
        with rasterio.open(path) as rast_file: 
            rast_list.append(rast_file)
'''



