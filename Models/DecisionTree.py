import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
from sklearn.preprocessing import OneHotEncoder
from sklearn import tree

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

def aggregate(ar, heads, timeperiod):
    '''
        timeperiod: #seconds
        aggregate data based on the time period, every 1 second/5second etc
    '''
    #data process to list of lists
    record = []
    #zip current state and the state after time period to see change relations.
    for i in range(0, ar.shape[0] - timeperiod):
        record.append(
            [str(heads[j]) + "_" + processState(ar[i, j], ar[i+timeperiod, j]) for j in range(ar.shape[1])])
    return record

def genlabel(col):
    '''
        col is a list of label classes, convert them to int
    '''
    total_class = list(set(col))
    res_label = []
    for items in col:
        for j in range(len(total_class)):
            if items == total_class[j]:
                res_label.append(j)
                break
    return res_label, total_class

def data_process(header, store_data, timeperiod):
    rec = aggregate(store_data, header, timeperiod)
    class_dict = {}
    for i in range(len(header)):
        try:
            int(ar[1][i])
        except ValueError: #if our data not integer valued, we train a tree on it
            train_data = []
            train_label = []
            for rows in range(len(rec)):
                data_row = []
                for cols in range(len(rec[0])):
                    if cols != i:
                        data_row.append(rec[rows][cols])
                    else:
                        train_label.append(rec[rows][cols])
                train_data.append(data_row)
            y, class_label = genlabel(train_label)
            enc = OneHotEncoder(handle_unknown='ignore')
            trans_res = enc.fit_transform(train_data).toarray()
            class_dict[header[i]] = (trans_res, y, enc, class_label)
    return class_dict

def train_tree(class_dict):
    tree_dict = {}
    for data_header in tree_dict.keys():
        trans_res, y, enc, class_label = class_dict[data_header]
        clf = tree.DecisionTreeClassifier(max_depth=5)
        clf = clf.fit(trans_res, y)
        treemodels[data_header] = clf
        feature_names = enc.get_feature_names()
        tree.plot_tree(clf, feature_names = feature_names, class_names= class_label)
        plt.show()
    return tree_dict

store_data = pd.read_csv("event.csv", index_col=0)
ar = store_data.to_numpy()
#do a decision tree for each class? we only care about discrete variables for now
heads = list(store_data.columns.values)
cd = data_process(heads, ar, 1)
treemodels = train_tree(cd)