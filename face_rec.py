import numpy as np
import pandas as pd
import cv2
import redis
import time
from datetime import datetime
#insight face
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise
import os
# Connect to Redis Client
hostname = 'redis-13182.c14.us-east-1-2.ec2.cloud.redislabs.com'
port = 13182
password = 'IHfyLBRNIHakGLvlgGdRmcpkVrZ3pRFx'
r = redis.Redis(
    host=hostname,
    port = port,
    password=password)
# Retrive data from database
def retrive_data(name):

    retrive_dict=r.hgetall(name)
    retrive_series = pd.Series(retrive_dict)
    retrive_series = retrive_series.apply(lambda x : np.frombuffer(x,dtype = np.float32))
    index = retrive_series.index
    index = list(map(lambda x : x.decode(),index))
    retrive_series.index = index
    retrive_df = retrive_series.to_frame().reset_index()
    retrive_df.columns = ['name_userid','facial embedding']
    retrive_df[['Name','UserID']]=retrive_df['name_userid'].apply(lambda x : x.split('@')).apply(pd.Series) 
    return retrive_df[['Name','UserID','facial embedding']]
# configure face analysis
faceapp = FaceAnalysis(name = 'buffalo_sc',
                       root = 'pretrain_model',
                       providers = ['CPUExecutionProvider'])
faceapp.prepare(ctx_id=0, det_size=(640,640), det_thresh =0.5)

# ML Search Algorithm
def ml_search_algorith(dataframe, feature_column, test_vector, name_userid = ['Name','UserID'], thresh =0.5):
    dataframe = dataframe.copy()
    X_list = dataframe[feature_column].tolist()
    x = np.asarray(X_list)
    similar = pairwise.cosine_similarity(x, test_vector.reshape(1,-1))
    similar_arr = np.array(similar).flatten()
    dataframe['cosine']=similar_arr
    data_filter = dataframe.query(f'cosine >= {thresh}')
    if len(data_filter) > 0:
        data_filter.reset_index(drop = True, inplace = True)
        argmax = data_filter['cosine'].argmax()
        name, userid = data_filter.loc[argmax][name_userid]

    else:
        name = 'Unknown'
        userid = 'Unknown'

    return name, userid
class RealTimePred:
    def __init__(self):
        self.logs = dict(name =[],userid=[], current_time=[])
    def reset_dict(self):
        self.logs= dict(name=[],userid=[],current_time=[])
    def saveLogs(self):
        dataframe = pd.DataFrame(self.logs)
        dataframe.drop_duplicates('name',inplace= True)
        name_list = dataframe['name'].tolist()
        userid_list = dataframe['userid'].tolist()
        ctime_list = dataframe['current_time'].tolist()
        encoded_data =[]
        for name,userid,ctime in zip(name_list,userid_list,ctime_list):
            if name != 'Unknown':
                concat_string = f"{name}@{userid}@{ctime}"
                encoded_data.append(concat_string)

        if len(encoded_data)>0:
            r.lpush('Whale_attendance:logs',*encoded_data)

        self.reset_dict()

    def face_prediction(self,test_img,dataframe, feature_column, name_userid = ['Name','UserID'], thresh =0.5):
        current_time = str(datetime.now())
        results = faceapp.get(test_img)
        test_copy = test_img.copy()
        for res in results:
            x1,y1,x2,y2 = res['bbox'].astype(int)
            embeddings = res['embedding']
            name, userid  = ml_search_algorith(dataframe,feature_column,test_vector = embeddings,name_userid = name_userid,thresh = thresh)
            if name == 'Unknown':
                color = (0,0,255)
        
            else:
                color = (0,255,0)
            cv2.rectangle(test_copy, (x1,y1),(x2,y2),color)
            text_gen = userid
            cv2.putText(test_copy,text_gen,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.5,color,1)
            self.logs['name'].append(name)
            self.logs['userid'].append(userid)
            self.logs['current_time'].append(current_time)

        return test_copy
### registration form
class RegistrationForm:
    def __init__(self):
        self.sample=0

    def reset(self):
        self.sample=0
    def get_embeddings(self,frame):
        results = faceapp.get(frame,max_num=1)
        embeddings = None
        for res in results:
            self.sample +=1
            x1,y1,x2,y2 = res['bbox'].astype(int)
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),1)
            text = f"sample = {self.sample}"
            cv2.putText(frame,text,(x1,y1),cv2.FONT_HERSHEY_DUPLEX,0.6,(255,255,0),2)
            embeddings=res['embedding']
        return frame,embeddings
    def save_data(self,name,userid):
        if name is not None:
            if name.strip()!='':
                key=f'{name}@{userid}'
            else:
                return 'name_false'
        else:
            return 'name_false'
        if 'facial_embeddings.txt' not in os.listdir():
            return 'file_false'
        #load "facial_embeddings.txt"
        x_array = np.loadtxt('facial_embeddings.txt',dtype=np.float32)
        #covert into array
        received_samples = int(x_array.size/512)
        x_array = x_array.reshape(received_samples,512)
        x_array = np.asarray(x_array)
        #cal. mean embedding
        x_mean = x_array.mean(axis=0)
        x_mean_bytes = x_mean.tobytes()
        #save in to redis database
        r.hset(name='Whale:Register',key =key, value = x_mean_bytes)
        os.remove('facial_embeddings.txt')
        self.reset()
        return True