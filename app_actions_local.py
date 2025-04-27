import streamlit as st
st.set_page_config(page_title="🐹 Action Rhythm", layout="centered")

# ───────────────────────────────────────────────────────────
# app_actions_local_game.py
# Offline-safe “Wake / Walk / Eat / Sleep” リズムゲーム 本番版
# ・Lv15–18: 8アクション / Lv19–20: 9アクション
# ・5レベルごと逆再生ボス / 最大Lv20
# ・ローカル assets/ から画像・音声を読み込む
# ───────────────────────────────────────────────────────────

import os, random, time, base64, uuid
from datetime import date

# ─── 設定 ─────────────────────────
ASSET_DIR        = "assets"
LIVES_MAX        = 3
ROUNDS_PER_LEVEL = 3
MAX_LEVEL        = 20
BOSS_INTERVAL    = 5
BASE_SPEED       = 1.5   # 秒
MIN_SPEED        = 0.5   # 秒

# ─── ユーティリティ ─────────────────
def uid() -> str:
    return uuid.uuid4().hex

def star_badge(lv: int) -> str:
    filled = "★" * max(1, lv // 5)
    return filled.ljust(5, "☆")

def seq_len(lv: int) -> int:
    if lv >= 19: return 9
    if lv >= 15: return 8
    return min(7, 2 + lv)

def play_speed(lv: int, diff: float) -> float:
    return max(MIN_SPEED, BASE_SPEED - 0.1 * (lv - 1) - 0.2 * diff)

def is_boss(lv: int) -> bool:
    return lv % BOSS_INTERVAL == 0

def asset(name: str) -> str:
    path = os.path.join(ASSET_DIR, name)
    if not os.path.isfile(path):
        st.warning(f"⚠️ Missing asset: {path}")
    return path

def play_sound(path: str):
    if os.path.isfile(path):
        data = base64.b64encode(open(path, "rb").read()).decode()
        st.audio(f"data:audio/wav;base64,{data}", format="audio/wav")

def safe_rerun():
    try:
        st.experimental_rerun()
    except:
        pass

# ─── リソース読み込み ─────────────────
ACTIONS = {
    "起きる / Wake":  asset("ham_wake.png"),
    "歩く / Walk":    asset("ham_walk.png"),
    "食べる / Eat":   asset("ham_eat.png"),
    "寝る / Sleep":   asset("ham_sleep.png"),
}
CLICK_SOUND   = asset("click.wav")
LEVELUP_SOUND = asset("levelup_fanfare.mp3")

# ─── セッション初期化 ─────────────────
today = date.today().isoformat()
if "initialized" not in st.session_state:
    st.session_state.update(
        initialized=True,
        level=1, diff=0.0,
        stage="start", seq=[], guess=[],
        lives=LIVES_MAX, round=0,
        best_level=1, today_level=0,
        today=today
    )
if st.session_state.today != today:
    st.session_state.today = today
    st.session_state.today_level = 0

# ─── UI ヘッダー ────────────────────
st.title("🐹 Action Rhythm (Local Lv20)")
c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
c1.markdown(f"❤️ {st.session_state.lives}/{LIVES_MAX}")
c2.markdown(
    f"🏅 Lv {st.session_state.level}<br/>{star_badge(st.session_state.level)}",
    unsafe_allow_html=True
)
c3.progress(
    st.session_state.round / ROUNDS_PER_LEVEL,
    text=f"Round {st.session_state.round}/{ROUNDS_PER_LEVEL}"
)
c4.markdown(
    f"Diff {st.session_state.diff:+.1f}" +
    (" 🔄Reverse" if is_boss(st.session_state.level) else "")
)

with st.sidebar:
    st.markdown("### 📅 Today")
    st.write(f"Best: {st.session_state.today_level}")
    st.write(star_badge(st.session_state.today_level))
    st.markdown("### 🏆 All-time")
    st.write(f"Best: {st.session_state.best_level}")
    st.write(star_badge(st.session_state.best_level))

# ─── ゲームフロー ───────────────────
if st.session_state.stage == "start":
    if st.button("▶️ Start", key="start_btn"):
        # シーケンス生成
        st.session_state.seq = random.choices(
            list(ACTIONS), k=seq_len(st.session_state.level)
        )
        st.session_state.stage = "show"
        safe_rerun()

elif st.session_state.stage == "show":
    if is_boss(st.session_state.level):
        st.info("🎵 Reverse order!")
    ph = st.empty()
    for act in st.session_state.seq:
        ph.image(ACTIONS[act], width=200, caption=act)
        play_sound(CLICK_SOUND)
        time.sleep(play_speed(
            st.session_state.level, st.session_state.diff
        ))
    ph.empty()
    st.session_state.stage = "guess"
    safe_rerun()

elif st.session_state.stage == "guess":
    st.write(
        "📝 Tap actions" +
        (" (Reverse)" if is_boss(st.session_state.level) else "")
    )
    for act in ACTIONS:
        if st.button(act, key=uid()):
            st.session_state.guess.append(act)
            play_sound(CLICK_SOUND)
            if len(st.session_state.guess) == len(st.session_state.seq):
                st.session_state.stage = "result"
                safe_rerun()
    st.caption("Input: " + " → ".join(st.session_state.guess))

elif st.session_state.stage == "result":
    target = (
        list(reversed(st.session_state.seq))
        if is_boss(st.session_state.level)
        else st.session_state.seq
    )
    success = st.session_state.guess == target

    # 難易度調整
    acc = sum(a == b for a, b in zip(st.session_state.guess, target)) / len(target)
    st.session_state.diff = max(-1, min(1, st.session_state.diff + (acc - 0.5) * 0.4))

    if success:
        st.success("✅ Round Clear!")
        st.session_state.round += 1
    else:
        st.error("❌ Miss! Correct: " + " → ".join(target))
        st.session_state.lives -= 1

    # 分岐処理
    if st.session_state.lives == 0:
        st.error(f"Game Over – Lv {st.session_state.level}")
        if st.button("🔄 Restart", key="restart_btn"):
            st.session_state.stage = "start"
            st.session_state.guess.clear()
            st.session_state.round = 0
            safe_rerun()

    elif st.session_state.round == ROUNDS_PER_LEVEL and success:
        play_sound(LEVELUP_SOUND)
        st.balloons()
        st.session_state.best_level = max(
            st.session_state.best_level, st.session_state.level
        )
        st.session_state.today_level = max(
            st.session_state.today_level, st.session_state.level
        )
        if st.session_state.level < MAX_LEVEL:
            if st.button("▶️ Next Level", key="next_btn"):
                st.session_state.level += 1
                st.session_state.round = 0
                st.session_state.guess.clear()
                st.session_state.stage = "start"
                safe_rerun()
        else:
            st.success("🎉 完全クリア！")

    else:
        if st.button("▶️ Next Round", key="round_btn"):
            st.session_state.guess.clear()
            st.session_state.stage = "show"
            safe_rerun()
