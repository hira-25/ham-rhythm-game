
"""app_actions_local.py
Local assets version (offline-safe) – Wake / Walk / Eat / Sleep rhythm game.
Lv15–18: 8 actions, Lv19–20: 9 actions, Reverse boss every 5 levels, hard cap Lv20.
"""

import os, random, time, base64, uuid
from datetime import date
import streamlit as st

# Configuration
LIVES_MAX = 3
ROUNDS_PER_LEVEL = 3
MAX_LEVEL = 20
BOSS_INTERVAL = 5
BASE_SPEED = 1.5
MIN_SPEED = 0.5

ASSET_DIR = "assets"  # Local folder containing PNG/WAV/MP3

def asset(name: str) -> str:
    path = os.path.join(ASSET_DIR, name)
    if not os.path.isfile(path):
        st.warning(f"⚠️ Missing asset: {path}")
    return path

ACTIONS = {
    "起きる / Wake":  asset("ham_wake.png"),
    "歩く / Walk":    asset("ham_walk.png"),
    "食べる / Eat":   asset("ham_eat.png"),
    "寝る / Sleep":   asset("ham_sleep.png"),
}
CLICK_SOUND   = asset("click.wav")
LEVELUP_SOUND = asset("levelup_fanfare.mp3")

# Session init
today_str = date.today().isoformat()
if "init" not in st.session_state:
    st.session_state.update(
        init=True, level=1, diff=0.0,
        stage="start", seq=[], guess=[],
        lives=LIVES_MAX, round=0,
        best_level=1, today_level=0, today=today_str
    )
if st.session_state.today != today_str:
    st.session_state.today, st.session_state.today_level = today_str, 0

# Helpers
uid = lambda: uuid.uuid4().hex
stars = lambda lv: ("★" * max(1, lv // 5)).ljust(5, "☆")

def seq_len(lv):
    if lv >= 19: return 9
    if lv >= 15: return 8
    return min(7, 2 + lv)

def play_speed():
    lv, diff = st.session_state.level, st.session_state.diff
    return max(MIN_SPEED, BASE_SPEED - 0.1 * (lv - 1) - 0.2 * diff)

def is_boss(): return st.session_state.level % BOSS_INTERVAL == 0

def reset(up=False):
    st.session_state.update(stage="start", seq=[], guess=[], round=0, lives=LIVES_MAX)
    if up and st.session_state.level < MAX_LEVEL:
        st.session_state.level += 1

def local_audio(path):
    if os.path.isfile(path):
        data = base64.b64encode(open(path, "rb").read()).decode()
        st.audio(f"data:audio/wav;base64,{data}", format="audio/wav")

# UI Header
st.set_page_config(page_title="Ham Rhythm Local", layout="centered")
st.title("🐹 アクションリズム・ローカル版 (Lv20)")

c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
c1.markdown(f"❤️ {st.session_state.lives}/{LIVES_MAX}")
c2.markdown(f"🏅 Lv {st.session_state.level}<br/>{stars(st.session_state.level)}", unsafe_allow_html=True)
c3.progress(st.session_state.round / ROUNDS_PER_LEVEL,
            text=f"Round {st.session_state.round}/{ROUNDS_PER_LEVEL}")
c4.markdown(f"Diff {st.session_state.diff:+.1f}" + (" 🔄Reverse" if is_boss() else ""))

# Sidebar records
with st.sidebar:
    st.markdown("### 📅 Today")
    st.write(f"Best: {st.session_state.today_level}")
    st.write(stars(st.session_state.today_level))
    st.markdown("### 🏆 All-time")
    st.write(f"Best: {st.session_state.best_level}")
    st.write(stars(st.session_state.best_level))

# Game flow
if st.session_state.stage == "start":
    if st.button("▶️ Start", key=uid()):
        st.session_state.seq = random.choices(list(ACTIONS), k=seq_len(st.session_state.level))
        st.session_state.stage = "show"
        st.experimental_rerun()

elif st.session_state.stage == "show":
    if is_boss():
        st.info("🎵 Reverse order!")
    ph = st.empty()
    for act in st.session_state.seq:
        ph.image(ACTIONS[act], width=200)
        local_audio(CLICK_SOUND)
        time.sleep(play_speed())
    ph.empty()
    st.session_state.stage = "guess"
    st.experimental_rerun()

elif st.session_state.stage == "guess":
    st.write("📝 Tap actions" + (" (Reverse)" if is_boss() else ""))
    cols = st.columns(4)
    for col, act in zip(cols, ACTIONS):
        with col:
            st.image(ACTIONS[act], width=100, caption=act)
            if st.button("", key=uid()):
                st.session_state.guess.append(act)
                local_audio(CLICK_SOUND)
                if len(st.session_state.guess) == len(st.session_state.seq):
                    st.session_state.stage = "result"
                    st.experimental_rerun()
    st.caption("Input: " + " → ".join(st.session_state.guess))

elif st.session_state.stage == "result":
    target = st.session_state.seq[::-1] if is_boss() else st.session_state.seq
    success = st.session_state.guess == target
    # DDA update
    acc = sum(a == b for a, b in zip(st.session_state.guess, target)) / len(target)
    st.session_state.diff = max(-1, min(1, st.session_state.diff + (acc - 0.5) * 0.4))
    if success:
        st.success("✅ Round Clear!")
        st.session_state.round += 1
    else:
        st.error("❌ Miss! Correct: " + " → ".join(target))
        st.session_state.lives -= 1

    # Branches
    if st.session_state.lives == 0:
        st.error(f"Game Over – Reached Lv {st.session_state.level}")
        if st.button("Restart", key=uid()):
            reset()
            st.experimental_rerun()
    elif st.session_state.round == ROUNDS_PER_LEVEL and success:
        local_audio(LEVELUP_SOUND)
        st.balloons()
        st.session_state.best_level = max(st.session_state.best_level, st.session_state.level)
        st.session_state.today_level = max(st.session_state.today_level, st.session_state.level)
        if st.session_state.level == MAX_LEVEL:
            st.success("🎉 Completed all 20 levels!")
        else:
            if st.button("Next Level", key=uid()):
                reset(next_level=True)
                st.experimental_rerun()
    else:
        if st.button("Next Round", key=uid()):
            st.session_state.update(guess=[], stage="show")
            st.experimental_rerun()
