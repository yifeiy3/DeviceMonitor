import pandas as pd
import random
import numpy as np
import argparse

dict = [{"id":"A","type":"digits",'status_list':[1.,2.,3.,4.,5.,6.]},
        {"id":"B","type":"switch",'status_list':["ON","OFF"]},
        {"id":"C","type":"switch",'status_list':["ON","OFF"]},
        {"id":"D","type":"digits",'status_list':[10,20,13,24,55,76]}]



def genData(devices):

    ids1 = []
    ids2 = []
    for item in devices:
        if item['type'] == "switch":
            ids1.append(item['id'])
        else:
            ids2.append(item['id'])
    ids1=list(set(ids1))
    ids2=list(set(ids2))
    ids = ids2+ids1


    device_ids = [x for x in ids]
    columes = ["time"]#+device_ids
    device_status=[x+"_status" for x in device_ids]
    columes += device_status
    df = pd.DataFrame(columns=columes)  
    unavalible_data = np.empty((1+len(ids),))
    unavalible_data[:] = np.NaN
 
    time = 1000

    while time <1000*300:
        for item_dct in devices:
            newtm = time + random.random()*500
            
            tempdf = pd.DataFrame([unavalible_data],columns=columes)
            tempdf['time']=newtm

            rand_status = random.choice(item_dct['status_list'])
            tempdf[item_dct['id']+'_status'] = rand_status
            df = df.append(tempdf,ignore_index=True)
        time +=1000
    df.sort_values(by=['time'],inplace=True)

    df = df.interpolate().ffill().bfill()
    x_val = np.linspace(1000,int(max(df['time'])/1000+1)*1000,int(np.floor(max(df['time'])/1000))+1)
    
    df = df.set_index('time')

    
    df = df.reindex(index=x_val,method='bfill').ffill()
    print(df.loc[1000])

    return df
    
        
##################################################################
#       Rule A
#       1, if B ON - then C must be ON
#       2, if B OFF - then C must be OFF in 5 second
#       3, if B change to OFF and C ON, B back to ON within 5s , C doesn't change
##################################################################

def rule_A(df):
    count = 1000
    while count <= df.index.max():
        if count+5000<=df.index.max() and df['B_status'].loc[count] == 'OFF' and df['C_status'].loc[count+5000] == 'ON':
            df['C_status'].loc[count+5000] = 'OFF'
        if df['B_status'].loc[count] == 'ON':
            df['C_status'].loc[count] = 'ON'
        count += 1000
    return df


        
df = genData(dict)
df = rule_A(df)
print(df)   







