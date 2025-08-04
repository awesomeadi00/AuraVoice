"""Module for the machine learning client."""
import subprocess
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

# Audio processing libraries
import librosa
import soundfile as sf
import numpy as np

# Web framework
from flask import Flask, request, jsonify
from flask_cors import CORS

# Machine learning and MIDI
import crepe
import pretty_midi

# AWS and database
import boto3
from botocore.exceptions import NoCredentialsError
from pymongo import MongoClient
from bson import ObjectId

# Utilities
from dotenv import load_dotenv

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize Flask app
app = Flask(__name__)
load_dotenv()
logging.basicConfig(level=logging.INFO)
CORS(app)

# AWS S3 Configuration
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)

# MongoDB Configuration
client = MongoClient("database", 27017)
db = client["auravoice"]
collection = db["midis"]

# Container configuration
HOST = "client"

# =============================================================================
# AUDIO PROCESSING FUNCTIONS
# =============================================================================

def convert_webm_to_wav(webm_file: str, wav_file: str) -> None:
    """Convert WebM audio file to WAV format."""
    result = subprocess.run(
        ["ffmpeg", "-i", webm_file, wav_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        print("ffmpeg error:", result.stderr.decode())
        raise ValueError("Error converting WebM to WAV")


def write_audio_to_file(file_name: str, audio_stream) -> None:
    """Write audio stream to file."""
    with open(file_name, "wb") as file:
        file.write(audio_stream.read())


def clean_up_files(webm_file: str, wav_file: str) -> None:
    """Remove temporary audio files."""
    os.remove(webm_file)
    os.remove(wav_file)


def calculate_amplitude_envelope(y: np.ndarray, frame_size: int = 1024, hop_length: int = 512) -> np.ndarray:
    """Calculate amplitude envelope of an audio signal using RMS."""
    amplitude_envelope = []
    for i in range(0, len(y), hop_length):
        frame = y[i : i + frame_size]
        rms = np.sqrt(np.mean(frame**2))
        amplitude_envelope.append(rms)
    return np.array(amplitude_envelope)


# =============================================================================
# PITCH DETECTION AND NOTE PROCESSING
# =============================================================================

def frequency_to_note_name(frequency: float) -> Optional[str]:
    """Convert a frequency in Hertz to a musical note name."""
    if frequency <= 0:
        return None
    # Convert numpy scalar to Python float if needed
    if hasattr(frequency, 'item'):
        frequency = frequency.item()
    frequency = float(frequency)
    note_number = pretty_midi.hz_to_note_number(frequency)
    return pretty_midi.note_number_to_name(int(note_number))


def process_audio_chunks(audio: np.ndarray, sr: int) -> List[Dict[str, Any]]:
    """Process audio data in chunks and return notes data."""
    confidence_threshold = 0.74
    chunk_size = 1024 * 10
    notes_data = []

    for start in range(0, len(audio), chunk_size):
        audio_chunk = audio[start : (start + chunk_size)]
        time, frequency, confidence, _ = crepe.predict(audio_chunk, sr, viterbi=True)

        for t, f, c in zip(time, frequency, confidence):
            if c >= confidence_threshold:
                note_name = frequency_to_note_name(f)
                if note_name:
                    notes_data.append({
                        "time": float(t),
                        "note": note_name,
                        "confidence": round(float(c), 2),  # Convert numpy scalar to Python float
                    })
    
    print(notes_data)
    return notes_data


def sort_notes_data(notes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort notes data by time."""
    return sorted(notes_data, key=lambda x: x["time"])


def smooth_pitch_data(notes_data: List[Dict[str, Any]], window_size: int = 5) -> List[Dict[str, Any]]:
    """Smooth pitch data using a sliding window approach."""
    smoothed_data = []
    for i in range(len(notes_data)):
        start = max(i - window_size // 2, 0)
        end = min(i + window_size // 2 + 1, len(notes_data))
        window = notes_data[start:end]

        avg_time = sum(note["time"] for note in window) / len(window)
        note_counts = {}
        for note in window:
            note_counts[note["note"]] = note_counts.get(note["note"], 0) + 1
        avg_note = max(note_counts, key=note_counts.get)

        smoothed_data.append({"time": avg_time, "note": avg_note})
    return smoothed_data


def filter_and_combine_notes(notes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and combine consecutive notes of the same type."""
    filtered_notes = []
    last_note = None

    for note in notes_data:
        if last_note is not None and note["note"] != last_note:
            filtered_notes.append({"note": last_note})
            last_note = note["note"]
        elif last_note is None:
            last_note = note["note"]

    if last_note is not None:
        filtered_notes.append({"note": last_note})

    logging.info("Filtered notes: %s", filtered_notes)
    return filtered_notes


def process_notes(notes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process notes through smoothing and filtering."""
    smoothed_notes = smooth_pitch_data(notes_data)
    return filter_and_combine_notes(smoothed_notes)


# =============================================================================
# TEMPO AND TIMING ANALYSIS
# =============================================================================

def detect_note_onsets(audio_file: str) -> np.ndarray:
    """Detect when notes begin (onsets)."""
    y, _ = librosa.load(audio_file, sr=44100)
    onsets = librosa.onset.onset_detect(y=y, sr=44100, units="time")
    logging.info("onsets: %s", onsets)
    return onsets


def estimate_note_durations(onsets: np.ndarray, y: np.ndarray, sr: int = 44100, threshold: float = 0.025) -> List[float]:
    """Estimate note durations using onsets and amplitude envelope."""
    amp_env = calculate_amplitude_envelope(y, sr)
    min_duration = 0.05
    durations = []

    # Process all onsets except the last one
    for i, onset in enumerate(onsets[:-1]):
        onset_sample = int(onset * sr)
        next_onset_sample = int(onsets[i + 1] * sr)

        end_sample = next_onset_sample
        for j in range(onset_sample, next_onset_sample, 512):
            if amp_env[j // 512] < threshold:
                end_sample = j
                break

        duration = max((end_sample - onset_sample) / sr, min_duration)
        durations.append(duration)

    # Handle the last onset separately
    if len(onsets) > 0:
        last_onset_sample = int(onsets[-1] * sr)
        end_sample = len(y)
        for j in range(last_onset_sample, end_sample, 512):
            if amp_env[j // 512] < threshold:
                end_sample = j
                break

        duration = max((end_sample - last_onset_sample) / sr, min_duration)
        durations.append(duration)

    logging.info("durations: %s", durations)
    return durations


def estimate_tempo(audio_file: str) -> float:
    """Estimate tempo for better time mapping."""
    y, sr = librosa.load(audio_file, sr=44100)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # Convert numpy array to scalar if needed
    if hasattr(tempo, 'item'):
        tempo = tempo.item()
    # Ensure tempo is a Python native float
    tempo = float(tempo)
    logging.info("tempo: %s", tempo)
    return tempo


# =============================================================================
# MIDI GENERATION
# =============================================================================

def create_midi_instrument(filtered_notes: List[Dict[str, Any]], onsets: np.ndarray, durations: List[float]) -> pretty_midi.Instrument:
    """Create a MIDI instrument and add notes to it."""
    instrument_program = pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
    instrument = pretty_midi.Instrument(program=instrument_program)
    
    # Ensure we have matching lengths
    min_length = min(len(filtered_notes), len(onsets), len(durations))
    logging.info(f"Creating MIDI with {min_length} notes (filtered_notes: {len(filtered_notes)}, onsets: {len(onsets)}, durations: {len(durations)})")
    
    for i in range(min_length):
        note_info = filtered_notes[i]
        onset = onsets[i]
        duration = durations[i]
        
        # Convert numpy values to Python native types
        if hasattr(onset, 'item'):
            onset = onset.item()
        if hasattr(duration, 'item'):
            duration = duration.item()
        
        logging.info("Adding note: %s", note_info)
        logging.info("Adding onset: %s", str(onset))
        logging.info("Adding duration: %s", str(duration))

        note_number = pretty_midi.note_name_to_number(note_info["note"])
        # Ensure note_number is a Python native type
        if hasattr(note_number, 'item'):
            note_number = note_number.item()
        note_number = int(note_number)
        logging.info("Note number: %s", note_number)

        start_time = float(onset)
        end_time = start_time + float(duration)

        note = pretty_midi.Note(
            velocity=100, pitch=note_number, start=start_time, end=end_time
        )
        instrument.notes.append(note)
    
    return instrument


def create_midi(filtered_notes: List[Dict[str, Any]], onsets: np.ndarray, durations: List[float], tempo: float, output_file: str = "output.mid") -> str:
    """Create MIDI file using all the information."""
    logging.info("Received notes for MIDI creation: %s", filtered_notes)
    logging.info("Starting to create MIDI file.")
    
    # Ensure tempo is a Python native type
    if hasattr(tempo, 'item'):
        tempo = tempo.item()
    tempo = float(tempo)
    
    if tempo <= 0:
        logging.warning("Invalid tempo detected. Setting default tempo.")
        tempo = 120.0
    
    static_dir = os.path.join(app.root_path, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        logging.info("Created static directory: %s", static_dir)
    
    midi_file_path = os.path.join(static_dir, output_file)
    midi_data = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    instrument = create_midi_instrument(filtered_notes, onsets, durations)
    midi_data.instruments.append(instrument)
    midi_data.write(midi_file_path)
    
    logging.info("MIDI file written to %s", midi_file_path)
    return output_file


def generate_midi_url(filtered_notes: List[Dict[str, Any]], onsets: np.ndarray, durations: List[float], tempo: float) -> str:
    """Generate MIDI URL for local file."""
    midi_filename = create_midi(filtered_notes, onsets, durations, tempo, output_file="output.mid")
    midi_url = f"http://{HOST}:5002/static/{midi_filename}"
    return midi_url


def create_and_store_midi_in_s3(filtered_notes: List[Dict[str, Any]], onsets: np.ndarray, durations: List[float], tempo: float) -> str:
    """Create MIDI file and upload to AWS S3."""
    unique_id = str(uuid.uuid4())
    midi_filename = f"output_{unique_id}.mid"
    create_midi(filtered_notes, onsets, durations, tempo, output_file=midi_filename)

    try:
        local_midi_file_path = f"static/{midi_filename}"
        s3.upload_file(local_midi_file_path, s3_bucket_name, midi_filename)

        # Return proxy URL that works from the browser
        midi_url = f"http://localhost:5001/proxy-midi/{midi_filename}"
        
        if os.path.exists(local_midi_file_path):
            os.remove(local_midi_file_path)
            print(f"Successfully deleted local file: {local_midi_file_path}")
        else:
            print(f"Local file not found for deletion: {local_midi_file_path}")

        return midi_url
        
    except FileNotFoundError:
        print("The MIDI file was not found")
        raise
    except NoCredentialsError:
        print("AWS credentials not available")
        raise


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def find_username(user_id: str) -> str:
    """Find username by user ID."""
    try:
        user_id_obj = ObjectId(user_id)
    except TypeError as e:
        logging.error("Error converting user_id to ObjectId: %s", e)
        return ""

    user_collection = db["users"]
    user_doc = user_collection.find_one({"_id": user_id_obj})
    
    if user_doc:
        username = user_doc.get("username")
        logging.info("Found username.")
        return username
    
    logging.error("User not found for user_id: %s", user_id)
    return ""


def store_in_db(user_id: str, username: str, midi_url: str) -> None:
    """Store MIDI file reference in database."""
    if not username:
        logging.error("Username not found for user_id: %s", user_id)
        return

    data = {
        "user_id": user_id,
        "username": username,
        "midi_url": midi_url,
        "created_at": datetime.utcnow(),
    }

    collection.insert_one(data)
    logging.info("Inserted file by: %s", username)


# =============================================================================
# FLASK ROUTES
# =============================================================================

@app.route("/process", methods=["POST"])
def process_data():
    """Main route to process audio data and generate MIDI."""
    try:
        logging.info("Received audio processing request")
        
        # Validate request
        if "audio" not in request.files:
            logging.error("No audio file found in request")
            raise ValueError("No audio file found in the request")
        
        file = request.files["audio"]
        user_id = request.form.get("user_id")
        
        logging.info(f"Processing audio file: {file.filename}, content_type: {file.content_type}")

        # Check MIME type
        if file.content_type != "audio/webm":
            logging.error(f"Unsupported content type: {file.content_type}")
            return jsonify({"error": "Unsupported Media Type"}), 415

        # Process audio files
        webm_file = "temp_recording.webm"
        wav_file = "temp_recording.wav"

        logging.info("Writing audio file to disk")
        write_audio_to_file(webm_file, file)
        
        logging.info("Converting WebM to WAV")
        convert_webm_to_wav(webm_file, wav_file)

        # Extract notes from audio
        logging.info("Reading audio file with soundfile")
        audio, sr = sf.read(wav_file)
        logging.info(f"Audio loaded: shape={audio.shape}, sample_rate={sr}")
        
        logging.info("Processing audio chunks for pitch detection")
        notes_data = process_audio_chunks(audio, sr)
        notes_data_sorted = sort_notes_data(notes_data)
        logging.info("Chunked notes data for jsonify: %s", notes_data_sorted)

        # Analyze timing and tempo
        logging.info("Loading audio with librosa for timing analysis")
        y, sr = librosa.load(wav_file, sr=44100)
        
        logging.info("Detecting note onsets")
        onsets = detect_note_onsets(wav_file)
        
        logging.info("Estimating note durations")
        durations = estimate_note_durations(onsets, y, sr=44100)
        
        logging.info("Estimating tempo")
        tempo = estimate_tempo(wav_file)

        # Clean up temporary files
        logging.info("Cleaning up temporary files")
        clean_up_files(webm_file, wav_file)

        # Check if we have any notes to process
        processed_notes = process_notes(notes_data)
        if not processed_notes:
            logging.warning("No notes detected in audio")
            return jsonify({"error": "No musical notes detected in the audio. Please try recording again with clearer audio."}), 400
        
        # Check if we have onsets and durations
        if len(onsets) == 0 or len(durations) == 0:
            logging.warning("No onsets or durations detected")
            return jsonify({"error": "Could not detect timing information. Please try recording again."}), 400
        
        # Generate and store MIDI
        logging.info("Creating and storing MIDI file")
        midi_url = create_and_store_midi_in_s3(
            processed_notes, onsets, durations, tempo
        )

        if midi_url is None:
            app.logger.error("Failed to generate or store MIDI file in S3")
            return jsonify({"error": "MIDI generation failed"}), 500

        # Store in database if user is logged in
        if user_id:
            logging.info(f"Storing MIDI in database for user: {user_id}")
            store_in_db(user_id, find_username(user_id), midi_url)

        logging.info(f"Successfully processed audio, MIDI URL: {midi_url}")
        return jsonify({"midi_url": midi_url})

    except IOError as e:
        app.logger.error("IO error occurred: %s", e)
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        app.logger.error("Value error occurred: %s", e)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        app.logger.error("Unexpected error occurred: %s", e)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
