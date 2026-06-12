"""Multilingual Meeting Notes Generator — Streamlit Application."""

import os
import sys
import tempfile
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# ── ensure project root is on sys.path for local imports ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pyrefly: ignore [missing-import]
from src.services.audio_processor import MeetingProcessor
# pyrefly: ignore [missing-import]
from src.data.data_models import MeetingResult


# ──────────────────────────────────────────────────────────────
# 0. Environment & page config
# ──────────────────────────────────────────────────────────────
load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

st.set_page_config(
    page_title="AI Meeting Notes Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────────────────────
# 1. Custom CSS — premium dark-theme look
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary: #0a0e1a;
    --bg-card: rgba(16, 22, 40, 0.85);
    --bg-card-hover: rgba(22, 30, 55, 0.92);
    --accent: #6c63ff;
    --accent-glow: rgba(108, 99, 255, 0.35);
    --accent-2: #00d4aa;
    --accent-3: #ff6b9d;
    --text-primary: #e8eaf6;
    --text-secondary: #9aa2c4;
    --border: rgba(108, 99, 255, 0.18);
    --radius: 16px;
    --shadow: 0 8px 32px rgba(0,0,0,0.35);
}

/* ── Global reset ── */
html, body, [data-testid="stApp"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary);
}

/* ── Header hero ── */
.hero {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    border-radius: var(--radius);
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 30% 40%, var(--accent-glow), transparent 60%),
                radial-gradient(circle at 70% 60%, rgba(0,212,170,0.12), transparent 50%);
    pointer-events: none;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #fff 0%, #c3bfff 50%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    position: relative;
}
.hero p {
    font-size: 1.05rem;
    color: var(--text-secondary);
    margin-top: .6rem;
    position: relative;
}

/* ── Glass card ── */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(18px);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.8rem;
    margin-bottom: 1.4rem;
    box-shadow: var(--shadow);
    transition: transform .25s ease, box-shadow .25s ease;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(108,99,255,0.18);
}

/* ── Metric chips ── */
.metric-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1.4rem;
}
.metric-chip {
    flex: 1;
    min-width: 140px;
    background: linear-gradient(135deg, rgba(108,99,255,0.12), rgba(0,212,170,0.08));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    text-align: center;
    transition: transform .2s ease;
}
.metric-chip:hover { transform: scale(1.04); }
.metric-chip .value {
    font-size: 1.85rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-chip .label {
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--text-secondary);
    margin-top: .25rem;
}

/* ── Section titles ── */
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: .8rem;
    display: flex;
    align-items: center;
    gap: .5rem;
}

/* ── Speaker badge ── */
.speaker-badge {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    background: linear-gradient(135deg, rgba(108,99,255,0.18), rgba(108,99,255,0.06));
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: .4rem 1rem;
    font-size: .82rem;
    font-weight: 500;
    margin-right: .5rem;
    margin-bottom: .5rem;
}
.speaker-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
}

