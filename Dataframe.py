
import pandas as pd
import random
import numpy as np

dict = [{"id":"A","type":"digits",'status_list':[1,2,3,4,5,6]},
        {"id":"B","type":"switch",'status_list':["ON","OFF"]},
        {"id":"C","type":"digits",'status_list':[1,2,3,4,5,6]}]



def genData(devices):

    ids1 = []
    ids2 = []
    for item in devices:
        if item['type'] == "strings":
            ids1.append((item['id'], item['stateName']))
        else:
            ids2.append((item['id'], item['stateName']))
    ids1=list(set(ids1))
    ids2=list(set(ids2))
    ids = ids2+ids1

    device_ids = [x for x in ids]
    columes = ["time"]#+device_ids
    device_status=[x[0]+"_"+x[1] for x in device_ids]
    columes += device_status
    df = pd.DataFrame(columns=columes)  
    unavalible_data = np.empty((1+len(ids),))
    unavalible_data[:] = np.NaN
 
    time = 1000
    while time < 5000:
        for item_dct in devices:
            newtm = time + random.random()*500

            tempdf = pd.DataFrame([unavalible_data],columns=columes)
            tempdf['time']=newtm

            rand_status = random.choice(item_dct['status_list'])
            tempdf[item_dct['id']+'_'+item_dct['stateName']] = rand_status
            df = df.append(tempdf)
        time +=1000
    df.sort_values(by=['time'],inplace=True)
    #df_switch.sort_values(by=['time'],inplace=True)
    #df['A_status'] = df['A_status'].interpolate()

    print(df)  
    df=df.interpolate(method ='linear').ffill().bfill()
    x_val = np.linspace(1000,int(max(df['time'])/1000+1)*1000,int(np.floor(max(df['time'])/1000))+1)
    
    df = df.set_index('time')

    
    df = df.reindex(index=x_val,method='bfill').ffill()
    print(df.loc[1000])

    return df
        
#genData(dict)   







