import re
from Analysis import Objects, isCloseProximity

def parse(rulestr):
    '''
        Simple parser based on the rule syntax.
    '''
    try:
        req, cond = rulestr.split(' WHEN ')
        conditions = cond.split(' AND ')
        require, timer = parsereq(req)
        conf = []
        for items in conditions:
            tconds, timec = parsecond(items)
            conf.append((tconds, timec))
        return (require, timer), conf
    except:
        print("Parse Error for rule string: " + rulestr)
        return None, []

def parsereq(req):
    '''
        parse the requirement rules according to the format.
        AFTER means event DO/DONT happen after some seconds, FOR means event happen for the duration of time
        return (DO/DONT, deviceMethod, device), (Time duration, Time unit, AFTER/FOR)

        Note we can't have DO SOMETHING FOR $duration or DONT DO SOMETHING AFTER $duration
        Since they can be easily converted to other rules by our syntax.
    '''
    try:
        domethod, device = re.findall(r'(^\w*)\s+(.*)(?= THE )|((?<= THE ).*)', req)
        res = (domethod[0], domethod[1], device[2])
    except:
        do, mode = re.findall(r'(^.*)(?= SET LOCATION MODE TO )|((?<= SET LOCATION MODE TO ).*)', req)
        res = (do[0], "Location", mode[1]) 
    tmp = ''
    try:
        if(do[0] == 'DO'):
            dev, rr = res[2].split(' AFTER ')
            res = (res[0], res[1], dev)
            tmp = 'AFTER'
        else:
            dev, rr = res[2].split(' FOR ')
            res = (res[0], res[1], dev)
            tmp = 'FOR'
    except:
        if res[1] == "Location":
            tmpp = res[2]
            res = (do[0], tmpp, "Location")
        return res, None
    else:
        dur, timeMethod = rr.split(' ')
        if res[1] == "Location":
            tmpp = res[2]
            res = (do[0], tmpp, "Location") #switch this back to correct order
        return res, (dur, timeMethod, tmp)

def parsecond(cond):
    '''
        For the conditions, the 'AFTER' key word is meaning less, just need to look out for 'FOR'
        return similar result to parsereq
    '''
    try:
        attr, device, value = re.findall(r'(^.*)(?= OF )|((?<= OF ).*)(?= IS )|((?<= IS ).*)', cond)
        res = (attr[0], device[1], value[2])
    except:
        mode = re.findall(r'(?=LOCATION MODE IS )|((?<=LOCATION MODE IS ).*)', cond)
        res = ("mode", "Location", mode[1])
    try:
        dev, rr = res[2].split(' FOR ')
        res = (res[0], res[1], dev)
    except:
        return res, None
    else:
        dur, timeMethod = rr.split(' ')
        return res, (dur, timeMethod, "FOR")

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
    else:
        return True, 0 #TODO: Implement this!


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
            Since they can be easily converted to other rules by our syntax.
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
                    print("\tDuration: {0}, Unit: {1}, Query: {2}".format(time[0], time[1], time[2]))
                else:
                    addRuleP(self.dodict, device, method, conds, time)
                    print("Rule gets added to Do dictionary")
                    print("\tDevice: {0}, Method: {1}, Conditions: {2}".format(device, method, conds))
                    print("\tDuration: {0}, Unit: {1}, Query: {2}".format(time[0], time[1], time[2]))
                    for it in conds:
                        a, d, v = it[0]
                        addRule(self.tempdict, d, a, v, ([(method, device)], time), it[1]) #add a reverse dictionary for easy lookup

    
    def checkValidCond(self, attri, devi, val, flag, tc):
        '''
            return true if condition met, tc is time constraint
        '''
        if flag:
            if devi == "Location":
                return (val == self.mode[0] and self.mode[1] <= tc) 
                #The state change happens before the time, valid for 'FOR' conditon
            else:
                return (val == self.deviceState[devi][attri][0] and self.deviceState[devi][attri][1] <= tc)
        else:
            if devi == "Location":
                return (val == self.mode[0])
            else:
                return (val == self.deviceState[devi][attri])
    
    def checkWithinTime(self, attri, devi, val, timereq, date, timecond):
        '''
            Perform the same check as check valid condition, but also need to make sure 
            the condition is happening within the given timeframe
        '''
        dstate = self.deviceState[devi][attri]
        lastmod = dstate[1]
        f, offset = calculateOffset(lastmod, timecond, backwards=True)
        nf, noffset = calculateOffset(lastmod, timereq)
        if nf:
            if f:
                if devi == "Location":
                    return (val == self.mode[0] and self.mode[1] <= offset and date <= noffset) 
                else:
                    return (val == dstate[0] and dstate[1] <= offset and date <= noffset)
        else:
            return self.checkValidCond(attri, devi, val, f, offset)

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
                    for confs, times in coreq:
                        for itt in confs:
                            method, de = itt[0]
                            docond = self.dodict[de][method]
                            flag = True
                            for ittt in docond:
                                a, d, v = ittt[0]
                                timecons = ittt[1]
                                f, doff = calculateOffset(date, timecons, backwards=True) #(whether we have time constraint, the offset)
                                flag = flag and self.checkValidCond(a, d, v, f, doff)
                            if flag: 
                                #all conditions for the do rule is satisfied
                                #need to check if do rule is executed within a very brief time frame.
                                j = i+1
                                changed = False
                                dateoffset = calculateOffset(date, times) #convert time input to the correct seconds offset
                                while(j < len(self.allEvents) and 
                                    (self.allEvents[j][0] < dateoffset or isCloseProximity(self.allEvents[j][0], dateoffset))): 
                                    #events happened within 2 second, after the offset time defined by the rules
                                    _date, _cmd, _name, thest, theval, theobj = self.allEvents[j]
                                    if theval == method and theobj == de: #we did change this device accordingly
                                        changed = True
                                        break
                                    j = j+1
                                if not changed:
                                    doVio.append((method, de, docond, times))
                except:
                    continue
            if cmd == 'APP_COMMAND' or cmd == 'LOCATION_MODE':
                try:
                    conffs = self.dontdict[tobj][val]
                    flagp = True
                    for con, ttcons in conffs:
                        for itemms in con:
                            att, de, va = itemms[0]
                            timecons = itemms[1]
                            flagp = flagp and self.checkWithinTime(att, de, va, ttcons, date, timecons)
                        if flagp:
                            if name:
                                dontVio.append((name, tobj, val, confs, ttcons))
                                #(appname that violated the rule, attributeState, device, value, description of the rule)
                            else:
                                dontVio.append(("LocationMode", tobj, val, confs, ttcons))
                except: #There is no rule about this event
                    continue
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
                    condds, timeccs = confs[j]
                    att, de, va = condds
                    if att == "mode":
                        out.write("\t\tThe location mode is: " + va)
                    else:
                        out.write("\t\tThe attribute " + att + " for " + de + " is " + va)
                    if timeccs:
                        out.write(" for" + timeccs[0] + " " + timeccs[1] + "\n")
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
                    condds, timeccs = docond[j]
                    att, de, va = condds
                    if att == "mode":
                        out.write("\t\tThe location mode is: " + va)
                    else:
                        out.write("\t\tThe attribute " + att + " for " + de + " is " + va)
                    if timeccs:
                        out.write(" for" + timeccs[0] + " " + timeccs[1] + "\n")
                
