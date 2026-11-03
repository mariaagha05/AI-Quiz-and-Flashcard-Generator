"""
StudyBuddy AI - Quiz & Flashcard Generator
Frontend: Streamlit | LLM: Groq
Run with:  streamlit run app.py
"""

import json
import os
import random
import re

import streamlit as st
from groq import Groq

# ----------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="StudyBuddy AI - Quiz & Flashcards",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Models are tried in order. If one is unavailable the next one is used.
MODEL_OPTIONS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]
MAX_NOTES_CHARS = 12000
MIN_NOTES_CHARS = 40

# ----------------------------------------------------------------------------
# Styling: high contrast, readable fonts, calm study-friendly palette
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Merriweather:wght@700&display=swap');

:root {
    --bg: #F6F3EC;
    --card: #FFFFFF;
    --ink: #1E293B;
    --muted: #475569;
    --primary: #2F6F6B;
    --primary-dark: #245552;
    --accent: #F4B942;
    --good-bg: #E3F4E8;
    --good-ink: #14532D;
    --bad-bg: #FDE8E8;
    --bad-ink: #7F1D1D;
    --border: #D9D4C7;
}

html, body, .stApp {
    background: var(--bg) !important;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
}

/* Readable text everywhere in the main area */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp div,
.stMarkdown, [data-testid="stMarkdownContainer"] {
    color: var(--ink);
}
.stApp p, .stApp li, .stApp label { font-size: 1.05rem; line-height: 1.65; }

