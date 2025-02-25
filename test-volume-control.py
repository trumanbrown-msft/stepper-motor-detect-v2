import usb.core
import usb.util
import pyaudio
import numpy as np
from tuning import Tuning
import logging
logging.getLogger('alsaaudio').setLevel(logging.CRITICAL)

# Initialize USB device for ReSpeaker
dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

if not dev:
    raise ValueError("ReSpeaker 4 Mic Array not found")

Mic_tuning = Tuning(dev)

def compute_rms(audio_data):
    if audio_data is None or len(audio_data) == 0:
        return 0.0
    
    # Ensure data is int16 and clamp any out-of-bounds values
    audio_data = np.clip(np.array(audio_data, dtype=np.int32), -32768, 32767)

    # Sanitize NaNs and infinities
    audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=32767, neginf=-32768)
    
    # Calculate RMS
    return np.sqrt(np.mean(np.square(audio_data)))

# Initialize PyAudio
p = pyaudio.PyAudio()

# Audio Parameters
RATE = 16000       # Sample rate
CHUNK = 1024       # Smaller chunk for real-time processing
CHANNELS = 6       # ReSpeaker has 6 channels
FORMAT = pyaudio.paInt16
THRESHOLD = 3000   # Lowered threshold to test with

# Find ReSpeaker index dynamically
def find_respeaker():
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if "ReSpeaker" in info["name"]:
            return info["index"]
    raise ValueError("ReSpeaker not found")

device_index = find_respeaker()

# Open the audio stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=device_index)

print("Listening for loud sounds...")

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        if len(data) < CHUNK * CHANNELS * 2:  # 2 bytes per sample (int16)
            print(f"Incomplete chunk received. Skipping frame.")
            continue
        
        audio_data = np.frombuffer(data, dtype=np.int16)
        audio_data = np.nan_to_num(audio_data)

        if len(audio_data) % CHANNELS != 0:
            print("Invalid chunk size; skipping frame")
            continue

        audio_data = audio_data.reshape(-1, CHANNELS)
        channel_0 = audio_data[:, 0]

        rms = compute_rms(channel_0)
        print(f"Volume: {rms:.2f}")

        if rms > THRESHOLD:
            direction = Mic_tuning.direction
            print(f"Loud sound detected! Direction: {direction}°")

except KeyboardInterrupt:
    print("Stopping...")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()