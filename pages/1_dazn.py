import os
import streamlit
 
from lib.dazn import __fst_section
from lib.dazn import __snd_section
from lib.dazn import __trd_section

SERVER = "dazn"

def main():

    FST_CHOICE = "Introduzione"
    SND_CHOICE = "Ricostruzione Flussi"
    TRD_CHOICE = "Profilazione CNAMEs"
    FRT_CHOICE = "Misurazioni"

    # config page
    streamlit.set_page_config(layout="wide")

    with streamlit.sidebar:
        page = streamlit.radio("Seleziona pagina", 
                               options=[FST_CHOICE, SND_CHOICE, 
                                        TRD_CHOICE, FRT_CHOICE])
        
    if page == FST_CHOICE:
        streamlit.html(os.path.join("www", SERVER, "0.html"))
        streamlit.html(os.path.join("www", SERVER, "1.html"))
    if page == SND_CHOICE:
        __fst_section.__render()
    if page == TRD_CHOICE:
        __snd_section.__render()
    if page == FRT_CHOICE:
        __trd_section.__render()
        

    #streamlit.html(os.path.join("www", SERVER, "3.html"))

    # # render the first section
    # __fst_section.__render()

    # # render the second section
    # __snd_secction.__render()

    # render the third section
    # __trd_section.__render()

main()


