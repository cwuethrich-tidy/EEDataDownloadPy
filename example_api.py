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
import json
import time
import sys
import time
import re
import threading
import datetime
import os


#from urllib.request import urlopen
#from shutil import copyfileobj
#from tempfile import NamedTemporaryFile

path = 'C:/Users/Cameron/Documents/geog5092/final/evPy' # Fill a valid download path
maxthreads = 5 # Threads count for downloads
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Customized label using date time
threads = []


# Set the URL for EE API
api_url_log = 'https://m2m.cr.usgs.gov/api/api/json/stable/login'

       
username = 'wuethrca'
password = '-v|4Uv_s26Vve_d'

credentials = {"username": username, "password": password}

# Make the HTTP POST request to obtain the API key
response = requests.post(api_url_log, json=credentials)
    
# Extract the API key from the response
apiKey = response.json().get("data")


 
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


def downloadFile(url, downloadId):
    sema.acquire()
    global path
    try:        
        response = requests.get(url, stream=True)
        disposition = response.headers['content-disposition']
        filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
        print(f"Downloading {filename} ...\n")
        filename = 'downloadId#' + str(downloadId) + '#' + filename
        if path != "" and path[-1] != "/":
            filename = "/" + filename
        open(path + filename, 'wb').write(response.content)
        print(f"Downloaded {filename}\n")
        sema.release()
    except Exception as e:
        print(f"Failed to download from {url}. {e}. Will try to re-download.")
        sema.release()
        runDownload(threads, url, downloadId)


def runDownload(threads, url, downloadId):
    print("Run download: " + str(url) + " " + str(downloadId))
    thread = threading.Thread(target=downloadFile, args=(url, downloadId))
    threads.append(thread)
    thread.start()



if __name__ == '__main__': 
    #NOTE :: Passing credentials over a command line arguement is not considered secure
    #        and is used only for the purpose of being example - credential parameters
    #        should be gathered in a more secure way for production usage
    #Define the command line arguements
    
    # user input    
    #parser = argparse.ArgumentParser()
    #parser.add_argument('-u', '--username', required=True, help='Username')
    #parser.add_argument('-p', '--password', required=True, help='Password')
    
    #args = parser.parse_args()
    
    #username = args.username
    #password = args.password     

    print("\nRunning Scripts...\n")
    
    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"
    
    # login
    payload = {'username' : username, 'password' : password}
    
    apiKey = sendRequest(serviceUrl + "login", payload)
        
    datasetName = "eviirs_ndvi" 

    spatialFilter =  {'filterType' : "mbr",
                      'lowerLeft' : {'latitude' : 39.6175, 'longitude' : -105.1057},
                      'upperRight' : { 'latitude' : 39.9110, 'longitude' : -104.6222}}
                     
    temporalFilter = {'start' : '2023-01-01', 'end' : '2023-12-03'}
    
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
        
        acquisitionFilter = {"end": "2023-12-03",
                             "start": "2023-01-01" }        
            
        payload = {'datasetName' : dataset['datasetAlias'], 
                                 'maxResults' : 100,
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
                label = "20231203_180000" #datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Customized label using date time
                payload = {'downloads' : downloads, 'label' : label}
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
                            runDownload(threads, download['url'],  download['downloadId'])
                        
                    for download in moreDownloadUrls['requested']:
                        if str(download['downloadId']) in requestResults['newRecords'] or str(download['downloadId']) in requestResults['duplicateProducts']:
                            downloadIds.append(download['downloadId'])
                            print("DOWNLOAD: " + download['url'])
                            runDownload(threads, download['url'],  download['downloadId'])
                     
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
                                print("Try DOWNLOAD...: " + download['url'])
                                runDownload(threads, download['url'],  download['downloadId'])
                            else:
                                pass

                else:
                    # Get all available downloads
                    for download in requestResults['availableDownloads']:
                        # TODO :: Implement a downloading routine
                        print("DOWNLOAD (to do): " + download['url'])
                        
                print("\nAll downloads are available to download.\n")
        else:
            print("Search found no results.\n")
                
    # Logout so the API Key cannot be used anymore
    endpoint = "logout"  
    if sendRequest(serviceUrl + endpoint, None, apiKey) == None:        
        print("Logged Out\n\n")
    else:
        print("Logout Failed\n\n") 


#sendRequest(url, data, apiKey)
downloadFile(url, downloadId)
runDownload(threads, url, downloadId)


