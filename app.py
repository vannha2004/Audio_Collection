import os
import re
import random
from datetime import datetime

import streamlit as st
from st_audiorec import st_audiorec
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
TRANSCRIPTS = [
    "Trần Quốc Toản sinh năm 1267, là con trai của Trung Thành vương.",
    "Sử liệu không ghi rõ Trung Thành vương có tên thật là gì), nên được phong là Hoài Văn hầu.",
    "Trước khi Hoài Văn hầu chào đời 10 năm, quân, dân Đại Việt đã khiến giặc Nguyên Mông thua tan tác.",
    "Điều này càng khiến Hốt Tất Liệt nung nấu quyết tâm thôn tính Đại Việt.",
    "Ta là Hoài Văn hầu, quan gia truyền gọi tất cả vương, hầu tới họp. Ta là hầu, cớ sao không cho vào?",
    "Vua thấy Hoài Văn Hầu Trần Quốc Toản, Hoài Nhân Vương Kiện đều còn trẻ tuổi, không cho dự bàn.",
    "Quốc Toản trong lòng hổ thẹn, phẫn kích, tay cầm quả cam, bóp nát lúc nào không biết.",
    "Trở về từ Hội nghị Bình Than, Hoài Văn hầu vẫn quyết tâm tìm cách đánh giặc cứu nước.",
    "Trần Quốc Toản còn cho thêu trên một lá cờ lớn 6 chữ vàng: “Phá cường địch, báo hoàng ân”.",
    "Cuối tháng 2 năm 1285, quân Nguyên Mông ồ ạt tấn công Đại Việt.",
    "khi đối trận với giặc, (Hoài Văn hầu) tự mình xông lên trước quân sĩ, giặc trông thấy phải lui tránh, không dám đối địch.",
    "Chàng thiếu niên dũng mãnh Trần Quốc Toản quyết truy đuổi tới cùng.",
    "trong lúc truy đuổi, Hoài Văn hầu Trần Quốc Toản không may hy sinh.",
    "Nhận được tin Hoài Văn hầu tử trận, Trần Nhân Tông rất đỗi thương tiếc.",
    "Khi đất nước sạch bóng giặc, nhà vua cử hành tang lễ rất trọng thể.",
    "Vua đích thân làm văn tế và truy tặng Trần Quốc Toản tước Hoài Văn vương."
]

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
        font-size: 1.3em; /* Larger font for reading */
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
    st.session_state["current_script"] = random.choice(TRANSCRIPTS)

# --- INITIALIZE STATE ---
if "current_script" not in st.session_state:
    st.session_state["current_script"] = random.choice(TRANSCRIPTS)

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
    safe_name = re.sub(r"[^\w -]+", "_", raw_name, flags=re.UNICODE).strip(" _-")

st.write("") # Spacer

# 2. Transcript Section (The "Script Card")
st.markdown('<span class="script-label">Mẫu câu cần đọc</span>', unsafe_allow_html=True)
st.markdown(f"""
    <div class="script-card">
        “{st.session_state['current_script']}”
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
    wav_audio_data = st_audiorec()

# --- LOGIC & SAVING ---
if wav_audio_data:
    if not safe_name:
        st.error("⚠️ Vui lòng nhập tên của bạn ở trên trước khi lưu file.")
        st.stop()

    audio_hash = hash(wav_audio_data)
    last_hash = st.session_state.get("last_audio_hash")

    if audio_hash != last_hash:
        now = datetime.now()
        time_part = now.strftime("%H%M%S")
        date_part = now.strftime("%d%m%Y")
        
        # Include a snippet of text in filename? (Optional, kept simple for now)
        filename = f"{safe_name} - {time_part} - {date_part}.wav"
        
        folder_path = os.path.join(DATA_DIR, safe_name)
        os.makedirs(folder_path, exist_ok=True)
        local_path = os.path.join(folder_path, filename)
        storage_path = f"{safe_name}/{filename}"

        # Save locally
        with open(local_path, "wb") as f:
            f.write(wav_audio_data)

        # Upload to Supabase
        upload_success = False
        if supabase:
            try:
                # Add metadata about which text was read? (Optional feature)
                supabase.storage.from_(bucket).upload(
                    storage_path,
                    wav_audio_data,
                    {"content-type": "audio/wav"},
                )
                upload_success = True
            except Exception as exc:
                st.error(f"⚠️ Lỗi upload Supabase: {exc}")

        st.session_state["last_audio_hash"] = audio_hash
        
        if upload_success:
            st.toast(f"✅ Đã lưu lên Cloud: {filename}", icon="☁️")
        else:
            st.toast(f"💾 Đã lưu nội bộ: {filename}", icon="💾")