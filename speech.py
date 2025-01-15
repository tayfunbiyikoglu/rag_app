import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
import tempfile
import os
from dotenv import load_dotenv
import io
import time
from pydub import AudioSegment

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="CEB Audio Analysis App", layout="wide")
st.title("CEB Audio Analysis App")

# Constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_TYPES = ["audio/wav", "audio/mpeg"]

def initialize_speech_client():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    if not speech_key or not speech_region:
        raise ValueError("Azure Speech credentials not found in environment variables")
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    return speech_config

def initialize_openai_client():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    return client

def validate_file(uploaded_file):
    """Validate the uploaded file"""
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE/1024/1024}MB limit")

    # Check file type
    if uploaded_file.type not in ALLOWED_TYPES:
        raise ValueError(f"Invalid file type. Allowed types: {', '.join(ALLOWED_TYPES)}")

    return True

def convert_to_wav(input_file, input_format):
    """Convert audio file to WAV format"""
    try:
        # Read the audio file
        if input_format == 'mp3':
            audio = AudioSegment.from_mp3(input_file)
        else:
            audio = AudioSegment.from_wav(input_file)

        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=tempfile.gettempdir()) as tmp_wav_file:
            audio.export(tmp_wav_file.name, format='wav')
            return tmp_wav_file.name

    except Exception as e:
        st.error(f"Error converting audio file: {str(e)}")
        raise

def transcribe_audio(audio_file_path, speech_config):
    """Transcribe audio file using Azure Speech Services"""
    try:
        audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        # Set up the event handlers
        done = False
        all_results = []

        def handle_result(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                all_results.append(evt.result.text)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                st.error(f"No speech could be recognized: {evt.result.no_match_details}")

        def handle_canceled(evt):
            st.error(f"Speech Recognition canceled: {evt.result.cancellation_details.reason}")
            if evt.result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                st.error(f"Error details: {evt.result.cancellation_details.error_details}")
            nonlocal done
            done = True

        def handle_session_stopped(evt):
            nonlocal done
            done = True

        # Connect the event handlers
        speech_recognizer.recognized.connect(handle_result)
        speech_recognizer.canceled.connect(handle_canceled)
        speech_recognizer.session_stopped.connect(handle_session_stopped)

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()
        while not done:
            time.sleep(0.1)  # Reduce CPU usage
            pass
        speech_recognizer.stop_continuous_recognition()

        if all_results:
            return " ".join(all_results)
        else:
            return "No speech could be recognized."

    except Exception as e:
        st.error(f"Error in transcribe_audio: {str(e)}")
        raise

def analyze_text(client, text):
    """Analyze text using Azure OpenAI"""
    try:
        # Generate summary
        summary_prompt = f"Please provide a concise summary of the following text:\n{text}"
        summary_response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise summaries."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        summary = summary_response.choices[0].message.content

        # Generate sentiment analysis
        sentiment_prompt = f"Analyze the sentiment of the following text and classify it as positive, negative, or neutral. Provide a brief explanation:\n{text}"
        sentiment_response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes sentiment."},
                {"role": "user", "content": sentiment_prompt}
            ]
        )
        sentiment = sentiment_response.choices[0].message.content

        return summary, sentiment
    except Exception as e:
        st.error(f"Error in analyze_text: {str(e)}")
        raise

def main():
    try:
        speech_config = initialize_speech_client()
        openai_client = initialize_openai_client()

        # File uploader with size limit
        uploaded_file = st.file_uploader(
            "Upload an audio file (WAV or MP3, max 25MB)",
            type=["wav", "mp3"]
        )

        if uploaded_file is not None:
            try:
                # Validate file
                validate_file(uploaded_file)

                st.audio(uploaded_file, format="audio/wav")

                # Create temporary file for the uploaded file
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(uploaded_file.name)[1],
                    dir=tempfile.gettempdir()
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                try:
                    # Convert to WAV if it's an MP3 file
                    file_format = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
                    if file_format == 'mp3':
                        wav_file_path = convert_to_wav(tmp_file_path, file_format)
                    else:
                        wav_file_path = tmp_file_path

                    with st.spinner("Transcribing audio..."):
                        transcription = transcribe_audio(wav_file_path, speech_config)
                        st.subheader("Transcription")
                        st.write(transcription)

                    if transcription and transcription != "No speech could be recognized.":
                        with st.spinner("Analyzing text..."):
                            summary, sentiment = analyze_text(openai_client, transcription)

                            st.subheader("Summary")
                            st.write(summary)

                            st.subheader("Sentiment Analysis")
                            st.write(sentiment)

                finally:
                    # Clean up temporary files
                    try:
                        os.unlink(tmp_file_path)
                        if file_format == 'mp3' and 'wav_file_path' in locals():
                            os.unlink(wav_file_path)
                    except Exception as e:
                        st.error(f"Error cleaning up temporary files: {str(e)}")

            except ValueError as ve:
                st.error(str(ve))
            except Exception as e:
                st.error(f"An error occurred processing the file: {str(e)}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
