import os
import re
import random
import io
import wave
from datetime import datetime
import csv

import streamlit as st
from st_audiorec import st_audiorec  # Giữ nguyên thư viện để có visualizer
from supabase import create_client, Client
from streamlit.runtime.secrets import StreamlitSecretNotFoundError

# --- CONFIGURATION ---
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(
    page_title="Thu Thập Giọng Nói",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TRANSCRIPT DATA ---
TRANSCRIPTS_FILE = os.path.join(DATA_DIR, "transcripts.txt")


def _finalize_transcript_entry(entry):
    text = " ".join(entry.get("text_lines", [])).strip()
    text = re.sub(r"\s+", " ", text)
    total_word = entry.get("total_word") or len(re.findall(r"\S+", text))
    local_count = int(entry.get("localword", 0))
    loan_count = int(entry.get("loanword", 0))
    local_label = (entry.get("localword_label") or str(local_count)).strip()
    loan_label = (entry.get("loanword_label") or str(loan_count)).strip()
    return {
        "text": text,
        "domain": entry.get("domain", ""),
        "localword": local_count,
        "loanword": loan_count,
        "localword_label": local_label,
        "loanword_label": loan_label,
        "total_word": int(total_word),
    }


def load_transcripts_from_file(file_path):
    if not os.path.exists(file_path):
        return []
    transcripts = []
    current = None
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Transcript "):
            if current and current.get("text_lines"):
                transcripts.append(_finalize_transcript_entry(current))
            current = {
                "domain": "",
                "localword": 0,
                "loanword": 0,
                "localword_label": "",
                "loanword_label": "",
                "total_word": 0,
                "text_lines": [],
            }
            domain_match = re.search(r"Domain:\s*([^—]+)", line)
            if domain_match:
                current["domain"] = domain_match.group(1).strip()
            continue
        if line.startswith("Số từ:"):
            total_match = re.search(r"Số từ:\s*(\d+)", line)
            if total_match:
                current["total_word"] = int(total_match.group(1))
            continue
        if line.startswith("Từ địa phương:"):
            local_label_match = re.search(r"Từ địa phương:\s*([^|]+)", line)
            if local_label_match:
                current["localword_label"] = local_label_match.group(1).strip()
            local_match = re.search(r"Từ địa phương:\s*(\d+)", line)
            if local_match:
                current["localword"] = int(local_match.group(1))
            loan_label_match = re.search(r"Từ mượn/phiên âm:\s*(.+)$", line)
            if loan_label_match:
                current["loanword_label"] = loan_label_match.group(1).strip()
            loan_match = re.search(r"Từ mượn/phiên âm:\s*(\d+)", line)
            if loan_match:
                current["loanword"] = int(loan_match.group(1))
            continue
        if line.startswith("(Tỉnh:"):
            continue
        if line.lower().startswith("unknown") or ("Transcripts" in line and "Dataset" in line):
            continue
        if current is None:
            continue
        current["text_lines"].append(line)
    if current and current.get("text_lines"):
        transcripts.append(_finalize_transcript_entry(current))
    return [t for t in transcripts if t.get("text")]


TRANSCRIPTS = load_transcripts_from_file(TRANSCRIPTS_FILE)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 10px;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        text-align: center;
    }
    .instruction-text {
        text-align: center;
        color: #555;
        font-size: 1.1em;
        margin-bottom: 20px;
    }
    /* STYLE FOR THE TRANSCRIPT CARD */
    .script-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        font-size: 1.3em;
        font-weight: 500;
        color: #2c3e50;
        border: 1px solid #eee;
        margin-bottom: 10px;
        line-height: 1.6;
    }
    .script-label {
        font-size: 0.8em;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
        display: block;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def get_supabase_client() -> Client | None:
    try:
        url = st.secrets.get("SUPABASE_URL", None) if hasattr(st, "secrets") else None
        key = st.secrets.get("SUPABASE_KEY", None) if hasattr(st, "secrets") else None
    except StreamlitSecretNotFoundError:
        url = None
        key = None
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        key = os.getenv("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None


def change_script():
    """Callback to change the current script randomly"""
    if not TRANSCRIPTS:
        return
    st.session_state["current_script_data"] = random.choice(TRANSCRIPTS)


def check_name_has_accent(name):
    """Kiểm tra xem tên có dấu hoặc ký tự đặc biệt không"""
    if not name:
        return False
    # Nếu tên chứa ký tự KHÔNG phải là (a-z, A-Z, 0-9, gạch dưới, gạch ngang, khoảng trắng)
    return not bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', name))


def get_audio_duration(audio_bytes):
    """Tính độ dài file wav (giây) từ bytes"""
    try:
        with io.BytesIO(audio_bytes) as f:
            with wave.open(f, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
    except Exception:
        return 0.0


def append_metadata_row(csv_path, row):
    """Append one metadata row, create file with header if missing."""
    header = [
        "Speaker",
        "Path",
        "Transcript",
        "Duration (s)",
        "Localword",
        "Loanword",
        "Total word",
        "Field",
    ]
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# --- INITIALIZE STATE ---
if "current_script_data" not in st.session_state:
    if TRANSCRIPTS:
        st.session_state["current_script_data"] = random.choice(TRANSCRIPTS)
    else:
        st.session_state["current_script_data"] = {
            "text": "",
            "domain": "",
            "localword": 0,
            "loanword": 0,
            "localword_label": "0",
            "loanword_label": "0",
            "total_word": 0,
        }

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt & Debug")
    supabase = get_supabase_client()
    bucket = os.getenv("SUPABASE_BUCKET", "audio")

    st.divider()
    st.subheader("Trạng thái hệ thống")
    is_connected = supabase is not None

    if is_connected:
        st.success("✅ Supabase Connected")
    else:
        st.error("❌ Supabase Disconnected")

# --- MAIN INTERFACE ---
st.title("🎙️ Thu Thập Giọng Nói")
st.markdown('<p class="instruction-text">Nhập tên, đọc câu mẫu bên dưới, và ghi âm.</p>', unsafe_allow_html=True)

st.divider()
# 1. Name Input Section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    raw_name = st.text_input("👤 Nhập tên của bạn:", placeholder="Ví dụ: Nguyen Van A")

    # LOGIC CHECK TÊN (Cảnh báo nhẹ)
    if raw_name and check_name_has_accent(raw_name):
        st.warning("⚠️ Tên có dấu: Hệ thống sẽ tự động chuyển về không dấu khi lưu.")

    # Tự động tạo safe_name để dùng cho việc lưu file
    safe_name = re.sub(r"[^\w -]+", "_", raw_name, flags=re.UNICODE).strip(" _-") if raw_name else ""

st.write("")

# 2. Transcript Section (The "Script Card")
st.markdown('<span class="script-label">Mẫu câu cần đọc</span>', unsafe_allow_html=True)
current_script = st.session_state["current_script_data"]
script_text = current_script.get("text", "")
st.markdown(f"""
    <div class="script-card">
        “{script_text}”
    </div>
""", unsafe_allow_html=True)

# Button to change script (Centered)
b_col1, b_col2, b_col3 = st.columns([2, 1, 2])
with b_col2:
    st.button("🔄 Đổi câu", on_click=change_script, use_container_width=True)

st.write("---")

# 3. Recorder Section
st.write("##### ⏺️ Bảng điều khiển ghi âm")
rec_col1, rec_col2, rec_col3 = st.columns([1, 6, 1])
with rec_col2:
    # --- YÊU CẦU (1): GIỮ VISUALIZER ---
    wav_audio_data = st_audiorec()

# --- LOGIC & SAVING ---
if wav_audio_data is not None:
    # Logic 1: Kiểm tra xem đã nhập tên chưa
    if not safe_name:
        st.error("⚠️ Vui lòng nhập tên của bạn ở trên trước khi lưu file.")
        st.stop()

    # --- YÊU CẦU (2): KIỂM TRA ĐỘ DÀI < 3s ---
    duration = get_audio_duration(wav_audio_data)
    if duration < 3.0:
        st.error(f"⚠️ Bản ghi quá ngắn ({duration:.1f}s). Vui lòng đọc bình tĩnh và đầy đủ câu (tối thiểu 3s).")
        st.stop()  # Dừng tiến trình, không lưu

    # Nếu file hợp lệ, tiến hành lưu
    audio_hash = hash(wav_audio_data)
    last_hash = st.session_state.get("last_audio_hash")

    if audio_hash != last_hash:
        # --- YÊU CẦU (3): HIỆU ỨNG LOADING ---
        with st.spinner("⏳ Đang xử lý và lưu dữ liệu..."):
            now = datetime.now()
            time_part = now.strftime("%H%M%S")
            date_part = now.strftime("%d%m%Y")

            filename = f"{safe_name} - {time_part} - {date_part}.wav"

            folder_path = os.path.join(DATA_DIR, safe_name)
            os.makedirs(folder_path, exist_ok=True)
            local_path = os.path.join(folder_path, filename)
            storage_path = f"{safe_name}/{filename}"

            # Save locally
            with open(local_path, "wb") as f:
                f.write(wav_audio_data)

            # Append CSV metadata
            csv_path = os.path.join(DATA_DIR, "records.csv")
            append_metadata_row(
                csv_path,
                {
                    "Speaker": raw_name.strip(),
                    "Path": local_path,
                    "Transcript": script_text,
                    "Duration (s)": f"{duration:.2f}",
                    "Localword": current_script.get("localword_label", current_script.get("localword", 0)),
                    "Loanword": current_script.get("loanword_label", current_script.get("loanword", 0)),
                    "Total word": current_script.get("total_word", 0),
                    "Field": current_script.get("domain", ""),
                },
            )

            # Upload to Supabase
            upload_success = False
            if supabase:
                try:
                    supabase.storage.from_(bucket).upload(
                        storage_path,
                        wav_audio_data,
                        {"content-type": "audio/wav"},
                    )
                    upload_success = True
                except Exception as exc:
                    st.error(f"⚠️ Lỗi upload Supabase: {exc}")

            st.session_state["last_audio_hash"] = audio_hash

            # Thông báo thành công
            if upload_success:
                st.toast(f"✅ Đã lưu lên Cloud: {filename}", icon="☁️")
            else:
                st.toast(f"💾 Đã lưu nội bộ: {filename}", icon="💾")