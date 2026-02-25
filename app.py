import os
import re
import random
import io
import wave
import threading
import json                          # NEW
from datetime import datetime, timezone  # NEW: thêm timezone

import streamlit as st
from st_audiorec import st_audiorec # Giữ nguyên thư viện để có visualizer
from supabase import create_client, Client
from streamlit.runtime.secrets import StreamlitSecretNotFoundError

# --- CONFIGURATION ---
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
MIN_RECORD_SECONDS = 35.0
TRANSCRIPT_BUCKET = os.getenv("SUPABASE_TRANSCRIPT_BUCKET", "transcripts")  # NEW

st.set_page_config(
    page_title="Thu Thập Giọng Nói",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TRANSCRIPT DATA ---
TRANSCRIPTS = [
    "Trần Quốc Toản sinh năm 1267, là con trai của Trung Thành vương. Sử liệu không ghi rõ Trung Thành vương có tên thật là gì, nên được phong là Hoài Văn hầu. Trước khi Hoài Văn hầu chào đời 10 năm, quân, dân Đại Việt đã khiến giặc Nguyên Mông thua tan tác. Điều này càng khiến Hốt Tất Liệt nung nấu quyết tâm thôn tính Đại Việt. Ta là Hoài Văn hầu, quan gia truyền gọi tất cả vương, hầu tới họp. Ta là hầu, cớ sao không cho vào? Giặc Nguyên cho sứ thần sang giả vờ mượn đường để xâm chiếm nước ta. Thấy sứ giặc ngang ngược đủ điều, Trần Quốc Toản vô cùng căm giận bèn nảy ra ý định đánh giặc cứu nước.Thấy chuyện ầm ĩ bên ngoài, Trần Nhân Tông hỏi ra mới biết chuyện, bèn cho người mang ban cho Hoài Văn hầu một quả cam và khuyên Hoài Văn hầu lui bước vì chưa đến tuổi bàn việc nước. ",
    "Vua thấy Hoài Văn Hầu Trần Quốc Toản, Hoài Nhân Vương Kiện đều còn trẻ tuổi, không cho dự bàn. Quốc Toản trong lòng hổ thẹn, phẫn kích, tay cầm quả cam, bóp nát lúc nào không biết. Trở về từ Hội nghị Bình Than, Hoài Văn hầu vẫn quyết tâm tìm cách đánh giặc cứu nước. Trần Quốc Toản còn cho thêu trên một lá cờ lớn 6 chữ vàng: “Phá cường địch, báo hoàng ân. Trần Quốc Toản đã trở thành tấm gương sáng ngời về ý chí và lòng yêu nước để các thế hệ trẻ Việt Nam noi theo. Tên của ông được đặt cho nhiều trường Tiểu học, Trung học ở nước ta và một số con đường của các tỉnh, thành phố trong đó có Bắc Ninh. Trần Nhân Tông chuẩn y mưu kế lập vườn không nhà trống, rút toàn bộ khỏi thành Thăng Long, nhà vua đã cho Hoài Văn hầu đi theo hộ giá vào Thanh Hóa.",
    "Cuối tháng 2 năm 1285, quân Nguyên Mông ồ ạt tấn công Đại Việt. Khi đối trận với giặc, Hoài Văn hầu tự mình xông lên trước quân sĩ, giặc trông thấy phải lui tránh. Chàng thiếu niên dũng mãnh Trần Quốc Toản quyết truy đuổi tới cùng. Trong lúc truy đuổi, Hoài Văn hầu Trần Quốc Toản không may hy sinh. Sau này, khi đối trận với giặc, tự mình xông lên trước quân sĩ, giặc trông thấy phải lui tránh, không dám đối địch. Đến khi mất, vua rất thương tiếc, thân làm văn tế, lại gia phong tước vương. Mới 15 tuổi, tính theo “tuổi ta” là 16, nhưng chàng thiếu niên này đã hừng hực chí lớn muốn diệt giặc bạo tàn, bảo vệ sự toàn vẹn cho non sông nước Việt. Tuy tử trận, nhưng Trần Quốc Toản đã góp công không nhỏ trong sự thành công của cuộc tổng phản công của quân đội triều đình, quét sạch bóng xâm lăng chỉ trong vòng khoảng 2 chục ngày đêm.",
    "Nhận được tin Hoài Văn hầu tử trận, Trần Nhân Tông rất đỗi thương tiếc. Khi đất nước sạch bóng giặc, nhà vua cử hành tang lễ rất trọng thể. Vua đích thân làm văn tế và truy tặng Trần Quốc Toản tước Hoài Văn vương. Điều này càng khiến Hốt Tất Liệt nung nấu quyết tâm thôn tính Đại Việt. Ta là Hoài Văn hầu, quan gia truyền gọi tất cả vương, hầu tới họp. Ta là hầu, cớ sao không cho vào? Trong các sử sách của Việt Nam như Khâm định Việt sử Thông giám Cương mục, Việt sử Tiêu án và các quyển sử soạn gần đây như Việt sử Tân biên của Phạm Văn Sơn, Việt Nam sử lược của Trần Trọng Kim, Trần Hưng Đạo của Hoàng Thúc Trâm đều không thấy đề cập đến cái chết của Hoài Văn Hầu Trần Quốc Toản. Chỉ có ĐVSKTT bản kỷ quyển V có viết: Nhưng các quyển sử của nhà Nguyên lại có đề cập đến cái chết của ông. An Nam truyện của Nguyên sử 209 tờ 8a10 có ghi: Quan quân đến sông Như Nguyệt, thì Nhật Huyên sai Hoài Văn Hầu đến đánh... Kinh thế đại điển tự lục trong Nguyên văn loại 41 tờ"
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
    st.session_state["current_script"] = random.choice(TRANSCRIPTS)

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

def upload_to_supabase_background(
    supabase_client: Client,
    bucket_name: str,
    storage_path: str,
    audio_bytes: bytes,
) -> None:
    """Upload audio to Supabase in a background thread to reduce UI wait time."""
    try:
        supabase_client.storage.from_(bucket_name).upload(
            storage_path,
            audio_bytes,
            {"content-type": "audio/wav"},
        )
    except Exception as exc:
        # Avoid calling Streamlit APIs from background threads.
        print(f"[Supabase upload error] {storage_path}: {exc}")


# NEW: Upload JSON transcript lên Supabase Storage
def upload_json_to_supabase(
    supabase_client: Client,
    transcript_bucket: str,
    file_name: str,
    transcript_text: str,
    created_at: str,
) -> tuple[bool, str]:
    """
    Tạo file JSON chứa thông tin transcript và upload lên Supabase.
    Trả về (success: bool, message: str).
    """
    try:
        # Tạo payload JSON
        payload = {
            "file_name": file_name,
            "transcript": transcript_text,
            "created_at": created_at,
        }
        json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

        # Tên file JSON tương ứng với file audio (chỉ đổi đuôi)
        json_filename = file_name.replace(".wav", ".json")
        # Lưu cùng cấu trúc thư mục với audio
        speaker_folder = file_name.split(" - ")[0] if " - " in file_name else "unknown"
        json_storage_path = f"{speaker_folder}/{json_filename}"

        # Kiểm tra bucket tồn tại
        buckets = [b.name for b in supabase_client.storage.list_buckets()]
        if transcript_bucket not in buckets:
            return False, f"Bucket '{transcript_bucket}' không tồn tại trên Supabase."

        supabase_client.storage.from_(transcript_bucket).upload(
            json_storage_path,
            json_bytes,
            {"content-type": "application/json"},
        )
        return True, f"Transcript JSON đã upload: {json_storage_path}"
    except Exception as exc:
        return False, f"Lỗi upload JSON: {exc}"

# --- INITIALIZE STATE ---
if "current_script" not in st.session_state:
    st.session_state["current_script"] = random.choice(TRANSCRIPTS)
if "record_locked" not in st.session_state:
    st.session_state["record_locked"] = False

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
st.markdown(f"""
    <div class="script-card">
        “{st.session_state['current_script']}”
    </div>
""", unsafe_allow_html=True)

# Button to change script (Centered)
b_col1, b_col2, b_col3 = st.columns([2, 1, 2])
with b_col2:
    st.button(
        "🔄 Đổi câu",
        on_click=change_script,
        use_container_width=True,
        disabled=st.session_state.get("record_locked", False),
    )

st.write("---")

# 3. Recorder Section
st.write("##### ⏺️ Bảng điều khiển ghi âm")
rec_col1, rec_col2, rec_col3 = st.columns([1, 6, 1])
with rec_col2:
    # --- YÊU CẦU (1): GIỮ VISUALIZER ---
    if st.session_state.get("record_locked", False):
        st.success("✅ Bạn đã hoàn thành ghi âm. Chỉ cần ghi 1 lần duy nhất.")
        wav_audio_data = None
    else:
        wav_audio_data = st_audiorec()

# --- LOGIC & SAVING ---
if wav_audio_data is not None:
    # Logic 1: Kiểm tra xem đã nhập tên chưa
    if not safe_name:
        st.error("⚠️ Vui lòng nhập tên của bạn ở trên trước khi lưu file.")
        st.stop()
        
    # --- YÊU CẦU (2): KIỂM TRA ĐỘ DÀI TỐI THIỂU ---
    duration = get_audio_duration(wav_audio_data)
    st.caption(f"⏱️ Thời gian đã ghi: {duration:.1f} giây")
    if duration < MIN_RECORD_SECONDS:
        st.error(
            f"⚠️ Bản ghi chưa đủ dài ({duration:.1f}s). "
            f"Vui lòng ghi ít nhất {MIN_RECORD_SECONDS:.0f} giây."
        )
        st.stop()  # Dừng tiến trình, không lưu

    # Nếu file hợp lệ, tiến hành lưu
    audio_hash = hash(wav_audio_data)
    last_hash = st.session_state.get("last_audio_hash")

    if audio_hash != last_hash:
        now = datetime.now()
        time_part = now.strftime("%H%M%S")
        date_part = now.strftime("%d%m%Y")

        filename = f"{safe_name} - {time_part} - {date_part}.wav"

        folder_path = os.path.join(DATA_DIR, safe_name)
        os.makedirs(folder_path, exist_ok=True)
        local_path = os.path.join(folder_path, filename)
        storage_path = f"{safe_name}/{filename}"

        # Save locally first (fast) so the user does not wait on network.
        with open(local_path, "wb") as f:
            f.write(wav_audio_data)

        st.session_state["last_audio_hash"] = audio_hash
        st.session_state["record_locked"] = True

        # NEW: Timestamp ISO format (UTC)
        created_at = datetime.now(timezone.utc).isoformat()
        current_transcript = st.session_state.get("current_script", "")

        # Upload to Supabase (audio + JSON transcript)
        if supabase:
            # NEW: Spinner thông báo đang lưu
            with st.spinner("☁️ Đang lưu audio và transcript lên Cloud, vui lòng chờ..."):
                # --- Upload Audio (chạy ngầm không block UI lâu) ---
                audio_thread = threading.Thread(
                    target=upload_to_supabase_background,
                    args=(supabase, bucket, storage_path, wav_audio_data),
                    daemon=True,
                )
                audio_thread.start()
                audio_thread.join(timeout=30)  # NEW: chờ tối đa 30s

                # NEW: Upload JSON transcript
                json_ok, json_msg = upload_json_to_supabase(
                    supabase_client=supabase,
                    transcript_bucket=TRANSCRIPT_BUCKET,
                    file_name=filename,
                    transcript_text=current_transcript,
                    created_at=created_at,
                )

            # NEW: Hiển thị kết quả
            st.success(f"✅ Đã lưu audio nội bộ và upload lên Cloud: `{filename}`")
            if json_ok:
                st.success(f"✅ {json_msg}")
            else:
                st.error(f"❌ {json_msg}")
        else:
            st.toast(f"💾 Đã lưu nội bộ: {filename}", icon="💾")
            st.warning("⚠️ Chưa kết nối Supabase — transcript JSON chưa được upload.")
