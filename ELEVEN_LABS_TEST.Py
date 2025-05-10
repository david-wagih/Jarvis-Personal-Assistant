import os
import wave
import openai
import pyaudio
import audioop
import numpy as np
import noisereduce as nr
from scipy.signal import butter, lfilter
from tempfile import NamedTemporaryFile
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from dotenv import load_dotenv

# === CONFIG ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
THRESHOLD = 400
SILENCE_CHUNKS = 80
MAX_RECORD_SECONDS = 10

# === Audio Filters ===
def bandpass_filter(audio_np, lowcut=300, highcut=3400, fs=RATE, order=6):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, audio_np)

def speak(text):
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)

def record_until_silence(threshold=THRESHOLD, silence_chunks=SILENCE_CHUNKS, max_seconds=MAX_RECORD_SECONDS):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)
    print("🎤 Speak now...")

    frames = []
    silent_chunk_count = 0
    started = False
    max_chunks = int(RATE / CHUNK * max_seconds)
    min_record_chunks = int(1.5 * RATE / CHUNK)

    for i in range(max_chunks):
        data = stream.read(CHUNK)
        audio_np = np.frombuffer(data, dtype=np.int16)
        filtered_np = bandpass_filter(audio_np)
        filtered_bytes = filtered_np.astype(np.int16).tobytes()
        rms = audioop.rms(filtered_bytes, 2)

        if rms > threshold:
            if not started:
                print("🎙️ Detected speech...")
            started = True
            frames.append(data)
            silent_chunk_count = 0
        elif started:
            frames.append(data)
            silent_chunk_count += 1
            if silent_chunk_count > silence_chunks and i > min_record_chunks:
                print("🔇 Detected silence.")
                break

    stream.stop_stream()
    stream.close()
    p.terminate()

    return b''.join(frames)

def reduce_noise(audio_bytes):
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    reduced = nr.reduce_noise(y=audio_np, sr=RATE)
    return reduced.astype(np.int16).tobytes()

def pad_audio(audio_bytes, padding_ms=300):
    pad = b'\0' * int(RATE * 2 * padding_ms / 1000)
    return pad + audio_bytes + pad

def save_wav(audio_bytes, rate=RATE):
    with NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wf = wave.open(f.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(audio_bytes)
        wf.close()
        return f.name

def transcribe_with_openai(wav_path):
    print("📤 Sending audio to Whisper API...")
    with open(wav_path, "rb") as audio_file:
        response = openai.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language=None
        )
    return response.text

def listen():
    audio = record_until_silence()
    if not audio:
        print("🤖 Didn't catch anything.")
        return ""

    audio = reduce_noise(audio)
    audio = pad_audio(audio)

    wav_path = save_wav(audio)
    text = transcribe_with_openai(wav_path).strip()
    os.remove(wav_path)
    print(f"🗣️ You said: {text}")
    return text

def ask_gpt(prompt):
    print("🤖 Thinking...")
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    return response.choices[0].message.content.strip()[:100]

# === Main Loop ===
while True:
    user_input = listen()
    if not user_input:
        continue

    if user_input.lower() in ["exit", "quit", "stop"]:
        speak("Goodbye!")
        break

    response = ask_gpt(user_input)
    print(f"🤖 GPT: {response}")
    speak(response)
