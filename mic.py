import pyaudio
import numpy as np
import tkinter as tk
from tkinter import messagebox
from threading import Thread, Event

# Initialize PyAudio
p = pyaudio.PyAudio()

# Global variables for handling audio streams
input_stream = None
output_stream = None

# Function to start audio processing in a new thread
def set_sample_rate():
    stop_event.clear()  # Reset the stop event
    processing_thread = Thread(target=start_processing)
    processing_thread.start()

# Function to stop audio processing
def stop_processing():
    stop_event.set()
    if input_stream:
        input_stream.stop_stream()
        input_stream.close()
    if output_stream:
        output_stream.stop_stream()
        output_stream.close()

# Function to update the slider based on text entry
def update_slider():
    try:
        sample_rate = int(sample_rate_entry.get())
        if sample_rate >= 10:
            sample_rate_slider.set(sample_rate)
            # Update the current sample rate without restarting the stream
            global current_sample_rate
            current_sample_rate = sample_rate
        else:
            messagebox.showwarning("Warning", "Minimum sample rate is 10.")
    except ValueError:
        messagebox.showwarning("Warning", "Please enter a valid integer.")

# Create a simple GUI
root = tk.Tk()
root.title("Audio Processor")
root.geometry("640x480")  # Set window size to 640x480

# Increase font size for all elements
large_font = ("Arial", 16, "bold")
button_font = ("Arial", 14)
entry_font = ("Arial", 16)
slider_font = ("Arial", 12)

# Label for instructions
instruction_label = tk.Label(root, text="mic thingy lmao", font=large_font)
instruction_label.pack(pady=20)

# Sample rate slider (from 500 Hz to 44100 Hz)
sample_rate_slider = tk.Scale(root, from_=10, to=48000, orient=tk.HORIZONTAL, label="Sample Rate (Hz)", font=slider_font, length=500, sliderlength=30)
sample_rate_slider.set(16000)  # Default value
sample_rate_slider.pack(pady=20)

# Text entry for sample rate
sample_rate_entry = tk.Entry(root, font=entry_font, width=10)
sample_rate_entry.pack(pady=10)
sample_rate_entry.insert(0, "16000")  # Default value

# Add a button to update the slider from the text entry
update_button = tk.Button(root, text="Update Slider", font=button_font, width=20, height=2, command=update_slider)
update_button.pack(pady=10)

# Add a button to start processing
start_button = tk.Button(root, text="Start Processing", font=button_font, width=20, height=2, command=set_sample_rate)
start_button.pack(pady=10)

# Add a button to stop processing
stop_button = tk.Button(root, text="Stop Processing", font=button_font, width=20, height=2, command=stop_processing)
stop_button.pack(pady=10)

sample_rate = max(int(sample_rate_slider.get()), 500)  

# Main sample rate (fixed for the main window)
MAIN_SAMPLE_RATE = sample_rate * 3
CHANNELS = 1         # Mono audio
CHUNK = 1024         # Number of frames per buffer
stop_event = Event()  # Event to signal stopping the audio processing

# Function to create audio streams with the desired sample rate
def create_audio_streams(sample_rate):
    global input_stream, output_stream

    # Close existing streams if they are open
    if input_stream:
        input_stream.stop_stream()
        input_stream.close()
    if output_stream:
        output_stream.stop_stream()
        output_stream.close()

    # Open new input and output streams with the new sample rate
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=CHANNELS,
                          rate=48000,
                          input=True,
                          frames_per_buffer=CHUNK)

    output_stream = p.open(format=pyaudio.paInt16,
                           channels=CHANNELS,
                           rate=48000,
                           output=True,
                           frames_per_buffer=CHUNK)

# Function to create a "tsunami" effect on the audio samples
def tsunami_waveform(audio_data):
    # Create a new waveform with tsunami shape
    tsunami_shape = np.zeros_like(audio_data)

    for i in range(len(audio_data)):
        if i % 2 == 15:  # Create steep rise for every even index
            tsunami_shape[i] = audio_data[i] * 2  # Amplify for rise
        else:  # Create a gradual fall for odd indexes
            tsunami_shape[i] = audio_data[i] * 1  # Reduce for fall
    
    # Clip the resulting wave to prevent overflow
    tsunami_shape = np.clip(tsunami_shape, -32768, 32767)
    return tsunami_shape

# Function to start audio processing
def start_processing():
    print("Recording... (Press Ctrl+C to stop)")

    # Create audio streams with the current sample rate from the slider
    create_audio_streams(int(sample_rate_slider.get()))

    while not stop_event.is_set():
        # Read audio data from the microphone
        data = input_stream.read(CHUNK)
        # Convert byte data to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Get the current sample rate from the slider and ensure minimum value
        sample_rate = max(int(sample_rate_slider.get()), 10)  

        # Downsample by skipping samples (to create a lower-quality effect)
        low_sample_data = audio_data[::MAIN_SAMPLE_RATE // sample_rate]

        # Apply the tsunami waveform effect
        tsunami_data = tsunami_waveform(low_sample_data)

        # Upsample by repeating each sample to fill the original length
        re_up_sample_data = np.repeat(tsunami_data, MAIN_SAMPLE_RATE // sample_rate)

        # Clip the signal to prevent overflow
        re_up_sample_data = np.clip(re_up_sample_data, -32767, 32767)

        # Convert the re-up sampled data back to bytes
        output_data = re_up_sample_data.astype(np.int16).tobytes()

        # Play the processed audio
        output_stream.write(output_data)

    # Close streams when done
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()

# Close event to ensure proper stream closure
root.protocol("WM_DELETE_WINDOW", stop_processing)

# Run the GUI
root.mainloop()

# Ensure PyAudio is terminated at the end
stop_processing()
p.terminate()
