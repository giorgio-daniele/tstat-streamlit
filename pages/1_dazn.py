import os
import streamlit
 
from lib.dazn import __fst_section
from lib.dazn import __snd_secction
from lib.dazn import __trd_section

SERVER = "dazn"

def main():

    # config page
    streamlit.set_page_config(layout="wide")

    streamlit.markdown(
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

    streamlit.html(os.path.join("www", SERVER, "3.html"))

    # render the first section
    __fst_section.__render()

    # render the second section
    __snd_secction.__render()

    # render the third section
    __trd_section.__render()

main()


