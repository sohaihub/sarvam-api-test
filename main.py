import streamlit as st
import requests
import base64
import io
import wave

API_KEY = "sk_v4ka9u7i_b869GOmkZ5PdM5M6JR1GyZHw"
API_URL = "https://api.sarvam.ai/text-to-speech"
MAX_CHARS = 100  # strict limit to prevent missing characters


def chunk_text(text, size):
    """Ensure exact character split without skipping."""
    text = text.strip()
    chunks = []
    while text:
        chunk = text[:size]
        chunks.append(chunk)
        text = text[size:]
    return chunks


def call_sarvam_tts(text_chunk, lang_code, speaker):
    headers = {
        "api-subscription-key": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text_chunk.strip(),
        "target_language_code": lang_code,
        "speaker": speaker,
        "model": "bulbul:v1"
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['audios'][0]


def merge_wav_base64(audio_base64_list):
    wav_buffers = []
    params = None
    for b64 in audio_base64_list:
        wav_bytes = base64.b64decode(b64)
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, 'rb') as w:
            if params is None:
                params = w.getparams()
            frames = w.readframes(w.getnframes())
            wav_buffers.append(frames)

    merged_frames = b"".join(wav_buffers)
    output_buffer = io.BytesIO()
    with wave.open(output_buffer, 'wb') as w_out:
        w_out.setparams(params)
        w_out.writeframes(merged_frames)

    return output_buffer.getvalue()


def main():
    st.title("🗣️ Sarvam TTS - Long Text to Speech")

    text = st.text_area("Enter your text (any language):", height=200)

    lang_option = st.selectbox("Select Language", ["English", "Tamil", "Hindi"])
    lang_map = {
    "English": ("en-IN", "meera"),
    "Tamil": ("ta-IN", "pavithra"),  # supports Tamil
    "Hindi": ("hi-IN", "vidya")      # supports Hindi
}

    lang_code, speaker = lang_map[lang_option]

    if st.button("Generate Audio"):
        if not text.strip():
            st.error("Please enter some text.")
            return

        chunks = chunk_text(text, MAX_CHARS)
        st.info(f"Text split into {len(chunks)} chunk(s).")

        audio_chunks = []
        for i, chunk in enumerate(chunks, 1):
            try:
                st.write(f"Processing chunk {i}/{len(chunks)}...")
                audio_b64 = call_sarvam_tts(chunk, lang_code, speaker)
                audio_chunks.append(audio_b64)
            except requests.HTTPError as e:
                st.error(f"Error on chunk {i}: {e.response.text}")
                return

        merged_audio = merge_wav_base64(audio_chunks)
        st.success("✅ Audio generated and merged successfully!")

        st.audio(merged_audio, format="audio/wav")
        st.download_button("📥 Download Audio", merged_audio, file_name="tts_audio.wav", mime="audio/wav")


if __name__ == "__main__":
    main()
