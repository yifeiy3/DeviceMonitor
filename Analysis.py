import json
import re
import getDeviceInfo as gd

def getJsonState(jsondata):
    '''
        obtain all the interaction from jsondata of monitor
    '''
    actions = []
    for v in jsondata:
        actions.append((v["date"], v["value"]))
    actions.reverse()
    return actions

def isCloseProximity(date, last):
    #typical date input : 2020-03-06T16:30:43Z
    if not last: 
        return False
    times = date[:-3] 
    seconds = date[-3:][:-1]
    ltime = last[:-3]
    lseconds = last[-3:][:-1]
    if(times != ltime):
        return False #different dates
    else:
        return int(seconds) - int(lseconds) < 5 #data happens within 5 seconds
    
class Objects():
    def __init__(self, objid, objname, objstates, evtstates):
        self.id = ""
        self.name = ""
        self.states = objstates
        self.events = evtstates
        self.monitorState = {} #states that can be inferred from monitor data

    def checksum(self):
        '''
            check for difference in length of monitorstate and states.
            check for if any state entry is different between monitor inferred state and actual states
            return the name of state that has differences
        '''
        diff = []
        for items in self.monitorState:
            if(len(self.monitorState[items]) != len(self.states[items])):
                diff.append(items)
                continue
            leng = len(self.monitorState[items])
            for i in range(leng):
                iid, mdate, appname, mvalue = self.monitorState[items][i]
                ddate, dvalue = self.states[items][i]
                if dvalue != mvalue:
                    diff.append(items)
                    break
        return diff

    def findConflict(self):
        '''
            check for direct conflict among the smartapp interactions
        '''
        conflicts = {}
        for items in self.monitorState:
            lastEvt = None
            lastEvtTime = None
            for i in range(len(self.monitorState[items])):
                iid, date, appname, value = self.monitorState[items][i]
                if isCloseProximity(date, lastEvtTime):
                    if conflicts[lastEvt]:
                        conflicts[lastEvt].append(iid)
                    else:
                        conflicts[lastEvt] = [iid]
                lastEvt = iid
                lastEvtTime = date
        return conflicts

    def changeMState(self, state, monitorState):
        if state in self.monitorState:
            self.monitorState[state].append(monitorState)
        else:
            self.monitorState[state] = [monitorState]
    

class Analysis():
    def __init__(self, tkey, tendpoint, important = None):
        self.mr = gd.Monitor(tkey, tendpoint) #monitor
        self.items = {}
        self.mstate = [] #monitor states
        self.important = important #important devices that we need to track for undesired behaviors
        #TODO: do we need to keep track of the important devices in dynamic checking?

    def _loadItems(self, jsondata, since=None):
        for it in jsondata:
            if(it["name"] == "Monitor Device"):
                self.mstate = getJsonState(self.mr.getStates("lastExec", it["id"], since))
                continue
            itemid = it["id"]
            attributes = {}
            for caps in it["capabilities"]:
                for c in caps["attributes"]:
                    attributes[c] = getJsonState(self.mr.getStates(c, itemid, since))
            evts = self.mr.getEvents(itemid)
            itt = Objects(itemid, it["name"], attributes, evts)
            self.items[it["name"]] = itt

    def _loadMonitorState(self):
        '''
            format of the monitor state:
                AppName: $app ($Device1 $DeviceState : $StateDescription, $Device2....)
            return places where important devices has states that is being changed
        '''
        impChange = {}
        for i, info in enumerate(self.mstate): #add enum to identify the events
            date, desc = info
            t = re.search(r'AppName:\s*([^\,]+),\s*\(([^\)]+)\)', desc)
            print(desc)
            if not t:
                continue
            appName, device = t.groups()
            devicelist = device.split(",")
            for d in devicelist:
                print(d)
                t2 = re.search(r'\[\s*([^\]]+)\]\s([^\s]+)\s*\:\s*([^\s]+)', d)
                if not t:
                    continue
                name, state, condition = t2.groups()
                self.items[name].changeMState(state, (i, date, appName, condition))
                    #(index for the change in monitor, the state being changed, (time of change, app of change, value for state changed to))
                if name in self.important:
                    if name in impChange:
                        impChange[name].append((state,i))
                    else:
                        impChange[name] = [(state, i)]
        return impChange
                
    def findIndirect(self):
        '''
            find the indirect conflicts such as issuing both AC and Heater on
        '''
        #TODO: Find a way to analyze potential indirect interactions between smartapps
        return 1 
    
    # def obtainApp(self, index):
    #     theitem = self.mstate[index][1]
    #     desc = theitem["value"]
    #     return (re.search(r'AppName:\s*([^\,]+),\s*\[([^\]]+)\]', desc).groups())[0]

    def _union_find(self, edges):
        '''
            use unionfind or dfs to conflicting apps together.
        '''
        visited = {}
        result = []
        for keys in edges:
            if(visited[keys]):
                continue
            component = [self.mstate[keys]["value"]]
            while (visited[keys] and edges[keys] != None):
                component.append(self.mstate[edges[keys]]["value"])
                keys = edges[keys]
            result.append(component)
        return result

    def analyze_direct(self):
        '''
            analyze all the direct conflicts among the system from the monitor
            returns a list of components that has the app name and the rule/interaction 
            they have conflicts.
        '''
        dconflicts = {}
        #find all the direct conflicts
        for obj in self.items:
            conf = self.items[obj].findConflict()
            for keys in conf:
                dconflicts[keys] = conf[keys]
        groupings = self._union_find(dconflicts)
        return groupings

    def backTrace(self, index):
        res = []
        start = min(0, index-4)
        for items in self.mstate[start:index+1]:
            res.append(items[1])
        return res

    def analyze(self, outputPath, since = None):
        '''
            checks if there is any unintened behavior of the system by:
                1. finding anomalous interactions if any from monitor
                2. finding direct conflicts between apps from monitor
                3. finding if there is any difference between monitor and actual devices
        '''
        system = self.mr.getThings("all")
        self._loadItems(system, since)
        imp = self._loadMonitorState()

        anomaly = self.findIndirect()

        dirconfApp= self.analyze_direct()

        cdiff = {}
        for obj in self.items:
            diffr = self.items[obj].checksum()
            if diffr:
                cdiff[self.items[obj].name] = diffr

        thechgs = {}
        for chgs in imp:
            for state, index in imp[chgs]:
                if chgs not in thechgs:
                    thechgs[chgs] = [(state, self.backTrace(index))]
                else:
                    thechgs[chgs].append((state, self.backTrace(index)))

        with open(outputPath, 'w') as outfile:
            outfile.write("All direct conflicts from monitor: \n")
            for items in dirconfApp:
                outfile.write(items + "\n")
            outfile.write("All logs for important items being modified: \n")
            for c in thechgs:
                for s, t in thechgs[c]:
                    outfile.write(c + ", state : " + s + ": \n")
                    for it in t:
                        outfile.write("\t" + it + "\n")
            outfile.write("All the discrepancies between monitor and device state: \n")
            for objs in cdiff:
                outfile.write(obj + ": ")
                for states in cdiff[objs]:
                    outfile.write(states) #TODO: Think of a different way to handle discrepancies probably

