import os
import streamlit
 
from lib.dazn import __fst_section
from lib.dazn import __snd_secction
#from lib.dazn import __trd_section

def main():

    # config page
    streamlit.set_page_config(layout="wide")

    # render the first section
    __fst_section.__render()

    # render the second section
    __snd_secction.__render()

    # # render the third section
    # __trd_section.__render()

main()


