import os
import streamlit as st

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# HTMLS = os.path.join(os.path.dirname(__file__), "htmls")
# st.set_page_config(layout="wide")
# st.html(os.path.join(HTMLS, "intro.html"))