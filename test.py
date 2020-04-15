import getDeviceInfo as gd
import json

monitorid = "9793402f-fcb7-42af-8461-da541b539f01" #arbitrary id for a device called monitor
stdattrribute = ['healthStatus', 'DeviceWatch-DeviceStatus', 'DeviceWatch-Enroll', 'versionNumber']
APIKey = "ff5c476f-1b99-4fc7-a747-0bed31268f11"
APIEndpt = "https://graph.api.smartthings.com/api/smartapps/installations/6428fa6b-8024-4e7b-8629-3d758a9aa2f2"

md = gd.Monitor(APIKey, APIEndpt)
d_info = md.getThings("all")
m_info = md.getThings("monitor") #example of getting info for one device
    

monitor_states = md.getStates("lastExec", monitorid) #example of getting state transitions of a certain state
monitor_events = md.getEvents(monitorid, 100) #example of getting events for one device

switch_states = md.getStates("switch", "abeafef6-7372-4347-bab6-4f485b8fb2d7")
switch_events = md.getEvents("abeafef6-7372-4347-bab6-4f485b8fb2d7", 5)

curr_mode = md.getHomeMode() #gets current location mode

with open('deviceInfos/alldevicelogtest.txt', 'w') as outfile:
    outfile.write("Current location mode: \n")
    json.dump(curr_mode, outfile)
    outfile.write("All device info: \n")
    json.dump(d_info, outfile)
    outfile.write("\n\nAll devices: \n")
    for items in d_info:
        outfile.write("\t" + items["name"] + ": " + items["id"] + "\n")
    for items in d_info:
        outfile.write("\n" + items["name"] + " Events: \n")
        json.dump(md.getEvents(items["id"], 5), outfile) #get last 5 events
        for it in items["capabilities"]:
            for attr in it["attributes"]:
                if attr not in stdattrribute:
                    outfile.write("\n" + items["name"] + " " + attr + "state: ")
                    json.dump(md.getStates(attr, items["id"]), outfile)
