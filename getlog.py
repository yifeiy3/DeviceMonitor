from Analysis import Analysis
from datetime import datetime, timedelta

API_KEY = "ff5c476f-1b99-4fc7-a747-0bed31268f11"    #The API Key of the monitor
ENDPOINT = "https://graph.api.smartthings.com/api/smartapps/installations/6428fa6b-8024-4e7b-8629-3d758a9aa2f2"   #The API endpoint of the monitor
IMPORTANT = ["Door"]  #important devices to keep track of state changes
output = 'deviceInfos/alldevicelog.txt' #output folder
since = datetime.utcnow() - timedelta(minutes=110) #check interaction since last hour
print(since)
#since = None

An = Analysis(API_KEY, ENDPOINT, important = IMPORTANT)
An.analyze(output, since)

