import json
import re
import getDeviceInfo as gd

stdattrribute = ['healthStatus', 'DeviceWatch-DeviceStatus', 'DeviceWatch-Enroll', 'versionNumber', 'battery']

def getJsonState(jsondata):
    '''
        obtain all the interaction from jsondata of monitor
    '''
    actions = []
    for v in jsondata:
        actions.append((v["date"], v["value"]))
    return actions

def addOrReplace(cdict, key, val, obj, repeat = False):
    if key in cdict:
        if repeat:
            cdict[key][0].append(val)
        else:
            if val not in cdict[key][0]:
                cdict[key][0].append(val)
    else:
        cdict[key] = ([val], obj)

def isIndirect(obj1, obj2):
    '''
        Checks if two objects are have conflicting descriptions, i.e. one is heater one is AC
    '''
    #TODO: find a metric to determine the indirect relationships
    return False

def isCloseProximity(date, last):
    #typical date input : 2020-03-06T16:30:43Z
    if not last or not date: 
        return False
    times = date[:-3] 
    seconds = date[-3:][:-1]
    ltime = last[:-3]
    lseconds = last[-3:][:-1]
    if(times != ltime):
        return False #different dates
    else:
        return abs(int(seconds) - int(lseconds)) < 2 #data happens within 1 second

class Objects():
    def __init__(self, objid, objname, objstates):
        self.id = objid
        self.name = objname
        self.states = objstates
        self.sysevts = []
        self.appevts = []
        self.sysst = {}
    
    def checksum(self):
        '''
            check if system events has discrepancies of actual device states, this intuitively 
            should always be consistent but check to be sure
        '''
        diff = []
        for items in self.sysevts:
            addOrReplace(self.sysst, items[3], items[4], items[5], repeat = True)
        for keys in self.sysst:
            vals = self.sysst[keys][0]
            gt = self.states[keys] #a list of (date ,state value)
            if(len(vals) != len(gt)):
                diff.append((self.name, keys))
                continue
            for i in range(len(vals)):
                if vals[i] != gt[i][1]:
                    diff.append((self.name, keys))
                    break
        return diff
            
    def findConflict(self):
        '''
            check for direct conflict among the smartapp interactions
        '''
        conflicts = {}
        lastEvtApp = None
        lastEvtTime = None
        for i in range(len(self.appevts)):
            date, cmd, name, st, val, tobj = self.appevts[i]
            if isCloseProximity(date, lastEvtTime):
                addOrReplace(conflicts, lastEvtApp, (name, self.name), self.name)
            lastEvtApp = name
            lastEvtTime = date
        return conflicts

