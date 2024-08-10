from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import os
from pydub import AudioSegment

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize speech recognizer
recognizer = sr.Recognizer()

@app.post("/process")
async def process(question: str = Form(...), file: UploadFile = File(...)):
    # Save the uploaded audio file
    file_location = f"temp_{file.filename}"
    with open(file_location, "wb+") as f:
        f.write(await file.read())
    
    # Convert audio to WAV format if necessary
    audio_format = file.filename.split(".")[-1]
    if audio_format.lower() != "wav":
        audio = AudioSegment.from_file(file_location)
        wav_location = "temp_converted.wav"
        audio.export(wav_location, format="wav")
        os.remove(file_location)  # Remove the original file
        file_location = wav_location

    # Process the audio file and recognize speech
    with sr.AudioFile(file_location) as source:
        audio_data = recognizer.record(source)
        try:
            answer = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            answer = "Could not understand audio"
        except sr.RequestError as e:
            answer = f"Could not request results from Google Speech Recognition service; {e}"
    
    # Create a text file with the question and answer
    text_file_path = "transcription_report.txt"
    with open(text_file_path, mode='w') as file:
        file.write(f"Question: {question}\n")
        file.write(f"Answer: {answer}\n")
    
    # Clean up temporary files
    if os.path.exists(file_location):
        os.remove(file_location)

    # Return the text file as a response
    return FileResponse(text_file_path, media_type='text/plain', filename=text_file_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
