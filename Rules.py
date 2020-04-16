import re
from Analysis import Objects

def parse(rulestr):
    '''
        Simple parser based on the rule syntax.
    '''
    try:
        req, cond = rulestr.split(' WHEN ')
        conditions = cond.split(' AND ')
        require = parsereq(req)
        conf = []
        for items in conditions:
            attr, device, value = parsecond(items)
            conf.append((attr, device, value))
        return require, conf
    except:
        print("Parse Error for rule string: " + rulestr)
        return None, []

def parsereq(req):
    try:
        do, attr, device, value = re.findall(r'(^.*)(?= SET )|((?<= SET ).*)(?= OF )|((?<= OF ).*)(?= TO )|((?<= TO ).*)', req)
        return (do[0], attr[1], device[2], value[3])
    except:
        do, mode = re.findall(r'(^.*)(?= SET LOCATION MODE TO )|((?<= SET LOCATION MODE TO ).*)', req)
        return (do[0], "mode", "Location" , mode[1])

def parsecond(cond):
    try:
        attr, device, value = re.findall(r'(^.*)(?= OF )|((?<= OF ).*)(?= IS )|((?<= IS ).*)', cond)
        return (attr[0], device[1], value[2])
    except:
        mode = re.findall(r'(?=LOCATION MODE IS )|((?<=LOCATION MODE IS ).*)', cond)
        return ("mode", "Location", mode[0])

def addRule(d, device, attribute, value, confs):
        if device in d:
            if attribute in d[device]:
                if value in d[device][attribute]:
                    d[device][attribute][value] += confs
                else:
                    d[device][attribute][value] = confs
            else:
                d[device][attribute] = {}
                d[device][attribute][value] = confs
        else:
            d[device] = {}
            d[device][attribute] = {}
            d[device][attribute][value] = confs

class Rules():
    def __init__(self, rules, modes, events, items):
        if not modes:
            print("Mode can not be empty")
        if len(modes) == 1:
            self.mode = modes[1]
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
                DO/DONT SET $attribute OF $devicename TO $value WHEN $attribute OF $devicename IS $value AND $attri.....
                DO/DONT SET $attribute ....  WHEN LOCATION MODE IS $mode
                DO/DONT SET LOCATION MODE TO $mode WHEN ...
            where we use the capital letters to distinguish tokens from names
        '''
        with open(self.rules, 'r') as rules:
            for lines in rules:
                req, conds = parse(lines)
                do, attr, device, val = req
                if do == "DONT":
                    addRule(self.dontdict, device, attr, val, conds)
                else:
                    addRule(self.dodict, device, attr, val, conds)
                    for a, d, v in conds:
                        addRule(self.tempdict, d, a, v, [(attr, device, val)]) #add a reverse dictionary for easy lookup

    
    def checkValidCond(self, attri, devi, val):
        '''
            return true if condition met 
        '''
        if devi == "Location":
            return (val == self.mode)
        else:
            return (val == self.deviceState[devi][attri])
    
    def checkRules(self):
        '''
            For the devices we could not infer states (The states are set way before and we can not obtain log),
            we assume such device conditions do not violate any rules.
        '''
        dontVio = [] #violation for don't rules
        doVio = [] #violation for do rules
        for i in range(len(self.allEvents)):
            date, cmd, name, st, val, tobj = self.allEvents[i]
            if cmd == 'DEVICE':
                self.deviceState[tobj][st] = val
                try: #a device changed state, check if any do rule conditions are satisfied
                    coreq = self.tempdict[tobj][st][val]
                    for att, de, va in coreq:
                        docond = self.dodict[de][att][va]
                        flag = True
                        for a, d, v in docond:
                            flag = flag and self.checkValidCond(a, d, v)
                        if flag and not self.checkValidCond(att, de, va): 
                            #all conditions for the do rule is satisfied and our rule is still not satisfied
                            #need to check if do rule is executed within a very brief time frame.
                            j = i+1
                            changed = False
                            while(j < len(self.allEvents) and self.allEvents[j][0] < date + 1500): #events happened within 1.5 second
                                _date, _cmd, _name, thest, theval, theobj = self.allEvents[j]
                                if thest == att and theval == va and theobj == de: #we did change this device accordingly
                                    changed = True
                                    break
                                j = j+1
                            if not changed:
                                doVio.append((name, tobj, st, val, coreq))
                except:
                    continue
            else:
                try:
                    confs = self.dontdict[tobj][st][val]
                    flag = True
                    for att, de, va in confs:
                        flag = flag and self.checkValidCond(att, de, va)
                    if flag:
                        if name:
                            dontVio.append((name, tobj, st, val, confs)) 
                            #(appname that violated the rule, attributeState, device, value, description of the rule)
                        else:
                            dontVio.append(("LocationMode", tobj, st, val, confs))
                except: #There is no rule about this event
                    continue
        return dontVio, doVio

    def ruleAnalysis(self, outfile):
        '''
            run analysis on rules, result specified in outfile.
        '''
        self.parseRules()
        do, dont = self.checkRules()
        with open(outfile, 'w') as out:
            out.write("All the DONT rules that are violated: \n")
            for i in range(len(dont)):
                nm, ob, st, val, confs = dont[i]
                if nm == "LocationMode":
                    out.write("\t" + str(i+1) + ". Changing location mode to: " + val + "\n")
                else:
                    out.write("\t" + str(i+1) + ". App: " + nm + "changed state " + st + " of device " + ob + " to " + val + "\n")
                out.write("\t Under the condition of: \n")
                for j in range(len(confs)):
                    att, de, va = confs[i]
                    if att == "mode":
                        out.write("\t\t The location mode is: " + va + "\n")
                    else:
                        out.write("\t\tThe attribute " + att + " for " + de + " is " + va + "\n")
            out.write("All the DO rules that are violated: \n")
            for i in range(len(do)):
                nm, ob, st, val, confs = do[i]
                if not nm:
                    out.write("\t" + str(i+1) + ". Not Changing location mode to: " + val + "\n")
                else:
                    out.write("\t" + str(i+1) + ". Not Changing state: " + st + " of device " + ob + " to " + val + "\n")
                out.write("\t Under the condition of: \n")
                for j in range(len(confs)):
                    att, de, va = confs[i]
                    if att == "mode":
                        out.write("\t\t The location mode is: " + va + "\n")
                    else:
                        out.write("\t\tThe attribute " + att + " for " + de + " is " + va + "\n")
                
