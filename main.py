import streamlit as st
import googlemaps
import os
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    st.error("Please set GOOGLE_MAPS_API_KEY in your .env file.")
    st.stop()

# Initialize Google Maps client
gmaps = googlemaps.Client(key=API_KEY)

# Detect if running on Streamlit Cloud
is_cloud = os.getenv('STREAMLIT_SERVER_HEADLESS', False)

# Initialize Voice Engine only if local
if not is_cloud:
    import pyttsx3
    speaker = pyttsx3.init()
else:
    speaker = None

# Initialize Speech Recognizer
recognizer = sr.Recognizer()

# Streamlit Page Setup
st.set_page_config(page_title="🏨 Global Hotel Voice Chat Assistant", page_icon="🏨")
st.title("🏨 Global Hotel Voice Chat Assistant")
st.caption("Chat or Speak to find safe, budget-friendly hotels anywhere!")

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Voice Input Option
use_voice = st.toggle("🎤 Use Voice Input")
user_prompt = None

if use_voice:
    if st.button("Speak Now"):
        with st.spinner("Listening..."):
            try:
                with sr.Microphone() as source:
                    audio = recognizer.listen(source, timeout=5)
                    user_prompt = recognizer.recognize_google(audio)
                    st.success(f"You said: {user_prompt}")
            except Exception as e:
                st.error(f"Voice Recognition Error: {e}")
else:
    user_prompt = st.chat_input("Where do you want to find hotels?")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Processing Chat
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        st.markdown(f"Searching for safe, budget hotels near **{user_prompt}**...")
        try:
            geocode_result = gmaps.geocode(user_prompt)
            if not geocode_result:
                st.warning(f"❌ Couldn't find location: {user_prompt}")
            else:
                location = geocode_result[0]['geometry']['location']
                latitude = location['lat']
                longitude = location['lng']

                places_result = gmaps.places_nearby(
                    location=(latitude, longitude),
                    radius=5000,
                    type="lodging"
                )

                safe_hotels = []
                rated_hotels = []

                for place in places_result['results']:
                    rating = place.get('rating', 0)
                    price_level = place.get('price_level', 'Unknown')

                    if rating >= 4.0 and (price_level != 'Unknown' and price_level <= 2):
                        safe_hotels.append(place)
                    elif rating >= 3.8:
                        rated_hotels.append(place)

                if safe_hotels:
                    hotel_replies = ""
                    for idx, hotel in enumerate(safe_hotels[:5], 1):
                        name = hotel.get('name', 'Unknown Hotel')
                        rating = hotel.get('rating', 'No rating')
                        price_level = hotel.get('price_level', 'Unknown')
                        address = hotel.get('vicinity', 'Unknown')
                        lat = hotel['geometry']['location']['lat']
                        lng = hotel['geometry']['location']['lng']
                        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

                        st.markdown(f"### {idx}. 🏨 {name}")
                        st.write(f"⭐ {rating} stars | 💲 Price Level: {price_level}")
                        st.write(f"📍 {address}")
                        st.markdown(f"[🌍 View on Map]({maps_link})")
                        st.markdown("---")
                        hotel_replies += f"{idx}. {name}, {address}. Rating {rating} stars.\n"

                    st.session_state.messages.append({"role": "assistant", "content": f"Here are the safest budget hotels I found:\n\n{hotel_replies}"})
                    if speaker:
                        speaker.say(f"Here are some safe hotels near {user_prompt}.")
                        speaker.runAndWait()

                elif rated_hotels:
                    st.info("🔔 No perfect safe-budget hotels found. Showing best rated nearby hotels!")
                    hotel_replies = ""
                    for idx, hotel in enumerate(rated_hotels[:5], 1):
                        name = hotel.get('name', 'Unknown Hotel')
                        rating = hotel.get('rating', 'No rating')
                        price_level = hotel.get('price_level', 'Unknown')
                        address = hotel.get('vicinity', 'Unknown')
                        lat = hotel['geometry']['location']['lat']
                        lng = hotel['geometry']['location']['lng']
                        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

                        st.markdown(f"### {idx}. 🏨 {name}")
                        st.write(f"⭐ {rating} stars | 💲 Price Level: {price_level}")
                        st.write(f"📍 {address}")
                        st.markdown(f"[🌍 View on Map]({maps_link})")
                        st.markdown("---")
                        hotel_replies += f"{idx}. {name}, {address}. Rating {rating} stars.\n"

                    st.session_state.messages.append({"role": "assistant", "content": f"Here are some highly rated hotels you might like:\n\n{hotel_replies}"})
                    if speaker:
                        speaker.say(f"Here are some highly rated hotels near {user_prompt}.")
                        speaker.runAndWait()

                else:
                    st.warning("⚡ No hotels found. Try another city!")
                    if speaker:
                        speaker.say(f"Sorry, no hotels found near {user_prompt}.")
                        speaker.runAndWait()

        except Exception as e:
            st.error(f"Error: {e}")