/* ── Action-item card ── */
.action-card {
    background: rgba(16, 22, 40, 0.7);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: .7rem;
    transition: background .2s;
}
.action-card:hover { background: rgba(22, 30, 55, 0.85); }
.action-card .priority {
    display: inline-block;
    font-size: .68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: .15rem .55rem;
    border-radius: 4px;
    margin-left: .6rem;
}
.priority-high   { background: rgba(255,107,157,0.22); color: #ff6b9d; }
.priority-medium { background: rgba(255,183,77,0.22);  color: #ffb74d; }
.priority-low    { background: rgba(0,212,170,0.22);   color: #00d4aa; }

/* ── Transcript bubble ── */
.transcript-bubble {
    background: rgba(16, 22, 40, 0.6);
    border-radius: 12px;
    padding: .9rem 1.2rem;
    margin-bottom: .55rem;
    border: 1px solid rgba(108,99,255,0.08);
}
.transcript-bubble .speaker-name {
    font-weight: 600;
    font-size: .85rem;
    margin-bottom: .25rem;
}
.transcript-bubble .text {
    font-size: .92rem;
    line-height: 1.55;
    color: var(--text-secondary);
}
.transcript-bubble .time {
    font-size: .72rem;
    color: rgba(154,162,196,0.6);
    margin-top: .2rem;
}

/* ── Sidebar polish ── */
[data-testid="stSidebar"] {
    border-right: 1px solid var(--border);
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent), #8b7aff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: .55rem 1.6rem !important;
    transition: transform .2s, box-shadow .2s !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px var(--accent-glow) !important;
}

/* ── Upload area ── */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
}

/* ── Processing spinner ── */
.processing-status {
    text-align: center;
    padding: 2rem;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 2. Helpers
# ──────────────────────────────────────────────────────────────
SPEAKER_COLORS = [
    "#6c63ff", "#00d4aa", "#ff6b9d", "#ffb74d",
    "#64b5f6", "#ce93d8", "#4dd0e1", "#aed581",
]

LANGUAGE_MAP = {
    "en": "English 🇬🇧", "es": "Spanish 🇪🇸", "fr": "French 🇫🇷",
    "de": "German 🇩🇪", "it": "Italian 🇮🇹", "pt": "Portuguese 🇵🇹",
    "hi": "Hindi 🇮🇳", "zh": "Chinese 🇨🇳", "ja": "Japanese 🇯🇵",
    "ko": "Korean 🇰🇷", "ru": "Russian 🇷🇺", "ar": "Arabic 🇸🇦",
}


def format_duration(seconds: int) -> str:
    """Convert seconds to human-friendly string."""
    if seconds <= 0:
        return "N/A"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def format_ms(ms: int) -> str:
    """Convert milliseconds to mm:ss."""
    total_sec = ms // 1000
    m, s = divmod(total_sec, 60)
    return f"{m:02d}:{s:02d}"


def build_summary_download(result: MeetingResult) -> str:
    """Create a plain-text summary for download."""
    lines = [
        f"MEETING SUMMARY — {result.title}",
        f"Date: {result.processed_at.strftime('%B %d, %Y at %I:%M %p')}",
        f"Language: {LANGUAGE_MAP.get(result.language, result.language)}",
        f"Duration: {format_duration(result.duration)}",
        "",
        "=" * 60,
        "SUMMARY",
        "=" * 60,
        result.summary.replace("**", "").replace("•", "-"),
        "",
        "=" * 60,
        "ACTION ITEMS",
        "=" * 60,
    ]
    for i, item in enumerate(result.action_items, 1):
        lines.append(f"{i}. [{item.priority.upper()}] {item.description}")
        if item.assignee:
            lines.append(f"   Assignee: {item.assignee}")
        if item.due_date:
            lines.append(f"   Due: {item.due_date}")
    return "\n".join(lines)


def build_transcript_download(result: MeetingResult) -> str:
    """Create a plain-text transcript for download."""
    speaker_map = {s.id: s.name for s in result.speakers}
    lines = [
        f"FULL TRANSCRIPT — {result.title}",
        f"Date: {result.processed_at.strftime('%B %d, %Y at %I:%M %p')}",
        "",
    ]
    for seg in result.segments:
        name = speaker_map.get(seg.speaker_id, seg.speaker_id)
        lines.append(f"[{format_ms(seg.start_time)}] {name}: {seg.text}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 3. Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown("---")

    if not ASSEMBLYAI_API_KEY:
        st.warning("⚠️ ASSEMBLY_AI_API_KEY missing in `.env`")
    else:
        st.success("✅ AssemblyAI key loaded")

    if not OPENAI_API_KEY:
        st.warning("⚠️ OPENAI_API_KEY missing in `.env`")
    else:
        st.success("✅ OpenAI key loaded")

    st.markdown("---")
    st.markdown(
        """
        **Supported formats**  
        `MP3` · `WAV` · `M4A` · `MP4`

        **Supported languages**  
        99 languages with auto-detection
        """,
    )
    st.markdown("---")
    st.caption("Built with AssemblyAI + OpenAI + Streamlit")


# ──────────────────────────────────────────────────────────────
# 4. Hero header
# ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎙️ AI Meeting Notes Generator</h1>
    <p>Upload a meeting recording — get an AI-powered summary, speaker analysis &amp; action items in seconds.</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# 5. File uploader
# ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Drop your meeting audio here",
    type=["mp3", "wav", "m4a", "mp4"],
    help="Maximum file size: 200 MB",
)

col_btn, col_spacer = st.columns([1, 3])
with col_btn:
    start_btn = st.button("🚀 Start Processing", type="primary", use_container_width=True)

# ──────────────────────────────────────────────────────────────
# 6. Processing
# ──────────────────────────────────────────────────────────────
if start_btn:
    # ── Validation ──
    if not uploaded_file:
        st.error("📂 Please upload an audio file first.")
        st.stop()
    if not ASSEMBLYAI_API_KEY:
        st.error("🔑 AssemblyAI API key is missing. Add it to your `.env` file.")
        st.stop()
    if not OPENAI_API_KEY:
        st.error("🔑 OpenAI API key is missing. Add it to your `.env` file.")
        st.stop()

    # ── Save uploaded file to temp dir ──
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # ── Process with status indicators ──
    try:
        progress = st.progress(0, text="Initialising…")
        status_area = st.empty()

        status_area.markdown(
            '<div class="processing-status">🔧 Initialising processor…</div>',
            unsafe_allow_html=True,
        )
        progress.progress(10, text="Initialising processor…")

        processor = MeetingProcessor(ASSEMBLYAI_API_KEY, OPENAI_API_KEY)

        status_area.markdown(
            '<div class="processing-status">🎤 Transcribing audio — this may take a few minutes…</div>',
            unsafe_allow_html=True,
        )
        progress.progress(30, text="Transcribing audio…")

        result: MeetingResult = processor.process_meeting_audio(tmp_path)

        progress.progress(100, text="Done!")
        status_area.empty()
        time.sleep(0.3)
        progress.empty()

        st.session_state["result"] = result

    except Exception as exc:
        st.error(f"❌ Processing failed: {exc}")
        st.stop()
    finally:
        # Cleanup temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

# ──────────────────────────────────────────────────────────────
# 7. Results display
# ──────────────────────────────────────────────────────────────
if "result" in st.session_state:
    result: MeetingResult = st.session_state["result"]

    st.markdown("---")

    # ── Metrics row ──
    lang_label = LANGUAGE_MAP.get(result.language, result.language)
    metrics_html = f"""
    <div class="metric-row">
        <div class="metric-chip">
            <div class="value">{format_duration(result.duration)}</div>
            <div class="label">Duration</div>
        </div>
        <div class="metric-chip">
            <div class="value">{result.unique_speakers_count}</div>
            <div class="label">Speakers</div>
        </div>
        <div class="metric-chip">
            <div class="value">{result.total_words:,}</div>
            <div class="label">Words</div>
        </div>
        <div class="metric-chip">
            <div class="value">{lang_label}</div>
            <div class="label">Detected Language</div>
        </div>
        <div class="metric-chip">
            <div class="value">{result.avg_confidence:.0%}</div>
            <div class="label">Confidence</div>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    # ── Two-column layout for summary + speakers ──
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📝 Meeting Summary</div>', unsafe_allow_html=True)
        st.markdown(f"### {result.title}")
        st.markdown(result.summary)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">👥 Speakers</div>', unsafe_allow_html=True)

        for idx, speaker in enumerate(result.speakers):
            color = SPEAKER_COLORS[idx % len(SPEAKER_COLORS)]
            st.markdown(
                f"""
                <div class="speaker-badge">
                    <span class="speaker-dot" style="background:{color}"></span>
                    <strong>{speaker.name}</strong>
                    &nbsp;·&nbsp; {speaker.word_count} words
                    &nbsp;·&nbsp; {format_duration(speaker.speaking_time)}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Action Items ──
    if result.action_items:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-title">✅ Action Items ({len(result.action_items)})</div>',
            unsafe_allow_html=True,
        )
        for item in result.action_items:
            pclass = f"priority-{item.priority}"
            assignee_str = f" — <em>{item.assignee}</em>" if item.assignee else ""
            due_str = f" · Due: {item.due_date}" if item.due_date else ""
            st.markdown(
                f"""
                <div class="action-card">
                    {item.description}{assignee_str}{due_str}
                    <span class="priority {pclass}">{item.priority}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Full Transcript ──
    speaker_map = {s.id: s.name for s in result.speakers}
    with st.expander("📜 Full Transcript", expanded=False):
        for idx, seg in enumerate(result.segments):
            name = speaker_map.get(seg.speaker_id, seg.speaker_id)
            cidx = list(speaker_map.keys()).index(seg.speaker_id) if seg.speaker_id in speaker_map else 0
            color = SPEAKER_COLORS[cidx % len(SPEAKER_COLORS)]
            st.markdown(
                f"""
                <div class="transcript-bubble">
                    <div class="speaker-name" style="color:{color}">{name}</div>
                    <div class="text">{seg.text}</div>
                    <div class="time">{format_ms(seg.start_time)} – {format_ms(seg.end_time)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Downloads ──
    st.markdown("---")
    st.markdown('<div class="section-title">📥 Download Reports</div>', unsafe_allow_html=True)
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        st.download_button(
            "📄 Summary",
            data=build_summary_download(result),
            file_name=f"meeting_summary_{datetime.now():%Y%m%d_%H%M}.txt",
            mime="text/plain",
        )
    with dl2:
        st.download_button(
            "📜 Transcript",
            data=build_transcript_download(result),
            file_name=f"meeting_transcript_{datetime.now():%Y%m%d_%H%M}.txt",
            mime="text/plain",
        )
    with dl3:
        if result.action_items:
            action_text = "\n".join(
                f"{i}. [{a.priority.upper()}] {a.description}"
                + (f" (Assignee: {a.assignee})" if a.assignee else "")
                for i, a in enumerate(result.action_items, 1)
            )
            st.download_button(
                "✅ Action Items",
                data=action_text,
                file_name=f"action_items_{datetime.now():%Y%m%d_%H%M}.txt",
                mime="text/plain",
            )