class Analysis():
    def __init__(self, tkey, tendpoint, important = None):
        self.mr = gd.Monitor(tkey, tendpoint)
        self.items = {}
        # self.mstate = []
        self.allevts = []
        self.important = important
    
    def _loadItems(self, jsondata, since=None):
        for it in jsondata:
            # if(it["name"] == "Monitor Device"):
            #     #format of mstate = (date, "Appname")
            #     self.mstate = getJsonState(self.mr.getStates("lastExec", it["id"], since))
            #     continue
            itemid = it["id"]
            attributes = {}
            itt = Objects(itemid, it["name"], attributes)
            self.items[it["name"]] = itt

    def _loadStates(self, tobject, modifiedStates, since=None):
        '''
            only loads in the necessary states that is changed.
        '''
        attributes = {}
        for states in modifiedStates:
            attributes[states] = getJsonState(self.mr.getStates(states, tobject.id, since))
        tobject.states = attributes

    def _loadEvts(self, tobject, jsondata, since=None):
        '''
            load the events for each object from the event log in our monitor
            tobject: the object name we are loading events for

            returns
                sysevts: all the events that changes the state for the object
                appevts: all the events from the apps
                conflicts: all the direct conflicts within the object when loading the evt,
                    happened when new event happened before the state change for previous called 
                    app is processed
        '''
        sysevts = []
        appevts = []
        conflicts = []
        changedStates = []

        prev = ("", "", "", "", "", "")
        obj = self.items[tobject]
        for it in jsondata:
            nme = it["device"]["name"]
            cmdtype = it["source"]["name"]
            date = it["date"]
            if cmdtype == "DEVICE":
                desc = it["desc"] #desc pattern: ($deviceName) ($deviceState) is ($statevalue)
                gp, val = re.findall(r'(^.*)(?=is)|(?<=is)\s+(.*)', desc)
                stval = stval = val[1]
                stname = it["name"]
                if stname in stdattrribute:
                    continue
                if stname not in changedStates:
                    changedStates.append(stname)

                nprev = (date, cmdtype, None, stname, stval, tobject)
                    #(date, commandtype, appname, statebeingchanged, newvalue, objname)

                if prev[1] == 'APP_COMMAND' and isCloseProximity(date, prev[0]):
                    if prev[4] != stval:
                        conflicts.append((prev, nprev))
                prev = nprev
                sysevts.append(nprev)
    
            elif cmdtype == "APP_COMMAND":
                desc = it["desc"] #desc pattern: ($Appname) sent ($command) command to ($device)
                app, cmd, device = re.findall(r'(^.*(?=sent))|((?<=sent).*)(?=command)|((?<=to).*)', desc)
                app = app[0][:-1]
                stval = cmd[1][1:-1]
                prevcmd = prev[1]
                prevst = prev[3]
                preval = prev[4]
                if(isCloseProximity(prev[0], date) and preval != stval):
                    #app command did not immediately cause state of the device change, add to direct conflict
                    theevt = (date, cmdtype, app, None, stval, tobject)
                    conflicts.append((prev, theevt))
                    appevts.append(theevt)
                    prev = theevt
                else:
                    theevt = (date, cmdtype, app, None, stval, tobject)
                    appevts.append(theevt)
                    prev = theevt

            else:
                print("Invalid type: " + cmdtype)
                continue

        obj.sysevts = sysevts
        obj.appevts = appevts
        return sysevts, appevts, conflicts, changedStates
    
    def _dfs(self, edges):
        '''
            edges is a dictionary that maps Appname to (Conflict list, app obj)
            where conflict list is a list of tuple (conflict appname, conflict obj)
            return: group the mappings into components
        '''
        visited = {}
        result = []
        stack = []
        for keys in edges:
            if keys in visited:
                continue
            stack.append(keys)
            component = []
            while(stack):
                temp = stack.pop()
                if temp not in edges:
                    continue
                if not component:
                    component = [(temp, edges[temp][1])] + edges[temp][0]
                else:
                    component = component + edges[temp][0]
                visited[temp] = True
                for i in range(len(edges[keys][0])):
                    if edges[keys][0][i][0] not in visited: #first term always app in conflcit
                        stack.append(edges[keys][0][i][0])
            result.append(component)
        return result

    def analyze_direct(self):
        dconflicts = {}
        #find all the direct conflicts
        for obj in self.items:
            conf = self.items[obj].findConflict()
            for keys in conf:
                dconflicts[keys] = conf[keys]
        groupings = self._dfs(dconflicts)
        return groupings

    def find_conf(self, device, cdict, clist):
        '''
            find all the abnormal direct conflicts from the clist and add it to the dictionary cdict
            we ignore the possible cases where cause by human error of changing the states of objects too often
        '''
        prev = ("", "", "", "", "", "")
        for first, second in clist:
            d1, cmd1, app1, st1, val1, tobj1 = first
            d2, cmd2, app2, st2, val2, tobj2 = second
            #by our construction, cmd2 must be "APP_COMMAND"
            if prev[1] == "APP_COMMAND":
                if cmd1 == "APP_COMMAND":
                    if isCloseProximity(d1, prev[0]):
                        addOrReplace(cdict, prev[2], (app1, device), device)
                    #Two app commands are in conflict, add both
                    if cmd2 == cmd1:
                        addOrReplace(cdict, app1, (app2, device), device)
                    #Otherwise, App command 1 produced an unintended result on the object, must be conflict from app before app command1,
                    #we have already added prev so we already accounted for this. 
                    #Prev can be defined to be first in this case since second is result from prev app
                if cmd2 == "APP_COMMAND": 
                    #the case where cmd1 and cmd2 are in conlfict because of prev, or some app conflicting with prev
                    if isCloseProximity(d2, prev[0]):
                        addOrReplace(cdict, prev[2], (app2, device), device)
                    #this is the case where immediate conflict from cmd1 device state with the app
                    else: 
                        dummyapp = tobj1 + "_state_" + st1 + "_state_" + val1
                        addOrReplace(cdict, dummyapp, (app2, device), device)
                prev = first
            else: 
                if cmd1 == "APP_COMMAND":
                    if isCloseProximity(d1, prev[0]):
                        dummyapp = device + "_state_" + prev[3] + "_state_" + prev[4]
                        addOrReplace(cdict, dummyapp, (app1, device), device)
                    if cmd2 == cmd1:
                        addOrReplace(cdict, app1, (app2, device), device)
                if cmd2 == "APP_COMMAND":
                    if isCloseProximity(d2, prev[0]):
                        dummyapp = device + "_state_" + prev[2] + "_state_" + prev[4]
                        addOrReplace(cdict, dummyapp, (app2, device), device)
                    else:
                        dummyapp = device + "_state_" + st1 + "_state_" + val1
                        addOrReplace(cdict, dummyapp, (app2, device), device)
                prev = first
    
    def _sort_evts(self, evtlist):
        '''
            sort all the events in chronological order
        '''
        #change date to an integer so we can compare
        #TODO: check the correctness of this sorting, gave the wrong order on testing
        for i in range(len(evtlist)):
            date, c1, a1, st1, v1, ob1 = evtlist[i]
            new = int(''.join(c for c in date if c.isdigit()))
            evtlist[i] = (new, c1, a1, st1, v1, ob1)
        l = sorted(evtlist)
        for items in l:
            print(items)
        return l
        
    def _loadallevts(self, since = None, maxEvts = 1000):
        '''
            Load all the events that has happened to the system since Since in a sorted datetime order
            also return if there is any discrepancy between obj state and system events.
        '''
        allevt = []
        bc = {}  #conflict where the transition of state is not in the right order
                 #from apps' direct conflict causing device to change state in short period of time
        diff = []
        for objname in self.items:
            obj = self.items[objname]
            evtjson = self.mr.getEvents(obj.id, since = since, max_evts=maxEvts)
            sys, app, conf, modstates = self._loadEvts(objname, evtjson, since)
            self._loadStates(obj, modstates, since)
            allevt = allevt + sys + app
            self.find_conf(obj.name, bc, conf)
            diff = diff + obj.checksum()

        self.allevts = self._sort_evts(allevt) #sorted events of every thing
        return bc, diff

    def analyze_allevents(self):
        '''
            analyze all the indirect conflicts and the places where important devices gets changed
            in the system from the event log field

            return: (indirect conflicts, places of important change)
        '''
        iconflicts = {}
        imp = []
        prevapp = None
        prevtime = None
        prevobj = None
        for idx, obj in enumerate(self.allevts):
            d, cmd, app, st, val, tobj = obj
            if(cmd == "APP_COMMAND"):
                if(tobj in self.important):
                    imp.append((tobj, idx))
                if isIndirect(tobj, prevobj) and isCloseProximity(d, prevtime):
                    addOrReplace(iconflicts, app, (prevapp, prevobj), tobj)
                        #add(app in conflict, object, object in conflict)
                prevapp = app
                prevtime = d
                prevobj = tobj
        groups = self._dfs(iconflicts)
        return groups, imp
    
    def _backtrace(self, idx):
        '''
            obtain the last 6 events that happenns before the change of important item
        '''
        res = []
        start = max(0, idx-5)
        for i in range(start, idx+1):
            res.append(self.allevts[i])
        return res
   
    def analyze(self, outputPath, since = None, maxe = 1000):

        system = self.mr.getThings("all")
        self._loadItems(system, since)
        bad_conflicts, differ = self._loadallevts(since, maxEvts=maxe)

        d_conflicts = self.analyze_direct() #direct conflicts
        b_conflicts = self._dfs(bad_conflicts)

        i_conflicts, imp = self.analyze_allevents()

        #TODO: Deal with these important changes
        imp_chgs = {}
        for obj, chgs in imp:
            addOrReplace(imp_chgs, obj, self._backtrace(chgs), obj)

        with open(outputPath, 'w') as outfile:
            outfile.write("All direct conflicts from monitor: \n")
            for i in range(len(d_conflicts)):
                outfile.write("\tComponent" + str(i) + "\n")
                for j in range(len(d_conflicts[i])):
                    outfile.write("\t\tApp:" + d_conflicts[i][j][0] + " Device: " + d_conflicts[i][j][1] + "\n")

            outfile.write("All the direct conflicts causes devices to change states abnormally: \n")
            for i in range(len(b_conflicts)):
                outfile.write("\tComponent" + str(i) + "\n")
                for j in range(len(b_conflicts[i])):
                    tp = b_conflicts[i][j][0]
                    if "_state_" in tp:
                        l = tp.split("_state_")
                        outfile.write("\tDevice: " + l[0] + " state: " + l[1] + " value: " + l[2] + "\n")
                    else:
                        outfile.write("\tApp:" + b_conflicts[i][j][0] + " Device: " + b_conflicts[i][j][1] + "\n")

            outfile.write("All the indirect conflicts: \n")
            for i in range(len(i_conflicts)):
                outfile.write("Component\t" + str(i) + "\n")
                for j in range(len(i_conflicts[i])):
                    t = i_conflicts[i][j]
                    outfile.write("\t\tApp:" + t[0] + " Device: " + t[1] + " Conflicted device: " + t[2] + "\n")
            
            outfile.write("All the important device change log: \n")
            for keys in imp_chgs:
                outfile.write('\tObject:' + keys + "\n")
                for i in range(len(imp_chgs[keys][0])):
                    outfile.write('\t\tChange Number: ' + str(i) + '\n')
                    l = imp_chgs[keys][0][i]
                    for tt in l:
                        if(tt[1] == "APP_COMMAND"):
                            outfile.write("\t\t\tApp: " + tt[2] + " changes " + tt[5] + " with " + tt[4] + "command\n")
                        else:
                            outfile.write("\t\t\tDevice: " + tt[5] + "'s " + tt[3] + " state changes to " + tt[4] + "\n")
            if differ:  #This should not happen, for debug purposes.
                outfile.write("Discrepant States: \n")
                for name, state in differ:
                    outfile.write("\tDeviceName: " + name + " Device State: " + state + "\n")
                    obj = self.items[name]
                    for it in obj.states[state]:
                        outfile.write("\t\tState:" + it[1] + "\n")
                    for evt in obj.sysst[state][0]:
                        outfile.write("\t\tEvent:" + evt + "\n")
            


