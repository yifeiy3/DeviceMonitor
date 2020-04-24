import re

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
        if(res[0] == 'DO'):
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