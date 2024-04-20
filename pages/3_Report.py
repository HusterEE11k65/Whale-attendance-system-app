import streamlit as st
from Home import face_rec
import pandas as pd
#st.set_page_config(page_title='Reporting',layout='wide')
st.subheader('Reporting')

# Retrive logs data and show in report.py
name = 'Whale_attendance:logs'
def load_logs(name,end=-1):
    logs_list = face_rec.r.lrange(name,start=0,end=end)
    return logs_list
tab1,tab2,tab3 = st.tabs(['Registered Data','Logs','Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        with st.spinner('Retriving data....'):
            redis_face_db = face_rec.retrive_data(name = 'Whale:Register')
            st.dataframe(redis_face_db[['Name','UserID']])
with tab2:    
    if st.button('Refresh Logs'):
        st.write(load_logs(name=name))
with tab3:
    logs_list = load_logs(name=name)
    convert_byte_to_string = lambda x: x.decode('utf-8')
    logs_list_string = list(map(convert_byte_to_string,logs_list))
    split_string = lambda x: x.split('@')
    logs_nested_list = list(map(split_string,logs_list_string))
    logs_df = pd.DataFrame(logs_nested_list,columns=['Name','UserID','Timestamp'])
    logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'])
    logs_df['Date'] = logs_df['Timestamp'].dt.date
    report_df = logs_df.groupby(by=['Date','Name','UserID']).agg(
        In_time = pd.NamedAgg('Timestamp','min'),
        Out_time = pd.NamedAgg('Timestamp','max')
    ).reset_index()
    report_df['In_time'] = pd.to_datetime(report_df['In_time'])
    report_df['Out_time'] = pd.to_datetime(report_df['Out_time'])
    report_df['Worked_time'] = report_df['Out_time']-report_df['In_time']
    all_dates = report_df['Date'].unique()
    name_userid = report_df[['Name','UserID']].drop_duplicates().values.tolist()
    date_name_userid_zip = []
    for date in all_dates:
        for name, userid in name_userid:
            date_name_userid_zip.append([date,name,userid])
    date_name_userid_zip_df = pd.DataFrame(date_name_userid_zip,columns=['Date','Name','UserID'])
    date_name_userid_zip_df = pd.merge(date_name_userid_zip_df,report_df,how='left',on=['Date','Name','UserID'])
    date_name_userid_zip_df['Worked_hours'] = date_name_userid_zip_df['Worked_time'].dt.seconds/(60*60)
    def status_marker(x):
        if pd.Series(x).isnull().all():
            return 'Not work'
        elif x>=0 and x<3:
            return 'Not work'
        elif x>=3 and x<4:
            return 'A half-day work'
        elif x>=4 and x<6:
            return 'A half-day work'
        elif x>=6 and x<23:
            return 'A full-day work'
        else:
            return 'Not work'
    date_name_userid_zip_df['Status'] = date_name_userid_zip_df['Worked_hours'].apply(status_marker)
    st.write(date_name_userid_zip_df)