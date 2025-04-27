import streamlit as st
st.set_page_config(page_title="Ham Rhythm Local", layout="centered")

"""app_actions_local_refactored.py
Offline‑safe Action Rhythm Game (Wake / Walk / Eat / Sleep)
Lv15–18: 8 actions, Lv19–20: 9 actions, Reverse boss every 5 levels, cap Lv20.
Refactored for readability and robustness based on code‑review feedback.
"""

# ────── Imports ──────
import os
import random
import time
import base64
import uuid
from datetime import date
from typing import Dict

# ────── Constants ──────
ASSET_DIR = "assets"

LIVES_MAX        = 3
ROUNDS_PER_LEVEL = 3
MAX_LEVEL        = 20
BOSS_INTERVAL    = 5

BASE_SPEED = 1.5     # seconds per action at Lv1
MIN_SPEED  = 0.5     # floor speed

HEART_EMOJI = "❤️"
MEDAL_EMOJI = "🏅"
STAR_FILLED = "★"
STAR_EMPTY  = "☆"

# ────── Utility functions ──────
def uid() -> str:
    """Return a unique key for Streamlit widgets."""
    return uuid.uuid4().hex

def stars(level: int) -> str:
    """Return a 5‑star badge string for the given level."""
    filled = STAR_FILLED * max(1, level // 5)
    return filled.ljust(5, STAR_EMPTY)

def seq_len(level: int) -> int:
    """Return sequence length based on level tiers."""
    if level >= 19:
        return 9
    if level >= 15:
        return 8
    return min(7, 2 + level)

def play_speed(level: int, diff: float) -> float:
    """Compute speed per action given level and difficulty delta."""
    return max(MIN_SPEED, BASE_SPEED - 0.1 * (level - 1) - 0.2 * diff)

def is_boss(level: int) -> bool:
    """True if the level is a reverse‑mode boss stage."""
    return level % BOSS_INTERVAL == 0

def asset_path(name: str) -> str:
    """Return full path in ASSET_DIR and warn if missing."""
    path = os.path.join(ASSET_DIR, name)
    if not os.path.isfile(path):
        st.warning(f"⚠️ Missing asset: {path}")
    return path

def local_audio(path: str) -> None:
    """Play a local WAV file inline. Safe if file missing."""
    if os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.audio(f"data:audio/wav;base64,{b64}", format="audio/wav")
        except Exception as exc:
            st.error(f"Audio load error: {exc}")

# ────── Assets ──────
ACTIONS: Dict[str, str] = {
    "起きる / Wake":  asset_path("ham_wake.png"),
    "歩く / Walk":    asset_path("ham_walk.png"),
    "食べる / Eat":   asset_path("ham_eat.png"),
    "寝る / Sleep":   asset_path("ham_sleep.png"),
}
CLICK_SOUND   = asset_path("click.wav")
LEVELUP_SOUND = asset_path("levelup_fanfare.mp3")

# ────── Session Initialization ──────
today_str = date.today().isoformat()
if "init" not in st.session_state:
    st.session_state.update(
        init=True,
        level=1,
        diff=0.0,
        stage="start",
        seq=[],
        guess=[],
        lives=LIVES_MAX,
        round=0,
        best_level=1,
        today_level=0,
        today=today_str,
    )
# Reset daily record if date changed
if st.session_state.today != today_str:
    st.session_state.today = today_str
    st.session_state.today_level = 0

# ────── Helpers to mutate state ──────
def reset(level_up: bool = False) -> None:
    """Reset round state; optionally increment level."""
    st.session_state.update(
        stage="start",
        seq=[],
        guess=[],
        round=0,
        lives=LIVES_MAX,
    )
    if level_up and st.session_state.level < MAX_LEVEL:
        st.session_state.level += 1

# ────── UI Header ──────
st.title("🐹 アクションリズム・ローカル版 (Lv20)")
col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
col1.markdown(f"{HEART_EMOJI} {st.session_state.lives}/{LIVES_MAX}")
col2.markdown(f"{MEDAL_EMOJI} Lv {st.session_state.level}<br/>{stars(st.session_state.level)}", unsafe_allow_html=True)
col3.progress(
    st.session_state.round / ROUNDS_PER_LEVEL,
    text=f"Round {st.session_state.round}/{ROUNDS_PER_LEVEL}",
)
col4.markdown(f"Diff {st.session_state.diff:+.1f}" + (" 🔄Reverse" if is_boss(st.session_state.level) else ""))

# Sidebar stats
with st.sidebar:
    st.markdown("### 📅 Today")
    st.write(f"Best: {st.session_state.today_level}")
    st.write(stars(st.session_state.today_level))
    st.markdown("### 🏆 All‑time")
    st.write(f"Best: {st.session_state.best_level}")
    st.write(stars(st.session_state.best_level))

# ────── Game Flow ──────
if st.session_state.stage == "start":
    if st.button("▶️ Start", key=uid()):
        st.session_state.seq = random.choices(list(ACTIONS), k=seq_len(st.session_state.level))
        st.session_state.stage = "show"
        st.experimental_rerun()

elif st.session_state.stage == "show":
    if is_boss(st.session_state.level):
        st.info("🎵 Reverse order!")
    placeholder = st.empty()
    for act in st.session_state.seq:
        placeholder.image(ACTIONS[act], width=200)
        local_audio(CLICK_SOUND)
        time.sleep(play_speed(st.session_state.level, st.session_state.diff))
    placeholder.empty()
    st.session_state.stage = "guess"
    st.experimental_rerun()

elif st.session_state.stage == "guess":
    st.write("📝 Tap actions" + (" (Reverse)" if is_boss(st.session_state.level) else ""))
    for act in ACTIONS:
        if st.button(act, key=uid()):
            st.session_state.guess.append(act)
            local_audio(CLICK_SOUND)
            if len(st.session_state.guess) == len(st.session_state.seq):
                st.session_state.stage = "result"
                st.experimental_rerun()
    st.caption("Input: " + " → ".join(st.session_state.guess))

elif st.session_state.stage == "result":
    target = st.session_state.seq[::-1] if is_boss(st.session_state.level) else st.session_state.seq
    success = st.session_state.guess == target

    # Update difficulty
    acc = sum(a == b for a, b in zip(st.session_state.guess, target)) / len(target)
    st.session_state.diff = max(-1, min(1, st.session_state.diff + (acc - 0.5) * 0.4))

    if success:
        st.success("✅ Round Clear!")
        st.session_state.round += 1
    else:
        st.error("❌ Miss! Correct: " + " → ".join(target))
        st.session_state.lives -= 1

    # Branch logic
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
                reset(level_up=True)
                st.experimental_rerun()
    else:
        if st.button("Next Round", key=uid()):
            st.session_state.guess.clear()
            st.session_state.stage = "show"
            st.experimental_rerun()
