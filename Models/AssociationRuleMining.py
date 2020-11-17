from apyori import apriori
import pandas as pd 

def checkint(s):
    try:
        int(s)
        return str(int(s)//5 * 5) #every category separate by a magnitude of 5
    except ValueError:
        return str(s)

def processState(s1, s2):
    ft = checkint(s1)
    sd = checkint(s2)
    if ft == sd:
        return ft + "_" + sd + "_" + "1" #check whether they are equal
    else:
        return ft + "_" + sd + "_" + "0"

def aggregate(df, timeperiod):
    '''
        timeperiod: #seconds
        aggregate data based on the time period, every 1 second/5second etc
    '''
    heads = list(df.columns.values)
    #data process to list of lists
    record = []
    ar = df.to_numpy()
    #zip current state and the state after time period to see change relations.
    for i in range(0, ar.shape[0] - timeperiod):
        record.append(
            [str(heads[j]) + "_" + processState(ar[i, j], ar[i+timeperiod, j]) for j in range(ar.shape[1])])
    #Problem here: what should we do with integer value such as temperature?
    #separate into categories, is there other things with integer than temperature?
    #light intensity, soundlevel, sounds like we can classify by a difference of 5
    return record

store_data = pd.read_csv("event.csv", index_col=0)
print(store_data.head())
rec = aggregate(store_data, 1)
association_rules = apriori(rec, min_support = 0.001, min_confidence=0.85, min_lift=3)
#they should have very high confidence since we want good rules.
association_result = list(association_rules)
print(len(association_result))


nontrivial_rules = []
for items in association_result:
    for ost in items[2]:
        conseq = list(ost[1]) #consequence of relation
        for conseqp in conseq:
            if conseqp[-1:] == '0':
                nontrivial_rules.append(ost) 
                break #we only care about devices change states


#Do this later. first see the output format
with open("AssociationRules.txt", 'w') as ofile:
    for i in range(len(nontrivial_rules)):
        ofile.write(str(i) + ": \n")
        conditions = list(nontrivial_rules[i][0])
        consequences = list(nontrivial_rules[i][1])
        confidence = str(nontrivial_rules[i][2])
        lift = str(nontrivial_rules[i][3])
        ofile.write("\t Conditions: \n")
        for ic in conditions:
            ofile.write("\t\t" + ic + "\n")
        ofile.write("\t Consequence: \n")
        for iq in consequences:
            ofile.write("\t\t" + iq + "\n")
        ofile.write("\t Confidence: " + confidence + " Lift: " + lift + "\n")
        


