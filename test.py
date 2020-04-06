import getDeviceInfo as gd
import json

monitorid = "9793402f-fcb7-42af-8461-da541b539f01"
APIKey = "ff5c476f-1b99-4fc7-a747-0bed31268f11"
APIEndpt = "https://graph.api.smartthings.com/api/smartapps/installations/bb64b684-213a-492e-8138-9b6722e1e9e5"

md = gd.Monitor(APIKey, APIEndpt)
d_info = md.getThings("all")
m_info = md.getThings("monitor")

monitor_states = md.getStates("lastExec", monitorid) #oka is deviceid for monitor
monitor_events = md.getEvents(monitorid, 100)

switch_states = md.getStates("switch", "abeafef6-7372-4347-bab6-4f485b8fb2d7")
switch_events = md.getEvents("abeafef6-7372-4347-bab6-4f485b8fb2d7", 5)

with open('deviceInfos/alldevicelogtest.txt', 'w') as outfile:
    outfile.write("All device info: \n")
    json.dump(d_info, outfile)
    outfile.write("\nMonitor info: \n")
    json.dump(m_info, outfile)
    outfile.write("\nMonitor states: \n")
    json.dump(monitor_states, outfile)
    outfile.write("\nMonitor events: \n")
    json.dump(monitor_events, outfile)
    outfile.write("\nSwitch states: \n")
    json.dump(switch_states, outfile)
    outfile.write("\nSwitch events: \n")
    json.dump(switch_events, outfile)

