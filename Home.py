import streamlit as st
st.set_page_config(page_title='Attendance System',layout = 'wide')
st.header('Whale Company ')
with st.spinner("Loading....."):
    import face_rec
st.success('Loaded successfully')