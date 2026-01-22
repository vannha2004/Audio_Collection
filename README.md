---
title: Audio Collection
emoji: 🌍
colorFrom: gray
colorTo: green
sdk: docker
pinned: false
license: apache-2.0
short_description: Collecting data from students
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# Voice Collection (Streamlit)

Minimal web UI to record voice and store .wav files.
File naming format: `ten - hhmmss - ddmmyyyy.wav`.

## Run locally

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Docker

```
docker build -t voice-collect .
docker run --rm -p 8501:8501 -v ${PWD}/data:/data voice-collect
```

Recorded .wav files are stored in `data/` (or `/data` in container).

## Free deploy (Hugging Face Spaces - Docker)

1. Create a free Space: https://huggingface.co/spaces (choose "Docker").
2. Push this repo to your GitHub.
3. In the Space settings, connect the GitHub repo.
4. The Space will build the Dockerfile automatically and host the app.

Note: Free Spaces use ephemeral storage; recordings may reset on rebuilds.
