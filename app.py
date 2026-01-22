import os
import re
from datetime import datetime

import streamlit as st
from st_audiorec import st_audiorec
from supabase import create_client, Client
from streamlit.runtime.secrets import StreamlitSecretNotFoundError

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)

st.set_page_config(page_title="Thu thap giong noi", layout="centered")

st.title("Thu thap giong noi")
st.write("Bam nut ghi am de bat dau, sau do dung lai de luu .wav.")

raw_name = st.text_input("Nhap ten cua ban de gan vao file ghi am")
safe_name = re.sub(r"[^\w -]+", "_", raw_name, flags=re.UNICODE).strip(" _-")

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

supabase = get_supabase_client()
bucket = os.getenv("SUPABASE_BUCKET", "audio")

wav_audio_data = st_audiorec()

if wav_audio_data:
    if not safe_name:
        st.warning("Vui long nhap ten truoc khi luu ghi am.")
        st.stop()

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

        with open(local_path, "wb") as f:
            f.write(wav_audio_data)

        if supabase:
            try:
                supabase.storage.from_(bucket).upload(
                    storage_path,
                    wav_audio_data,
                    {"content-type": "audio/wav"},
                )
                st.success(f"Da luu len Supabase: {storage_path}")
            except Exception as exc:
                st.error(f"Khong the upload len Supabase: {exc}")

        st.session_state["last_audio_hash"] = audio_hash
        st.success(f"Da luu: {filename}")

    st.audio(wav_audio_data, format="audio/wav")
