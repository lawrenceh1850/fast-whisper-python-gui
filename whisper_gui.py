import sys
import threading
import tempfile
import numpy as np
import wave
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt6.QtCore import pyqtSlot
import sounddevice as sd
from faster_whisper import WhisperModel

class AudioRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.is_recording = False
        self.audio_buffer = []
        self.sample_rate = 16000

        self.model_size = "large-v2"
        self.model = WhisperModel(self.model_size, compute_type="int8")

    def initUI(self):
        self.setWindowTitle('Audio Recorder')
        self.setGeometry(300, 300, 500, 500)  # x, y, width, height

        # Create layout
        layout = QVBoxLayout()

        # Create record button
        self.record_button = QPushButton('Start Recording', self)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        # Create text area
        self.transcript_text = QTextEdit(self)
        self.transcript_text.setReadOnly(True)
        layout.addWidget(self.transcript_text)
        self.transcript_text.setPlaceholderText("Transcript will appear here")

        # Set layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Add a button that will copy text in the text area to clipboard
        self.copy_button = QPushButton('Copy Transcript to Clipboard', self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_button)

        # Add a button to clear the text area
        self.clear_button = QPushButton('Reset Transcript Area', self)
        self.clear_button.clicked.connect(self.clear_text)
        layout.addWidget(self.clear_button)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.transcript_text.toPlainText())

    def clear_text(self):
        self.transcript_text.setPlaceholderText("")
        self.transcript_text.clear()

    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.setText('Start Recording')
            self.thread.join()
            self.process_recording()
            # You would also handle transcription here
        else:
            self.is_recording = True
            self.record_button.setText('Stop Recording')
            self.audio_buffer = []
            self.thread = threading.Thread(target=self.record_thread)
            self.thread.start()

    def record_thread(self):
        with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=self.audio_callback):
            while self.is_recording:
                sd.sleep(1000)

    def audio_callback(self, indata, frames, time, status):
        self.audio_buffer.extend(indata.copy())

    def process_recording(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(np.int16(np.concatenate(self.audio_buffer) * 32767))
            print(f"Recording saved to {temp_file.name}")

            # Transcribe the recording
            full_transcript = self.transcribe_recording(temp_file.name)
            # Append the transcript to the text area
            self.append_transcription(full_transcript)


    def transcribe_recording(self, audio_file):
        # The transcription now returns a tuple (segments, info)
        segments, info = self.model.transcribe(audio_file)
        # Concatenate the text from each segment to form the full transcript
        full_transcript = '\n'.join([segment.text.strip() for segment in segments])
        print("Full transcript: ", full_transcript)
        return full_transcript

    def append_transcription(self, transcript):
        self.transcript_text.append(transcript)

def main():
    app = QApplication(sys.argv)
    ex = AudioRecorder()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
