# This file used to generate data for inferring rules.
# Sample data is generated with Date | Time | Device | State

from Analysis import Analysis
from datetime import datetime, timedelta
from Rules import Rules
from Dataframe import genData

def checkfloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def checkint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

API_KEY = "ff5c476f-1b99-4fc7-a747-0bed31268f11"    #The API Key of the monitor
ENDPOINT = "https://graph.api.smartthings.com/api/smartapps/installations/07043c3c-81c3-488f-9b6b-5c085f559432"   #The API endpoint of the monitor
IMPORTANT = ["Door"]  #important devices to keep track of state changes
log_output = 'deviceInfos/alldevicelog.txt' #output folder for analysis of device logs
rule_output = 'deviceInfos/alldevicerule.txt' #output folder for analysis of log according to rules
rule_input = 'rules/rule.txt' #input for our rules
#rule_input = None
#since = datetime.utcnow() - timedelta(minutes=110) #check interaction since last hour
print("Analyzing events since")
since = None
if not since:
    print(datetime.utcnow() - timedelta(days = 7))
else:
    print(since)

An = Analysis(API_KEY, ENDPOINT, important = IMPORTANT)
An.analyze(log_output, since, debug=True)
if rule_input:
    print("rule file:" + rule_input)
    Ru = Rules(rule_input, An.mevents, An.allevts, An.items)

homeDevices = An.items.keys() #all the devices in the house
devicelist = []
for devices in homeDevices:
    devObj = An.items[devices]
    print(devObj.states)
    for statenames in devObj.states:
        possiblestates = list(set([x for (date, x) in devObj.states[statenames]]))
        if possiblestates and len(possiblestates) > 1: #ignore the nonchanging states now, too many states for thermostat
            typ = "strings"
            if checkfloat(possiblestates[0]):
                typ = "digits"
                possiblestates = [float(x) for x in possiblestates]
            if checkint(possiblestates[0]):
                typ = "digits"
                possiblestates = [int(x) for x in possiblestates]
            devdict = {"id": devObj.name, "stateName": statenames, "type": typ, "status_list": possiblestates}
            devicelist.append(devdict)
print(devicelist)
genData(devicelist)
rulesgen = []
