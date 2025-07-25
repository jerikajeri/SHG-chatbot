
import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import os
from googletrans import Translator

# Setup Gemini API Key
genai.configure(api_key="AIzaSyBNkjzDmJjXPcgKz9uhA_489KQ5Qx6TGOM")
model = genai.GenerativeModel('gemini-1.5-pro-latest')

translator = Translator()

st.title("SHG Multilingual Chatbot with Voice (Gemini AI)")

# Text Input Section
user_question = st.text_input("Ask your question (any language) 👇")

# Voice Input Section
if st.button("🎙️ Speak Now"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening...")
        audio = recognizer.listen(source)
        try:
            user_question = recognizer.recognize_google(audio)
            st.write(f"You said: {user_question}")
        except:
            st.write("Sorry, could not recognize your voice.")

if user_question:
    # Translate to English (if needed)
    detected_lang = translator.detect(user_question).lang
    if detected_lang != 'en':
        user_question = translator.translate(user_question, dest='en').text

    # Gemini AI Response
    response = model.generate_content(user_question)
    answer = response.text

    # Translate back to original language
    translated_answer = translator.translate(answer, dest=detected_lang).text

    # Display and Speak the Response
    st.write("🤖 Chatbot Answer:")
    st.write(translated_answer)

    tts = gTTS(translated_answer, lang=detected_lang)
    tts.save("response.mp3")
    os.system("start response.mp3")
