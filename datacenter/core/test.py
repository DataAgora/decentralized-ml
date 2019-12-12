import requests
import urllib.request

print('Beginning file download with urllib2...')

url = "http://localhost:8999/model.h5"
urllib.request.urlretrieve(url, 'model.h5')
