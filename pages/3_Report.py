import streamlit as st
from Home import face_rec
#st.set_page_config(page_title='Reporting',layout='wide')
st.subheader('Reporting')

# Retrive logs data and show in report.py
name = 'Whale_attendance:logs'
def load_logs(name,end=-1):
    logs_list = face_rec.r.lrange(name,start=0,end=end)
    return logs_list
tab1,tab2 = st.tabs(['Registered Data','Logs'])

with tab1:
    if st.button('Refresh Data'):
        with st.spinner('Retriving data....'):
            redis_face_db = face_rec.retrive_data(name = 'Whale:Register')
            st.dataframe(redis_face_db[['Name','UserID']])
with tab2:    
    if st.button('Refresh Logs'):
        st.write(load_logs(name=name))
