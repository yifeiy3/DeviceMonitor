import re
from Analysis import Objects
from datetime import datetime, timedelta
from Parse import parse

def timediff(t2, t1):
    '''
        find difference of time, take in special case when within a minute transition
    '''
    if (t1 // 1000) % 100 < 2 and (t2 // 1000) % 100 > 58:
        return 0 #if date is somehting like 23:59:59:000.
    return t1 - t2

def addRule(d, device, attribute, value, confs, time):
    if device in d:
        if attribute in d[device]:
            if value in d[device][attribute]:
                d[device][attribute][value] += (confs, time)
            else:
                d[device][attribute][value] = [(confs, time)]
        else:
            d[device][attribute] = {}
            d[device][attribute][value] = [(confs, time)]
    else:
        d[device] = {}
        d[device][attribute] = {}
        d[device][attribute][value] = [(confs, time)]

def addRuleP(d, device, method, confs, time):
    if device in d:
        if method in d[device]:
            d[device][method] += (confs, time)
        else:
            d[device][method] = [(confs, time)]
    else:
        d[device] = {}
        d[device][method] = [(confs, time)]

def calculateOffset(date, timec, backwards=False):
    '''
        provide a new date res by going backwards or forwards from our date with the
        parameters provided by our time constraint timec. If there are no constraints,
        return False, -1

        Return: (Flag, new date), flag = true iff new date is not -1
    '''
    if not timec:
        return False, -1
    elif date == -1:
        return True, -1
    else:
        amt = int(timec[0])
        unit = timec[1]
        millisec = date % 1000
        dformat = "%Y%m%d%H%M%S"
        d = datetime.strptime(str(date//1000), dformat) #python does not support milliseconds
        if unit == 'SECONDS':
            if backwards:
                newd = d - timedelta(seconds=amt)
            else:
                newd = d + timedelta(seconds=amt)
        elif unit == 'MINUTES':
            if backwards:
                newd = d - timedelta(minutes=amt)
            else:
                newd = d + timedelta(minutes=amt)
        else:
            if backwards:
                newd = d - timedelta(hours=amt)
            else:
                newd = d + timedelta(hours=amt)
        res = int(newd.strftime(dformat)) * 1000 + millisec
        return True, res

class Rules():
    def __init__(self, rules, modes, events, items):
        if not modes:
            print("Mode can not be empty")
        if len(modes) == 1:
            self.mode = (modes[0][1], -1)
        else:
            self.mode = None
        self.deviceState = self._initializeState(items) #dictionary about all the device state that is relevant for our rules.
        self.allEvents = events
        self.rules = rules
        self.dodict = {} #map device to attribute, attribute to value, value to all the conflicts.
        self.dontdict = {}
        self.tempdict = {} #A temporary dictionary used ot help handling dodict business. 
        
    def _initializeState(self, items):
        deviceD = {}
        for key in items:
            obj = items[key]
            deviceD[obj.name] = {}
            for k in obj.states: #list of all attributes for the object
                deviceD[obj.name][k] = None
        return deviceD

    def parseRules(self):
        '''
            parse the rules file as input for us to use. For simplicity of parsing, the format
            of the rules should be of the follows:
                DO/DONT $deviceMethod THE $device AFTER/FOR $duration SECONDS/MINUTES/HOURS 
                WHEN $attribute OF $devicename IS $value FOR/AFTER $duration SECONDS/MINUTES/HOURS AND $attri.....
                DO/DONT $deviceMethod ....  WHEN LOCATION MODE IS $mode
                DO/DONT SET LOCATION MODE TO $mode WHEN ...
            where we use the capital letters to distinguish tokens from names

            Note we can't have DO SOMETHING FOR $duration or DONT DO SOMETHING AFTER $duration
            Since they can be easily converted to other rules by our syntax. For Time duration, the smallest
            unit is seconds, the biggest unit is hours.
        '''
        with open(self.rules, 'r') as rules:
            for lines in rules:
                req, conds = parse(lines)
                (do, method, device) = req[0] #in case for location mode, device = Mode, method = 'location'
                time = req[1]
                if do == "DONT":
                    addRuleP(self.dontdict, device, method, conds, time)
                    print("Rule gets added to DONT dictionary:")
                    print("\tDevice: {0}, Method: {1}, Conditions: {2}".format(device, method, conds))
                    if req[1]:
                        print("\tDuration: {0}, Unit: {1}, Query: {2}".format(time[0], time[1], time[2]))
                    else:
                        print("No time constraint")
                else:
                    addRuleP(self.dodict, device, method, conds, time)
                    print("Rule gets added to Do dictionary")
                    print("\tDevice: {0}, Method: {1}, Conditions: {2}".format(device, method, conds))
                    if req[1]:
                        print("\tDuration: {0}, Unit: {1}, Query: {2}".format(time[0], time[1], time[2]))
                    else:
                        print("No time constraint")
                    for it in conds:
                        a, d, v = it[0]
                        addRule(self.tempdict, d, a, v, ([(method, device)], time), it[1]) #add a reverse dictionary for easy lookup

    def checkValidCond(self, attri, devi, val, flag, tc):
        '''
            return true if condition met, tc is time constraint
        '''
        if flag:
            if devi == "Location":
                return self.mode != None and (val == self.mode[0] and self.mode[1] <= tc) 
                #The state change happens before the time, valid for 'FOR' conditon
            else:
                return (val == self.deviceState[devi][attri][0] and self.deviceState[devi][attri][1] <= tc)
        else:
            if devi == "Location":
                return self.mode != None and (val == self.mode[0])
            else:
                return (val == self.deviceState[devi][attri][0])
    
    def checkWithinTime(self, attri, devi, val, timereq, date, timecond):
        '''
            Perform the same check as check valid condition, but also need to make sure 
            the condition is happening within the given timeframe

            timereq is the time duration constraint for our requirement
            timecond is the time duration constraint for our condition

            return: (All of the condition are satisfied within timeframe, The execution happens within the timeframe 
            for DONT rule specification)
        '''
        if devi == 'Location':
            dstate = self.mode
            lastmod = dstate[1]
        else:
            dstate = self.deviceState[devi][attri]
            lastmod = dstate[1]
        f, offset = calculateOffset(date, timecond, backwards=True) #all the condition are satisfied w.r.t to their durations
        lf, sffset = calculateOffset(lastmod, timecond) #add back the time frame needed for all the conditions
        if lf:
            lastmod = sffset
        nf, noffset = calculateOffset(lastmod, timereq) #the event happened within the time frame for DONT rule
        if nf:
            if f:
                if devi == "Location":
                    return (self.mode != None and (val == self.mode[0] and self.mode[1] <= offset), (date <= noffset))
                else:
                    return ((val == dstate[0] and dstate[1] <= offset), (date <= noffset))
            else:
                return (self.checkValidCond(attri, devi, val, f, offset), (date <= noffset))
        else: #We do not care about execution within a timeframe, set the second parameter to True
            return (self.checkValidCond(attri, devi, val, f, offset), True)

    def isNewStateChange(self, attri, val, device, constraints):
        '''
            Check if any device in the constraint list changes state before our last condition is true
            for the duration amount of time.
        '''
        for stuff, _tc in constraints:
            att, tobj, v = stuff
            if attri == att and tobj == device and v != val:
                return True
        return False

    def checkRules(self):
        '''
            For the devices we could not infer states (The states are set way before and we can not obtain log),
            we assume such device conditions do not violate any rules.
        '''
        dontVio = [] #violation for don't rules
        doVio = [] #violation for do rules
        for i in range(len(self.allEvents)):
            date, cmd, name, st, val, tobj = self.allEvents[i]
            if cmd == 'DEVICE' or cmd == 'LOCATION_MODE': #location mode need to account for both
                if cmd == 'LOCATION_MODE':
                    self.mode = (val, date)
                else:
                    self.deviceState[tobj][st] = (val, date) #add the date field to calculate the time offset
                try: 
                    #a device changed state, check if any do rule conditions are satisfied
                    coreq = self.tempdict[tobj][st][val]
                except:
                    continue
                else:
                    for confs, times in coreq:
                        for method, de in confs[0]:
                            try:
                                docond = self.dodict[de][method]
                            except:
                                continue
                            else:
                                for ittt in docond:
                                    flag = True
                                    theconstraints = ittt[0]
                                    timess = ittt[1]
                                    for things in theconstraints:
                                        a, d, v = things[0]
                                        if a == st and d == tobj and v == val:
                                            continue #we know this is already satisfied.
                                        timecons = things[1]
                                        f, doff = calculateOffset(date, timecons, backwards=True) #(whether we have time constraint, the offset)
                                        flag = flag and self.checkValidCond(a, d, v, f, doff)
                                    if flag: 
                                        #all conditions for the do rule is satisfied
                                        #need to check if do rule is executed within a very brief time frame.
                                        j = i+1
                                        changed = False
                                        _t, dateoffset = calculateOffset(date, timess) #convert time input to the correct seconds offset
                                        stt, changeoffset = calculateOffset(date, times) #the period we need to wait for the condition to be valid

                                        while(j < len(self.allEvents) and 
                                            (timediff(self.allEvents[j][0], dateoffset) > 0 or timediff(dateoffset, self.allEvents[j][0]) < 2000)): 
                                            #events happened after, but within 2 second after the offset time defined by the rules
                                            _date, _cmd, _name, thest, theval, theobj = self.allEvents[j]
                                            if theval == method and theobj == de: #we did change this device accordingly
                                                changed = True
                                                break
                                            #The condition is changed before our current condition is valid for the duration of time, we 
                                            #do not have our rule condition satisfied anymore.
                                            if stt and self.allEvents[j][0] < changeoffset and self.isNewStateChange(thest, theval, theobj, theconstraints):
                                                changed = True
                                                break                                    
                                            j = j+1
                                        if not changed:
                                            doVio.append((method, de, docond, timess))

            if cmd == 'APP_COMMAND' or cmd == 'LOCATION_MODE':
                try:
                    conffs = self.dontdict[tobj][val]
                except: #There is no rule about this event
                    continue
                else:
                    flagp = True
                    anyp = False
                    for con, ttcons in conffs:
                        for itemms in con:
                            att, de, va = itemms[0]
                            timecons = itemms[1]
                            fp, ap = self.checkWithinTime(att, de, va, ttcons, date, timecons)
                            flagp = fp and flagp #the excution meets all the conditions for DONT
                            anyp = ap or anyp #the execution is within the time frame for required
                        if flagp and anyp:
                            if name:
                                dontVio.append((name, tobj, val, conffs, ttcons))
                                #(appname that violated the rule, attributeState, device, value, description of the rule)
                            else:
                                dontVio.append(("LocationMode", tobj, val, conffs, ttcons))
        return dontVio, doVio

    def ruleAnalysis(self, outfile):
        '''
            run analysis on rules, result specified in outfile.
        '''
        self.parseRules()
        dont, do = self.checkRules()
        with open(outfile, 'w') as out:
            out.write("All the DONT rules that are violated: \n")
            for i in range(len(dont)):
                nm, ob, val, confs, timecons = dont[i]
                if nm == "LocationMode":
                    out.write("\t" + str(i+1) + ". Changing location mode to: " + val)
                else:
                    out.write("\t" + str(i+1) + ". App: " + nm + " calls " + val + " method on " + ob)
                if timecons:
                    out.write(" " + timecons[2] + " " + timecons[0] + " " + timecons[1] + "\n")
                out.write("\tUnder the condition of: \n")
                for j in range(len(confs)):
                    condds, _time = confs[j]
                    for k in range(len(condds)):
                        att, de, va = condds[k][0]
                        timeccs = condds[k][1]
                        if att == "mode":
                            out.write("\t\tThe location mode is: " + va)
                        else:
                            out.write("\t\tThe attribute " + att + " for " + de + " is " + va)
                        if timeccs:
                            out.write(" for " + timeccs[0] + " " + timeccs[1] + "\n")
                        else:
                            out.write("\n")
            out.write("All the DO rules that are violated: \n")
            for i in range(len(do)):
                method, de, docond, timecons = do[i]
                if de == "Location":
                    out.write("\t" + str(i+1) + ". Not Changing location mode to: " + method)
                else:
                    out.write("\t" + str(i+1) + ". Not calling method: " + method + " on device " + de)
                if timecons:
                    out.write(" " + timecons[2] + " " + timecons[0] + " " + timecons[1] + "\n")
                out.write("\tUnder the condition of: \n")
                for j in range(len(docond)):
                    condds, _time = docond[j]
                    for k in range(len(condds)):
                        att, de, va = condds[k][0]
                        timeccs = condds[k][1]
                        if att == "mode":
                            out.write("\t\tThe location mode is: " + va)
                        else:
                            out.write("\t\tThe attribute " + att + " for " + de + " is " + va)
                        if timeccs:
                            out.write(" for " + timeccs[0] + " " + timeccs[1] + "\n")
                        else:
                            out.write("\n")
                    
