import sounddevice as sd
import numpy as np
import wave
import os
from faster_whisper import WhisperModel
import threading

# see https://github.com/Vaibhavs10/insanely-fast-whisper

def record_audio(filename, sample_rate=16000):
    print("Recording... Press Enter to stop.", flush=True)

    # This function will be run in a separate thread to record audio until stopped
    def record_thread():
        with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
            while recording:
                sd.sleep(1000)

    # Callback function to continuously store audio data
    def callback(indata, frames, time, status):
        audio_buffer.extend(indata.copy())

    recording = True
    audio_buffer = []

    # Start recording in a separate thread
    thread = threading.Thread(target=record_thread)
    thread.start()

    # Wait for the user to stop the recording
    input()
    recording = False

    # Wait for the recording thread to finish
    thread.join()

    # Save the recorded audio to a file
    audio_data = np.concatenate(audio_buffer)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(np.int16(audio_data * 32767))

    print("Recording saved to", filename)

def transcribe_audio(model, audio_file):
    result = model.transcribe(audio_file)
    return result

# Initialize Whisper model
print("Initializing Whisper model...")
model_size = "large-v2"
model = WhisperModel(model_size, compute_type="int8")

# Record audio
AUDIO_FILE = "recording.wav"

# make a loop to record audio and transcribe it until user quits with control C
while True:
    # quit if user presses control C
    try:
        print("Press Enter to start recording...", flush=True)
        input()
        record_audio(AUDIO_FILE)

        # # Save the recorded audio to a file
        # save_wavefile(audio_file, np.int16(audio_data * 32767))

        # Transcribe the audio
        transcription = transcribe_audio(model, AUDIO_FILE)
        print("Transcription:")
        # the first element of the tuple transcription is a generator, print all segments from the generator
        for segment in transcription[0]:
            print(segment.text)
    except KeyboardInterrupt:
        print("Quitting...")
        break

# delete AUDIO_FILE
print("Deleting recording...")
os.remove(AUDIO_FILE)