import streamlit as st
from config import *

def envlogger_section():
  st.markdown("""
  <div style="line-height:1.3;">
  <ol>
  <li>Open the files from the EnvLogger app</li>
  <li>Open the folder for the sampling day</li>
  <li>Select the file</li>
  <li>Save the file to your mobile phone in the folder you have selected</li>
  <li>Upload the data file (as you downloaded it, without making any changes) to the form from the folder on your mobile phone</li>
  </ol>
  </div>
  """, unsafe_allow_html=True)
  st.image(ENVLOGGER_IMAGE_PATH)