h1, h2, h3, h4 {
    font-family: 'Merriweather', Georgia, serif !important;
    color: var(--ink) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #EAE5D8 !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--ink); }

/* Inputs */
textarea, input[type="text"], input[type="password"] {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    font-size: 1.05rem !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
}
textarea:focus, input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(47,111,107,0.25) !important;
}
[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border-radius: 10px !important;
}
[data-baseweb="select"] * { color: var(--ink) !important; }
[data-baseweb="popover"] * { color: var(--ink) !important; background: #FFFFFF; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    transition: transform .1s ease, background .2s ease;
}
.stButton > button *, .stFormSubmitButton > button *, .stDownloadButton > button * {
    color: #FFFFFF !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: var(--primary-dark) !important;
    transform: translateY(-1px);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #FFFFFF;
    border-radius: 10px 10px 0 0;
    padding: 10px 22px;
    font-weight: 600;
    font-size: 1.05rem;
    border: 1px solid var(--border);
}
.stTabs [aria-selected="true"] { background: var(--primary) !important; }
.stTabs [aria-selected="true"] * { color: #FFFFFF !important; }

/* Radio options as readable cards */
[data-testid="stRadio"] label {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    width: 100%;
}
[data-testid="stRadio"] label:hover { border-color: var(--primary); background: #F1F8F7; }

/* Custom components */
.hero {
    background: linear-gradient(135deg, #2F6F6B 0%, #3E8E88 100%);
    padding: 28px 32px;
    border-radius: 18px;
    margin-bottom: 22px;
    box-shadow: 0 6px 18px rgba(47,111,107,0.25);
}
.hero h1, .hero p { color: #FFFFFF !important; margin: 0; }
.hero h1 { font-size: 2.1rem; margin-bottom: 6px; }
.hero p { font-size: 1.1rem; opacity: .95; }

.q-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 6px solid var(--primary);
    border-radius: 14px;
    padding: 18px 22px;
    margin: 18px 0 10px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.q-card .q-num { color: var(--primary-dark); font-weight: 700; font-size: .95rem; letter-spacing: .5px; }
.q-card .q-text { color: var(--ink); font-size: 1.2rem; font-weight: 600; margin-top: 4px; }

.result-good, .result-bad {
    border-radius: 12px; padding: 14px 18px; margin: 8px 0; font-size: 1.05rem; line-height: 1.6;
}
.result-good { background: var(--good-bg); color: var(--good-ink) !important; border: 1px solid #9AD4AB; }
.result-bad  { background: var(--bad-bg);  color: var(--bad-ink) !important;  border: 1px solid #F0A8A8; }
.result-good *, .result-bad * { color: inherit !important; }

.score-card {
    background: #FFFFFF;
    border: 2px solid var(--primary);
    border-radius: 18px;
    padding: 26px;
    text-align: center;
    margin: 10px 0 20px 0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
}
.score-card .big { font-size: 3.2rem; font-weight: 800; color: var(--primary-dark) !important; }
.score-card .msg { font-size: 1.2rem; font-weight: 600; color: var(--ink) !important; }

.flash {
    border-radius: 20px;
    padding: 56px 36px;
    min-height: 240px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center;
    box-shadow: 0 8px 24px rgba(0,0,0,0.10);
    margin: 14px 0 18px 0;
}
.flash.front { background: #FFFFFF; border: 3px solid var(--primary); }
.flash.back  { background: #FFF6DD; border: 3px solid var(--accent); }
.flash .tag  { font-size: .85rem; font-weight: 700; letter-spacing: 1.5px; color: var(--muted) !important; margin-bottom: 14px; }
.flash .txt  { font-size: 1.55rem; font-weight: 600; color: var(--ink) !important; line-height: 1.5; }

.tip {
    background: #FFFFFF; border: 1px dashed var(--primary);
    border-radius: 12px; padding: 12px 16px; font-size: 1rem;
}

/* Hide default Streamlit chrome for a cleaner look */
#MainMenu, footer { visibility: hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
DEFAULTS = {
    "mcqs": [],
    "flashcards": [],
    "gen_id": 0,
    "submitted": False,
    "user_answers": {},
    "card_idx": 0,
    "card_flipped": False,
    "topic": "",
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def resolve_api_key(typed_key: str) -> str:
    """Typed key > environment variable > Streamlit secrets."""
    if typed_key and typed_key.strip():
        return typed_key.strip()
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        secret = st.secrets.get("GROQ_API_KEY", "")
        return str(secret).strip()
    except Exception:
        return ""


def build_prompt(notes: str, difficulty: str, n_mcq: int, n_cards: int) -> str:
    difficulty_guide = {
        "Easy": "Test basic recall of key facts and definitions. Distractors should be clearly different.",
        "Medium": "Test understanding and application. Distractors should be plausible.",
        "Hard": "Test deep understanding, analysis and edge cases. Distractors should be very plausible.",
    }[difficulty]

    return f"""You are an expert teacher. Using ONLY the lesson notes below, create study material.

Difficulty: {difficulty}. {difficulty_guide}

Create exactly {n_mcq} multiple-choice questions and exactly {n_cards} flashcards.

Return ONLY valid JSON in exactly this shape:
{{
  "topic": "short topic title",
  "mcqs": [
    {{
      "question": "question text",
      "options": ["option 1", "option 2", "option 3", "option 4"],
      "answer_index": 0,
      "explanation": "2-3 sentences explaining why the correct answer is right and why others are wrong"
    }}
  ],
  "flashcards": [
    {{"front": "term or question", "back": "concise answer or definition"}}
  ]
}}

Rules:
- Each MCQ has exactly 4 options WITHOUT letter prefixes like "A)".
- answer_index is an integer 0-3 pointing to the correct option.
- Spread correct answers across positions; do not always use the same index.
- If a count is 0, return an empty list for it.
- Do not add any text outside the JSON.

LESSON NOTES:
\"\"\"
{notes}
\"\"\"
"""


def clean_option(text) -> str:
    text = str(text).strip()
    return re.sub(r"^\(?[A-Da-d][\)\.\:]\s+", "", text).strip()


def validate_payload(data: dict, want_mcq: int, want_cards: int):
    """Normalise the model output. Raises ValueError if unusable."""
    if not isinstance(data, dict):
        raise ValueError("Response was not a JSON object.")

    mcqs = []
    for item in data.get("mcqs", []) or []:
        try:
            question = str(item["question"]).strip()
            options = [clean_option(o) for o in item["options"]][:4]
            if len(options) != 4 or not question or any(not o for o in options):
                continue
            raw_idx = item.get("answer_index", item.get("answer", 0))
            if isinstance(raw_idx, str):
                raw_idx = raw_idx.strip()
                if raw_idx.upper() in ("A", "B", "C", "D"):
                    raw_idx = "ABCD".index(raw_idx.upper())
                else:
                    raw_idx = int(raw_idx)
            idx = int(raw_idx)
            if idx not in range(4):
                continue
            explanation = str(item.get("explanation", "")).strip() or "No explanation provided."
            mcqs.append(
                {"question": question, "options": options, "answer_index": idx, "explanation": explanation}
            )
        except (KeyError, TypeError, ValueError):
            continue

    cards = []
    for item in data.get("flashcards", []) or []:
        try:
            front = str(item["front"]).strip()
            back = str(item["back"]).strip()
            if front and back:
                cards.append({"front": front, "back": back})
        except (KeyError, TypeError):
            continue

    if want_mcq > 0 and not mcqs:
        raise ValueError("No valid quiz questions were returned.")
    if want_cards > 0 and not cards:
        raise ValueError("No valid flashcards were returned.")

    topic = str(data.get("topic", "")).strip()
    return topic, mcqs[:want_mcq] if want_mcq else [], cards[:want_cards] if want_cards else []


def parse_json_loose(text: str) -> dict:
    """Parse JSON even if the model wrapped it in markdown fences."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def friendly_error(exc: Exception) -> str:
    msg = str(exc)
    low = msg.lower()
    if "401" in low or "invalid api key" in low or "authentication" in low:
        return "Your Groq API key looks invalid. Please check it in the sidebar."
    if "429" in low or "rate limit" in low:
        return "Groq rate limit reached. Please wait a moment and try again."
    if "connection" in low or "timeout" in low or "timed out" in low:
        return "Could not reach Groq. Please check your internet connection and try again."
    return f"Something went wrong while generating: {msg}"


def generate_material(api_key: str, model: str, notes: str, difficulty: str, n_mcq: int, n_cards: int):
    """Call Groq with retries and model fallback. Returns (topic, mcqs, cards)."""
    client = Groq(api_key=api_key, timeout=60.0)
    prompt = build_prompt(notes, difficulty, n_mcq, n_cards)

    models_to_try = [model] + [m for m in MODEL_OPTIONS if m != model]
    last_error = None

    for current_model in models_to_try:
        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You output only valid JSON. You are a careful, accurate teacher.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.4 if attempt == 0 else 0.2,
                    max_tokens=6000,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                data = parse_json_loose(content)
                return validate_payload(data, n_mcq, n_cards)
            except (ValueError, json.JSONDecodeError) as exc:
                last_error = exc  # bad output: retry
                continue
            except Exception as exc:  # API / network problem
                last_error = exc
                low = str(exc).lower()
                if "401" in low or "invalid api key" in low:
                    raise
                break  # try next model

    raise RuntimeError(friendly_error(last_error) if last_error else "Unknown error.")


def reset_for_new_generation():
    st.session_state.gen_id += 1
    st.session_state.submitted = False
    st.session_state.user_answers = {}
    st.session_state.card_idx = 0
    st.session_state.card_flipped = False


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    typed_key = st.text_input(
        "Groq API key",
        type="password",
        placeholder="gsk_...",
        help="Or set GROQ_API_KEY as an environment variable / Streamlit secret.",
    )
    model = st.selectbox("AI model", MODEL_OPTIONS, index=0)
    difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"], value="Medium")
    output_mode = st.radio("What to create?", ["Quiz + Flashcards", "Quiz only", "Flashcards only"])

    n_mcq = 0
    n_cards = 0
    if output_mode in ("Quiz + Flashcards", "Quiz only"):
        n_mcq = st.slider("Number of quiz questions", 3, 20, 5)
    if output_mode in ("Quiz + Flashcards", "Flashcards only"):
        n_cards = st.slider("Number of flashcards", 3, 20, 8)

    st.markdown("---")
    st.markdown(
        '<div class="tip">💡 <b>Study tip:</b> Study in 25-minute blocks, '
        "then take a 5-minute break. Test yourself before re-reading!</div>",
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# Header + Input
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>📚 StudyBuddy AI</h1>
        <p>Paste your lesson notes, pick a difficulty, and get quizzes with explanations and flashcards in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

notes = st.text_area(
    "📝 Paste your lesson notes here",
    height=260,
    placeholder="Example: Photosynthesis is the process by which plants convert light energy into chemical energy...",
    max_chars=MAX_NOTES_CHARS,
)

col_a, col_b = st.columns([1, 3])
with col_a:
    generate_clicked = st.button("✨ Generate", use_container_width=True)
with col_b:
    st.caption(f"{len(notes):,} / {MAX_NOTES_CHARS:,} characters")

if generate_clicked:
    api_key = resolve_api_key(typed_key)
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar (or set GROQ_API_KEY).")
    elif len(notes.strip()) < MIN_NOTES_CHARS:
        st.warning("Please paste a bit more lesson text (at least a couple of sentences).")
    elif n_mcq == 0 and n_cards == 0:
        st.warning("Choose what you want to create in the sidebar.")
    else:
        try:
            with st.spinner("Reading your notes and writing questions..."):
                topic, mcqs, cards = generate_material(
                    api_key, model, notes.strip(), difficulty, n_mcq, n_cards
                )
            reset_for_new_generation()
            st.session_state.mcqs = mcqs
            st.session_state.flashcards = cards
            st.session_state.topic = topic
            st.success(
                f"Done! Created {len(mcqs)} question(s) and {len(cards)} flashcard(s)."
            )
        except Exception as exc:  # never crash the page
            st.error(str(exc))

# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------
mcqs = st.session_state.mcqs
cards = st.session_state.flashcards

if mcqs or cards:
    if st.session_state.topic:
        st.markdown(f"### 🎯 Topic: {st.session_state.topic}")

    tab_names = []
    if mcqs:
        tab_names.append("📝 Quiz")
    if cards:
        tab_names.append("🗂️ Flashcards")
    tabs = st.tabs(tab_names)
    tab_map = dict(zip(tab_names, tabs))

    # ------------------------------ QUIZ ------------------------------
    if mcqs:
        with tab_map["📝 Quiz"]:
            gid = st.session_state.gen_id

            if not st.session_state.submitted:
                st.markdown("Choose one answer for each question, then press **Submit answers**.")
                with st.form(f"quiz_form_{gid}"):
                    for i, q in enumerate(mcqs):
                        st.markdown(
                            f'<div class="q-card"><div class="q-num">QUESTION {i + 1} OF {len(mcqs)}</div>'
                            f'<div class="q-text">{q["question"]}</div></div>',
                            unsafe_allow_html=False if False else True,
                        )
                        st.radio(
                            f"Answer for question {i + 1}",
                            options=list(range(4)),
                            format_func=lambda k, opts=q["options"]: f"{'ABCD'[k]}.  {opts[k]}",
                            index=None,
                            key=f"q_{gid}_{i}",
                            label_visibility="collapsed",
                        )
                    submit = st.form_submit_button("✅ Submit answers")

                if submit:
                    st.session_state.user_answers = {
                        i: st.session_state.get(f"q_{gid}_{i}") for i in range(len(mcqs))
                    }
                    st.session_state.submitted = True
                    st.rerun()
            else:
                answers = st.session_state.user_answers
                score = sum(
                    1 for i, q in enumerate(mcqs) if answers.get(i) == q["answer_index"]
                )
                total = len(mcqs)
                pct = round(score / total * 100)
                if pct == 100:
                    msg = "🏆 Perfect! You've mastered this."
                elif pct >= 80:
                    msg = "🌟 Excellent work!"
                elif pct >= 60:
                    msg = "👍 Good job - review the ones you missed."
                elif pct >= 40:
                    msg = "💪 Keep going - read the explanations below."
                else:
                    msg = "📖 Time to review the notes and try again."

                st.markdown(
                    f'<div class="score-card"><div class="big">{score} / {total}</div>'
                    f'<div class="msg">{pct}% &nbsp;-&nbsp; {msg}</div></div>',
                    unsafe_allow_html=True,
                )
                st.progress(pct / 100)

                st.markdown("### 🔍 Review")
                for i, q in enumerate(mcqs):
                    chosen = answers.get(i)
                    correct = q["answer_index"]
                    is_right = chosen == correct
                    st.markdown(
                        f'<div class="q-card"><div class="q-num">QUESTION {i + 1}</div>'
                        f'<div class="q-text">{q["question"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                    your = "No answer" if chosen is None else f"{'ABCD'[chosen]}. {q['options'][chosen]}"
                    right = f"{'ABCD'[correct]}. {q['options'][correct]}"
                    if is_right:
                        st.markdown(
                            f'<div class="result-good">✅ <b>Correct!</b> Your answer: {your}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="result-bad">❌ <b>Incorrect.</b> Your answer: {your}<br>'
                            f"✔️ Correct answer: <b>{right}</b></div>",
                            unsafe_allow_html=True,
                        )
                    with st.expander("💡 Explanation", expanded=not is_right):
                        st.write(q["explanation"])

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔁 Retake quiz", use_container_width=True):
                        reset_for_new_generation()
                        st.rerun()

    # --------------------------- FLASHCARDS ---------------------------
    if cards:
        with tab_map["🗂️ Flashcards"]:
            total_cards = len(cards)
            st.session_state.card_idx = max(0, min(st.session_state.card_idx, total_cards - 1))
            idx = st.session_state.card_idx
            card = cards[idx]

            st.markdown(f"**Card {idx + 1} of {total_cards}**")
            st.progress((idx + 1) / total_cards)

            if st.session_state.card_flipped:
                st.markdown(
                    f'<div class="flash back"><div class="tag">ANSWER</div>'
                    f'<div class="txt">{card["back"]}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="flash front"><div class="tag">QUESTION / TERM</div>'
                    f'<div class="txt">{card["front"]}</div></div>',
                    unsafe_allow_html=True,
                )

            def go_prev():
                st.session_state.card_idx = max(0, st.session_state.card_idx - 1)
                st.session_state.card_flipped = False

            def go_next():
                st.session_state.card_idx = min(total_cards - 1, st.session_state.card_idx + 1)
                st.session_state.card_flipped = False

            def flip():
                st.session_state.card_flipped = not st.session_state.card_flipped

            def shuffle_cards():
                random.shuffle(st.session_state.flashcards)
                st.session_state.card_idx = 0
                st.session_state.card_flipped = False

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.button("⬅️ Previous", on_click=go_prev, disabled=idx == 0, use_container_width=True)
            with b2:
                st.button("🔄 Flip card", on_click=flip, use_container_width=True)
            with b3:
                st.button("Next ➡️", on_click=go_next, disabled=idx == total_cards - 1, use_container_width=True)
            with b4:
                st.button("🔀 Shuffle", on_click=shuffle_cards, use_container_width=True)
else:
    st.markdown(
        '<div class="tip">👋 <b>How it works:</b> 1) Paste your notes &nbsp; 2) Choose difficulty in the sidebar '
        "&nbsp; 3) Click <b>Generate</b> &nbsp; 4) Take the quiz and review flashcards.</div>",
        unsafe_allow_html=True,
    )
