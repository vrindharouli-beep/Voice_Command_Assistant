import customtkinter as ctk
import threading
import speech_recognition as sr
import webbrowser
import datetime
import os
import platform
import pyttsx3
import psutil
import sounddevice as sd
import numpy as np

from dotenv import load_dotenv 
from google import genai      

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None
GEMINI_MODEL = 'gemini-2.5-flash'

try:
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment. Check your .env file!")
    gemini_client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Gemini Client Initialization Error: {e}")
    gemini_client = None

engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def record_audio(duration=5, fs=16000):
    app.after(0, lambda: result_text.set("Listening..."))
    try:
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        return np.squeeze(audio_data)
    except Exception as e:
        app.after(0, lambda: result_text.set(f"Microphone error: {e}"))
        return None

def recognize_speech_from_sd():
    r = sr.Recognizer()
    audio = record_audio(duration=6)
    if audio is None:
        return None

    audio_data = sr.AudioData(audio.tobytes(), 16000, 2)
    try:
        text = r.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio."
    except sr.RequestError:
        return "Network error."

def process_command(cmd):
    cmd = cmd.lower()
    response = ""

    if "open google" in cmd:
        webbrowser.open("https://google.com")
        response = "Opening Google search."
    elif "open youtube" in cmd:
        webbrowser.open("https://youtube.com")
        response = "Opening YouTube for videos."
    elif "open wikipedia" in cmd:
        webbrowser.open("https://wikipedia.org")
        response = "Opening Wikipedia."
    elif "open amazon" in cmd or "open shopping" in cmd:
        webbrowser.open("https://amazon.com")
        response = "Opening Amazon."
    elif "open news" in cmd:
        webbrowser.open("https://news.google.com")
        response = "Opening Google News."
    elif "search for" in cmd:
        query = cmd.split("search for", 1)[-1].strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            response = f"Searching Google for {query}."
        else:
            response = "What would you like me to search for?"
    elif "open calculator" in cmd:
        os.system("calc")
        response = "Opening Calculator."
    elif "open command prompt" in cmd or "open cmd" in cmd:
        os.system("start cmd")
        response = "Opening Command Prompt."
    elif "open word" in cmd or "open microsoft word" in cmd:
        os.system("winword")
        response = "Opening Microsoft Word."
    elif "open excel" in cmd or "open spreadsheet" in cmd:
        os.system("excel")
        response = "Opening Microsoft Excel."
    elif "open notepad" in cmd:
        os.system("notepad")
        response = "Opening Notepad."
    elif "open vs code" in cmd or "open code" in cmd:
        os.system("code")
        response = "Opening Visual Studio Code."
    elif "time" in cmd:
        response = "The time is " + datetime.datetime.now().strftime("%I:%M %p")
    elif "battery" in cmd:
        battery = psutil.sensors_battery()
        if battery:
            response = f"Battery is at {battery.percent} percent."
        else:
            response = "Battery information not available."
    elif "help robot" in cmd or "what can you do" in cmd:
        response = process_command_ai(
            "List 5 example commands, including 'open google', and 'open calculator', and one question I can ask you about science.",
            "You are a friendly assistant explaining your capabilities to the user."
        )
    elif "hello" in cmd:
        response = "Hello there! I’m your Gemini-powered voice assistant."
    elif "exit" in cmd or "quit" in cmd:
        response = "Goodbye! Have a nice day."
        speak(response)
        app.destroy()
        return
    else:
        response = process_command_ai(
            cmd,
            "You are a helpful and brief voice assistant. Keep your answers concise and conversational, focusing only on the information requested."
        )

    speak(response)
    return response

def process_command_ai(query, system_instruction):
    if not gemini_client:
        return "The AI assistant is not initialized due to a configuration error."

    app.after(0, lambda: result_text.set("Thinking with Gemini..."))
    try:
        gemini_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=query,
            config={"system_instruction": system_instruction}
        )
        return gemini_response.text
    except Exception as e:
        return f"Gemini AI Error: Could not get a response. ({e})"

def listen_and_act():
    text = recognize_speech_from_sd()

    if not text or text.startswith("Could not understand") or text == "Network error.":
        app.after(0, lambda: result_text.set(f"{text}"))
        return

    app.after(0, lambda: result_text.set(f"You said: {text}"))
    response = process_command(text)

    if response:
        app.after(0, lambda: result_text.set(f"You said: {text}\nAssistant: {response}"))

def start_listening_thread():
    threading.Thread(target=listen_and_act, daemon=True).start()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Smart Voice Assistant (Gemini Powered)")
app.geometry("600x400")
app.resizable(False, False)

title = ctk.CTkLabel(app, text="Smart Voice Assistant", font=("Helvetica", 24, "bold"))
title.pack(pady=15)

info_text = "Press 'Listen' and say commands like:\n'open Google', 'time', or try 'Help Robot'."
if not gemini_client:
     info_text = "Gemini Client Failed to Initialize. Please set your API key."

info = ctk.CTkLabel(
    app,
    text=info_text,
    font=("Arial", 14),
    justify="center"
)
info.pack(pady=10)

result_text = ctk.StringVar(value="Ready to assist you!")
result_lbl = ctk.CTkLabel(app, textvariable=result_text, font=("Arial", 16), wraplength=520)
result_lbl.pack(pady=20)

listen_btn = ctk.CTkButton(app, text="Listen", font=("Arial", 18, "bold"), width=200, height=50,
                          fg_color="#2e89ff", hover_color="#1b64c1", command=start_listening_thread)
listen_btn.pack(pady=15)

exit_btn = ctk.CTkButton(app, text="Exit", font=("Arial", 14, "bold"), width=100, height=35,
                          fg_color="#ff4c4c", hover_color="#c13b3b", command=app.destroy)
exit_btn.pack(pady=10)

app.mainloop()
