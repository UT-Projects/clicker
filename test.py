import requests
import json

payload = {'status':True}

r = requests.post(url="http://localhost:5000/poll", verify=False, data=payload)
print(r.json())