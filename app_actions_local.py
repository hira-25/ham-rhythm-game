
import streamlit as st
st.set_page_config(page_title="Ham Rhythm Local", layout="centered")
"""Minimal debug edition – ensures Start works, logs state transitions.
"""
import os
import random
import time
import base64
import uuid
from datetime import date

# ==== Config ====
ASSET_DIR = "assets"
LIVES_MAX = 3
ROUNDS_PER_LEVEL = 3
MAX_LEVEL = 20
BOSS_INTERVAL = 5
BASE_SPEED = 1.5
MIN_SPEED = 0.5
ENABLE_SOUND = True

# ==== Utils ====
def uid() -> str: return uuid.uuid4().hex
def stars(lv:int)->str: return ("★"*max(1,lv//5)).ljust(5,"☆")
def seq_len(lv:int)->int:
    if lv>=19: return 9
    if lv>=15: return 8
    return min(7,2+lv)
def is_boss(lv:int)->bool: return lv%BOSS_INTERVAL==0
def asset(name:str)->str: return os.path.join(ASSET_DIR,name)

def local_audio(path:str):
    if not ENABLE_SOUND or not os.path.isfile(path): return
    with open(path,"rb") as f:
        b64=base64.b64encode(f.read()).decode()
    st.audio(f"data:audio/wav;base64,{b64}",format="audio/wav")

# ==== Assets ====
ACTIONS={
    "起きる / Wake": asset("ham_wake.png"),
    "歩く / Walk": asset("ham_walk.png"),
    "食べる / Eat": asset("ham_eat.png"),
    "寝る / Sleep": asset("ham_sleep.png")
}
CLICK_SOUND   = asset("click.wav")
LEVELUP_SOUND = asset("levelup_fanfare.mp3")

# ==== Session ====
today=date.today().isoformat()
if "init" not in st.session_state:
    st.session_state.update(init=True, level=1, diff=0.0, stage="start",
                            seq=[], guess=[], lives=LIVES_MAX, round=0,
                            best=1, today_best=0, today=today)
if st.session_state.today!=today:
    st.session_state.today=today; st.session_state.today_best=0

# ==== Header ====
st.title("🐹 アクションリズム DEBUG")
c1,c2,c3=st.columns(3)
c1.markdown(f"❤️ {st.session_state.lives}/{LIVES_MAX}")
c2.markdown(f"Lv {st.session_state.level}<br/>{stars(st.session_state.level)}",unsafe_allow_html=True)
c3.markdown(f"Stage: {st.session_state.stage}")

# ==== Flow ====
if st.session_state.stage=="start":
    if st.button("▶️ Start", key="start_btn"):
        st.session_state.seq=random.choices(list(ACTIONS),k=seq_len(st.session_state.level))
        st.session_state.stage="show"; st.experimental_rerun()

elif st.session_state.stage=="show":
    st.write(f"DEBUG seq={st.session_state.seq}")
    ph=st.empty()
    for act in st.session_state.seq:
        ph.image(ACTIONS[act] if os.path.isfile(ACTIONS[act]) else None,width=200,caption=act)
        local_audio(CLICK_SOUND)
        time.sleep(1)
    ph.empty()
    st.session_state.stage="guess"; st.experimental_rerun()

elif st.session_state.stage=="guess":
    for act in ACTIONS:
        if st.button(act, key=uid()):
            st.session_state.guess.append(act)
            if len(st.session_state.guess)==len(st.session_state.seq):
                st.session_state.stage="result"; st.experimental_rerun()
    st.write("Input:", st.session_state.guess)

elif st.session_state.stage=="result":
    st.write("Round complete. (simplified debug mode)")
    if st.button("Restart",key="restart"): 
        st.session_state.stage="start"; st.session_state.guess.clear()
