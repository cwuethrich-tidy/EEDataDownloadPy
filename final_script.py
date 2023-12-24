import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path
from datetime import datetime
import os
import numpy as np
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import argparse

# Set the URL for EE API
api_url_log = 'https://m2m.cr.usgs.gov/api/api/json/stable/login'

username = 'wuethrca'
password = '-v|4Uv_s26Vve_d'

credentials = {"username": username, "password": password}

    # Make the HTTP POST request to obtain the API key
response = requests.post(api_url_log, json=credentials)
    
    # Extract the API key from the response
apiKey = response.json().get("data")
print(f"API Key: {apiKey}")


 
# send http request
def sendRequest(url, data, apiKey = None):  
    json_data = json.dumps(data)
    
    if apiKey == None:
        response = requests.post(url, json_data)
    else:
        headers = {'X-Auth-Token': apiKey}              
        response = requests.post(url, json_data, headers = headers)    
    
    try:
      httpStatusCode = response.status_code 
      if response == None:
          print("No output from service")
          sys.exit()
      output = json.loads(response.text)	
      if output['errorCode'] != None:
          print(output['errorCode'], "- ", output['errorMessage'])
          sys.exit()
      if  httpStatusCode == 404:
          print("404 Not Found")
          sys.exit()
      elif httpStatusCode == 401: 
          print("401 Unauthorized")
          sys.exit()
      elif httpStatusCode == 400:
          print("Error Code", httpStatusCode)
          sys.exit()
    except Exception as e: 
          response.close()
          print(e)
          sys.exit()
    response.close()
    
    return output['data']


