
import streamlit as st
st.set_page_config(page_title="Ham Rhythm Local", layout="centered")

# Offline‑safe Action Rhythm Game (Local assets)
# Debugged for Streamlit >=1.44: replaced experimental_rerun with safe rerun wrapper

import os, random, time, base64, uuid
from datetime import date

# Configuration
ASSET_DIR = "assets"
LIVES_MAX = 3
ROUNDS_PER_LEVEL = 3
MAX_LEVEL = 20
BOSS_INTERVAL = 5
BASE_SPEED = 1.5
MIN_SPEED = 0.5

# Utility
def uid() -> str:
    return uuid.uuid4().hex

def star_badge(level: int) -> str:
    stars = "★" * max(1, level // 5)
    return stars.ljust(5, "☆")

def seq_len(level: int) -> int:
    if level >= 19:
        return 9
    if level >= 15:
        return 8
    return min(7, 2 + level)

def play_speed(level: int, diff: float) -> float:
    return max(MIN_SPEED, BASE_SPEED - 0.1 * (level - 1) - 0.2 * diff)

def is_boss(level: int) -> bool:
    return level % BOSS_INTERVAL == 0

def asset(name: str) -> str:
    path = os.path.join(ASSET_DIR, name)
    if not os.path.isfile(path):
        st.warning(f"⚠️ Missing asset: {path}")
    return path

def local_audio(path: str):
    if os.path.isfile(path):
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        st.audio(f"data:audio/wav;base64,{b64}", format="audio/wav")

def safe_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        return  # no-op for Streamlit >=1.44

# Assets
ACTIONS = {
    "起きる / Wake": asset("ham_wake.png"),
    "歩く / Walk": asset("ham_walk.png"),
    "食べる / Eat": asset("ham_eat.png"),
    "寝る / Sleep": asset("ham_sleep.png"),
}
CLICK_SOUND = asset("click.wav")
LEVELUP_SOUND = asset("levelup_fanfare.mp3")

# Session state
today = date.today().isoformat()
if "initialized" not in st.session_state:
    st.session_state.update(
        initialized=True,
        level=1,
        diff=0.0,
        stage="start",
        guess=[],
        seq=[],
        lives=LIVES_MAX,
        round=0,
        best_level=1,
        today_level=0,
        today=today,
    )
if st.session_state.today != today:
    st.session_state.today = today
    st.session_state.today_level = 0

# Header
st.title("🐹 Action Rhythm (Local Debug)")
c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
c1.markdown(f"❤️ {st.session_state.lives}/{LIVES_MAX}")
c2.markdown(f"🏅 Lv {st.session_state.level}<br/>{star_badge(st.session_state.level)}", unsafe_allow_html=True)
c3.progress(st.session_state.round / ROUNDS_PER_LEVEL, text=f"Round {st.session_state.round}/{ROUNDS_PER_LEVEL}")
c4.markdown(f"Diff {st.session_state.diff:+.1f}" + (" 🔄" if is_boss(st.session_state.level) else ""))

# Game flow
if st.session_state.stage == "start":
    if st.button("▶️ Start", key="start_btn"):
        st.session_state.seq = random.choices(list(ACTIONS), k=seq_len(st.session_state.level))
        st.session_state.stage = "show"
        safe_rerun()

elif st.session_state.stage == "show":
    if is_boss(st.session_state.level):
        st.info("🎵 Reverse order!")
    ph = st.empty()
    for act in st.session_state.seq:
        ph.image(ACTIONS[act], width=200, caption=act)
        local_audio(CLICK_SOUND)
        time.sleep(play_speed(st.session_state.level, st.session_state.diff))
    ph.empty()
    st.session_state.stage = "guess"
    safe_rerun()

elif st.session_state.stage == "guess":
    st.write("📝 Tap actions" + (" (Reverse)" if is_boss(st.session_state.level) else ""))
    for act in ACTIONS:
        if st.button(act, key=uid()):
            st.session_state.guess.append(act)
            local_audio(CLICK_SOUND)
            if len(st.session_state.guess) == len(st.session_state.seq):
                st.session_state.stage = "result"
                safe_rerun()
    st.caption("Input: " + " → ".join(st.session_state.guess))

elif st.session_state.stage == "result":
    target = st.session_state.seq[::-1] if is_boss(st.session_state.level) else st.session_state.seq
    correct = st.session_state.guess == target
    acc = sum(a == b for a, b in zip(st.session_state.guess, target)) / len(target)
    st.session_state.diff = max(-1, min(1, st.session_state.diff + (acc - 0.5) * 0.4))

    if correct:
        st.success("✅ Round Clear!")
        st.session_state.round += 1
    else:
        st.error("❌ Miss! Correct: " + " → ".join(target))
        st.session_state.lives -= 1

    if st.session_state.lives == 0:
        st.error(f"Game Over – Lv {st.session_state.level}")
        if st.button("Restart", key="restart"):
            st.session_state.stage = "start"
            st.session_state.guess.clear()
            st.session_state.round = 0
            safe_rerun()
    elif st.session_state.round == ROUNDS_PER_LEVEL and correct:
        local_audio(LEVELUP_SOUND)
        st.balloons()
        st.session_state.best_level = max(st.session_state.best_level, st.session_state.level)
        st.session_state.today_level = max(st.session_state.today_level, st.session_state.level)
        if st.session_state.level < MAX_LEVEL:
            if st.button("Next Level", key="next_level"):
                st.session_state.level += 1
                st.session_state.round = 0
                st.session_state.stage = "start"
                st.session_state.guess.clear()
                safe_rerun()
        else:
            st.success("🎉 Completed all 20 levels!")
    else:
        if st.button("Next Round", key="next_round"):
            st.session_state.guess.clear()
            st.session_state.stage = "show"
            safe_rerun()
