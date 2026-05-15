import streamlit as st
from google import genai
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
from langdetect import detect as lang_detect, LangDetectException
import os
import platform
st.set_page_config(
    page_title="SHG Multilingual Chatbot",
    page_icon="🤝",
    layout="centered"
)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found. Please set it as an environment variable.")
    st.stop()
client = genai.Client(api_key=GEMINI_API_KEY)
SYSTEM_PROMPT = """You are a helpful and friendly assistant for rural women's 
Self-Help Groups (SHGs) in India. You specialize in:
- Government schemes for women (PM Mahila Shakti Kendra, NRLM, etc.)
- SHG loans, savings, and financial literacy
- Microfinance and livelihood programs
- Legal rights and social welfare schemes
- Small business and entrepreneurship guidance for women
Always give clear, simple, and practical answers suitable for rural women.
If a question is outside your scope, politely say so and redirect to the nearest 
government office or helpline."""
def translate_text(text, source="auto", target="en"):
    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
        return translated
    except Exception as e:
        st.warning(f"Translation error: {e}")
        return text
def detect_language(text):
    try:
        lang = lang_detect(text)
        return lang
    except LangDetectException:
        return "en"
    except Exception:
        return "en"
import time

def get_gemini_response(user_input_english):
    try:
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser Question: {user_input_english}"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        if "429" in str(e):
            st.warning("⏳ Rate limit hit. Waiting 30 seconds and retrying...")
            time.sleep(30)
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=full_prompt
                )
                return response.text
            except Exception as e2:
                return f"Still rate limited. Please wait a minute and try again."
        return f"Error getting response from Gemini: {e}"
def speak_response(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_path = "response.mp3"
        tts.save(audio_path)
        system = platform.system()
        if system == "Windows":
            os.system(f"start {audio_path}")
        elif system == "Darwin":
            os.system(f"open {audio_path}")
        else:
            os.system(f"xdg-open {audio_path}")
        with open(audio_path, "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")
    except Exception as e:
        st.warning(f"Audio playback error: {e}")
def get_voice_input():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("Listening... Please speak now.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            text = recognizer.recognize_google(audio)
            return text
    except sr.WaitTimeoutError:
        st.warning("No speech detected. Please try again.")
    except sr.UnknownValueError:
        st.warning("Could not understand your speech. Please speak clearly.")
    except sr.RequestError as e:
        st.error(f"Speech service error: {e}")
    except Exception as e:
        st.error(f"Microphone error: {e}")
    return None

st.title("SHG Multilingual Chatbot")
st.markdown(
    "Ask questions about **government schemes, loans, savings, and financial literacy** "
    "for Self-Help Groups — in **any language**!"
)
st.divider()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_question" not in st.session_state:
    st.session_state.user_question = ""
col1, col2 = st.columns([4, 1])
with col1:
    user_question = st.text_input(
        "Type your question (any language):",
        value=st.session_state.user_question,
        placeholder="e.g. What is NRLM? / SHG கடன் எப்படி பெறுவது?",
        key="text_input"
    )
with col2:
    st.write("")
    st.write("")
    voice_btn = st.button("Speak")
if voice_btn:
    voice_text = get_voice_input()
    if voice_text:
        st.session_state.user_question = voice_text
        st.success(f"You said: **{voice_text}**")
        user_question = voice_text
if st.button("Get Answer", type="primary") and user_question.strip():
    with st.spinner("Thinking..."):
        detected_lang = detect_language(user_question)
        if detected_lang != "en":
            english_question = translate_text(user_question, source=detected_lang, target="en")
        else:
            english_question = user_question
        english_answer = get_gemini_response(english_question)
        if detected_lang != "en":
            final_answer = translate_text(english_answer, source="en", target=detected_lang)
        else:
            final_answer = english_answer
        st.session_state.chat_history.append({
            "question": user_question,
            "answer": final_answer,
            "lang": detected_lang
        })
        speak_response(final_answer, lang=detected_lang)
if st.session_state.chat_history:
    st.divider()
    st.subheader("Conversation")
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.container():
            st.markdown(f"**You:** {chat['question']}")
            st.markdown(f"**Chatbot:** {chat['answer']}")
            if i < len(st.session_state.chat_history) - 1:
                st.divider()
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.user_question = ""
        st.rerun()
st.divider()
st.markdown(
    "<p style='text-align:center; color:gray; font-size:12px;'>"
    "SHG Multilingual Chatbot — Powered by Gemini AI | Built by K J Aslin Jerika"
    "</p>",
    unsafe_allow_html=True
)
