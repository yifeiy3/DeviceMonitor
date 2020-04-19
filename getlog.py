from Analysis import Analysis
from datetime import datetime, timedelta
from Rules import Rules

API_KEY = "ff5c476f-1b99-4fc7-a747-0bed31268f11"    #The API Key of the monitor
ENDPOINT = "https://graph.api.smartthings.com/api/smartapps/installations/39077465-2039-4f2b-87d7-07807b0cd548"   #The API endpoint of the monitor
IMPORTANT = ["Door"]  #important devices to keep track of state changes
log_output = 'deviceInfos/alldevicelog.txt' #output folder for analysis of device logs
rule_output = 'deviceInfos/alldevicerule.txt' #output folder for analysis of log according to rules
rule_input = 'rules/rule.txt' #input for our rules
#rule_input = None
since = datetime.utcnow() - timedelta(minutes=110) #check interaction since last hour
print("Analyzing events since")
print(since)
#since = None

An = Analysis(API_KEY, ENDPOINT, important = IMPORTANT)
An.analyze(log_output, since)
if rule_input:
    print("rule file:" + rule_input)
    Ru = Rules(rule_input, An.mevents, An.allevts, An.items)
    Ru.ruleAnalysis(rule_output)