if __name__ == '__main__': 
    #NOTE :: Passing credentials over a command line arguement is not considered secure
    #        and is used only for the purpose of being example - credential parameters
    #        should be gathered in a more secure way for production usage
    #Define the command line arguements
    
    # user input    
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True, help='Username')
    parser.add_argument('-p', '--password', required=True, help='Password')
    
    args = parser.parse_args()
    
    username = args.username
    password = args.password     

    print("\nRunning Scripts...\n")
    
    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
    
    # login
    payload = {'username' : username, 'password' : password}
    
    apiKey = sendRequest(serviceUrl + "login", payload)
    
    print("API Key: " + apiKey + "\n")
    
    datasetName = ""
    
    spatialFilter =  {}
                     
    temporalFilter = {}
    
    payload = {'datasetName' : datasetName,
                               'spatialFilter' : spatialFilter,
                               'temporalFilter' : temporalFilter}                     
    
    print("Searching datasets...\n")
    datasets = sendRequest(serviceUrl + "dataset-search", payload, apiKey)
    
    print("Found ", len(datasets), " datasets\n")
    
    # download datasets
    for dataset in datasets:
        
        # Because I've ran this before I know that I want GLS_ALL, I don't want to download anything I don't
        # want so we will skip any other datasets that might be found, logging it incase I want to look into
        # downloading that data in the future.
        if dataset['datasetAlias'] != datasetName:
            print("Found dataset " + dataset['collectionName'] + " but skipping it.\n")
            continue
            
        # I don't want to limit my results, but using the dataset-filters request, you can
        # find additional filters
        
        acquisitionFilter = {"end": "2005-12-10",
                             "start": "2000-12-10" }        
            
        payload = {'datasetName' : dataset['datasetAlias'], 
                                 'maxResults' : 2,
                                 'startingNumber' : 1, 
                                 'sceneFilter' : {
                                                  'spatialFilter' : spatialFilter,
                                                  'acquisitionFilter' : acquisitionFilter}}
        
        # Now I need to run a scene search to find data to download
        print("Searching scenes...\n\n")   
        
        scenes = sendRequest(serviceUrl + "scene-search", payload, apiKey)
    
        # Did we find anything?
        if scenes['recordsReturned'] > 0:
            # Aggregate a list of scene ids
            sceneIds = []
            for result in scenes['results']:
                # Add this scene to the list I would like to download
                sceneIds.append(result['entityId'])
            
            # Find the download options for these scenes
            # NOTE :: Remember the scene list cannot exceed 50,000 items!
            payload = {'datasetName' : dataset['datasetAlias'], 'entityIds' : sceneIds}
                                
            downloadOptions = sendRequest(serviceUrl + "download-options", payload, apiKey)
        
            # Aggregate a list of available products
            downloads = []
            for product in downloadOptions:
                    # Make sure the product is available for this scene
                    if product['available'] == True:
                         downloads.append({'entityId' : product['entityId'],
                                           'productId' : product['id']})
                         
            # Did we find products?
            if downloads:
                requestedDownloadsCount = len(downloads)
                # set a label for the download request
                label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Customized label using date time
                payload = {'downloads' : downloads,
                                             'label' : label}
                # Call the download to get the direct download urls
                requestResults = sendRequest(serviceUrl + "download-request", payload, apiKey)          
                              
                # PreparingDownloads has a valid link that can be used but data may not be immediately available
                # Call the download-retrieve method to get download that is available for immediate download
                if requestResults['preparingDownloads'] != None and len(requestResults['preparingDownloads']) > 0:
                    payload = {'label' : label}
                    moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", payload, apiKey)
                    
                    downloadIds = []  
                    
                    for download in moreDownloadUrls['available']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            print("DOWNLOAD: " + download['url'])
                        
                    for download in moreDownloadUrls['requested']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            print("DOWNLOAD: " + download['url'])
                     
                    # Didn't get all of the reuested downloads, call the download-retrieve method again probably after 30 seconds
                    while len(downloadIds) < (requestedDownloadsCount - len(requestResults['failed'])): 
                        preparingDownloads = requestedDownloadsCount - len(downloadIds) - len(requestResults['failed'])
                        print("\n", preparingDownloads, "downloads are not available. Waiting for 30 seconds.\n")
                        time.sleep(30)
                        print("Trying to retrieve data\n")
                        moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", payload, apiKey)
                        for download in moreDownloadUrls['available']:                            
                            if download['downloadId'] not in downloadIds and (str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']):
                                downloadIds.append(download['downloadId'])
                                print("DOWNLOAD: " + download['url']) 
                            
                else:
                    # Get all available downloads
                    for download in requestResults['availableDownloads']:
                        # TODO :: Implement a downloading routine
                        print("DOWNLOAD: " + download['url'])   
                print("\nAll downloads are available to download.\n")
        else:
            print("Search found no results.\n")
                
    # Logout so the API Key cannot be used anymore
    endpoint = "logout"  
    if sendRequest(serviceUrl + endpoint, None, apiKey) == None:        
        print("Logged Out\n\n")
    else:
        print("Logout Failed\n\n") 





'''
####### Raster Processing #########
####### Plotting Time Series #########

aur_list = []
ff_list = []

# Create raster stack
aur_stack = gpd.read_file(aur_list)
ff_stack = gpd.read_file(ff_list)

# Raster to DataFrame
aur_df = aur_stack.melt(id_vars=['geometry'], var_name='date', value_name='NDVI')
aur_df = aur_df.dropna().reset_index(drop=True)

ff_df = ff_stack.melt(id_vars=['geometry'], var_name='date', value_name='NDVI')
ff_df = ff_df.dropna().reset_index(drop=True)

# Convert date column to datetime
aur_df['date'] = pd.to_datetime(aur_df['date'])
ff_df['date'] = pd.to_datetime(ff_df['date'])

# Round NDVI values
aur_df['NDVI'] = round(aur_df['NDVI'], 2)
ff_df['NDVI'] = round(ff_df['NDVI'], 2)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(aur_df['date'], aur_df['NDVI'], label='Auraria Campus')
plt.plot(aur_df['date'], aur_df['NDVI'])
plt.title('Auraria Campus Mean NDVI')
plt.xlabel('Date')
plt.ylabel('NDVI')
plt.legend()
plt.show()

plt.figure(figsize=(10, 6))
plt.scatter(ff_df['date'], ff_df['NDVI'], label='Five Fridges Farm')
plt.plot(ff_df['date'], ff_df['NDVI'])
plt.title('Five Fridges Farm NDVI')
plt.xlabel('Date')
plt.ylabel('NDVI')
plt.legend()
plt.show()

'''