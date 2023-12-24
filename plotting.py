from datetime import datetime
import os
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import pandas as pd
import re


dir = 'C:/Users/Cameron/Documents/geog5092/final/evForPlots'

rast_list = []

for filename in os.listdir(dir):
    path = os.path.join(dir, filename)
    if path.endswith(".tif"):
        with rasterio.open(path) as rast_file:
            data = rast_file.read(1)  
            rast_list.append(data)


alist = rast_list[::2]
indices = [6, 9, 10, 11]
aur_list = [arr.flat[indices] for arr in alist]

fflist = rast_list[1::2]
ff_list = [arr[1][1] for arr in fflist]


aurdf = pd.DataFrame(aur_list)
ffdf = pd.DataFrame(ff_list)

current_columns = aurdf.columns

column_mapping = {col: 'NDVI' for col in current_columns}

aurdf.rename(columns=column_mapping, inplace=True)
ffdf.rename(columns={ffdf.columns[0]: 'NDVI'}, inplace=True)

dates = ['1/3', '1/10', '1/17', '1/24', '1/31', '2/7', '2/14', '2/21', '2/28', '3/7', '3/14', '3/21', '3/28', '4/4',
         '4/11', '4/18', '4/25', '5/2', '5/9', '5/16', '5/23', '5/30', '6/6', '6/13', '6/20', '6/27', '7/4', '7/11',
         '7/18', '7/25', '8/1', '8/8', '8/15', '8/22', '8/29', '9/5', '9/12', '9/19', '9/26', '10/3', '10/10', '10/17',
         '10/24', '10/31', '11/07', '11/14']

year = 2023

date_objects = [datetime.strptime(f"{year}/{date}", "%Y/%m/%d").date() for date in dates]

aurdf['date'] = dates
ffdf['date'] = dates


aurdf1 = aurdf.iloc[:, [0, -1]].copy()
aurdf2 = aurdf.iloc[:, [1, -1]].copy()
aurdf3 = aurdf.iloc[:, [2, -1]].copy()
aurdf4 = aurdf.iloc[:, [3, -1]].copy()



plt.figure(figsize=(10, 6))
# Scatter plot
plt.scatter(aurdf1['date'], aurdf1['NDVI'], label='Points', marker='o')
# Line plot
plt.plot(aurdf1['date'], aurdf1['NDVI'], label='Line', color='green', linestyle='-')
# Set labels and title
plt.title("Auraria Campus NDVI Pixel 1")
plt.xlabel("Date")
plt.ylabel("NDVI")
# Show the plot
plt.show()