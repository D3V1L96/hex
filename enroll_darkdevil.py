import sounddevice as sd
import soundfile as sf

def record_master_voice(filename="darkdevil_sample.wav", duration=5, fs=16000):
    print(f"Please speak clearly for {duration} seconds to record your master voice sample.")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, recording, fs)
    print(f"Master voice sample saved as '{filename}'.")

if __name__ == "__main__":
    record_master_voice()
