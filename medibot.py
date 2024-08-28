import pandas as pd
import streamlit as st
import requests
import google.generativeai as genai
import json
from google.generativeai.types import StopCandidateException
import difflib

st.set_page_config(
    page_title="Medibot",
    page_icon="👨‍⚕️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "This is a medical chatbot integrated with Gemini AI."
    }
)

# Increase font size for all elements including input fields
st.markdown("""
    <style>
    .stApp {
        background-color: #2950aa;  /* Navy blue color */
    }
    .big-font {
        font-size:20px !important;
    }
    .stTextInput > div > div > input {
        font-size: 20px;
    }
    .stTextArea > div > div > textarea {
        font-size: 20px;
    }
             /* Change the font color for the entire app */
    body {
        color: #FFFFFF;  /* White font color */
    }
    /* Change the font color for headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;  /* Blue color for headers */
    }
    /* Change the font color for specific elements if needed */
    .stTextInput label, .stTextArea label, .stchat_message {
        color: #FFFFFF;  /* White color for input labels */
    }
    /* Styling for chat messages */
    .stChatMessage {
        font-size: 24px !important;  /* Increase font size for chat messages */
    }
    .stChatMessage p {
        color: #FFFFFF !important;  /* Change text color for chat messages */
    }
    .stChatMessage .stChatMessageContent {
        background-color: #e6f3ff !important;  /* Light blue background for message content */
        border-radius: 15px !important;  /* Rounded corners for message bubbles */
        padding: 5px !important;  /* Add some padding inside the message bubbles */
    }
    </style>
    """, unsafe_allow_html=True)

def get_closest_match(word, word_list):
    matches = difflib.get_close_matches(word, word_list, n=1, cutoff=0.6)
    return matches[0] if matches else None

class MedicalChatbot:
    def __init__(self, csv_file):
        self.centers = []
        self.load_centers(csv_file)

    def load_centers(self, csv_file):
        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            services = [service.strip().lower() for service in row['services'].split(',')]
            center_info = {
                "center": row['center'],
                "services": services,
                "address": row['address'],
                "phone": row['phone'],
                "hours": row['hours'],
                "ratings": row['ratings'],
                "fees": row['fees']                
            }
            self.centers.append(center_info)

    def get_service_info(self, keyword):
        keyword = keyword.lower().strip()
        matching_centers = []

        for center in self.centers:
            for service in center['services']:
                if keyword in service:
                    matching_centers.append(center)
                    break

        if matching_centers:
            #response = f"Keyword: {keyword.capitalize()}\n"
            response = "Available Centers:\n"
            response += f"\nNote: All prices listed are fictitious estimates.\n"
            for center in matching_centers:
                response += f"\nCenter: {center['center']}\n"
                response += f"  Address: {center['address']}\n"
                response += f"  Phone: {center['phone']}\n"
                response += f"  Hours: {center['hours']}\n" 
                response += f"  Rating: {center['ratings']}\n" 
                response += f"  Fees: ${center['fees']}\n"             
            return response
        else:
            return "Sorry, we do not have information on that service."

    def respond_to_prompt(self, prompt):
        return self.get_service_info(prompt)

    def get_all_services(self):
        all_services = set()
        for center in self.centers:
            all_services.update(center['services'])
        return list(all_services)    

# Gemini AI configuration
API_KEY = "AIzaSyDguVIkytn21HBhcQoQJis_e7JcuAPQMko"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

def initializeAI():
    initialPrompt = """
    Your role is to be a chatbot responding to the messages from a user.
    Your response should be a string in json format with two keys: a 'response'
    key and a 'quit' key. The value of the 'response' key should be your response 
    to the user's prompt, and the value for the 'quit' key should be false unless 
    the user wants to end the conversation.

    Please keep your responses concise and avoid unnecessary repetition or recitation 
    of large amounts of text. If you're unsure or the query is too broad, ask for 
    clarification.

    Here's an example of how your response should be formatted:
    {'response': 'Good morning in Spanish is "buenos días"', 'quit': false}
    """
    chat.send_message(initialPrompt)


def get_gemini_ai_response(prompt):
    try:
        response = chat.send_message(prompt)
        reply = response.text
        map = json.loads(reply[8:len(reply)-4])
        return map['response']
    except StopCandidateException:
        return "I apologize, but I encountered an issue while generating a response. Could you please rephrase your question or try a different query?"
    except json.JSONDecodeError:
        return "I'm sorry, but I couldn't process the response correctly. Could you please try again?"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}. Please try again."

initializeAI()

# Initialize the chatbot
csv_file = 'medical_services1.csv'
chatbot = MedicalChatbot(csv_file)

# Initialize session state variables if they don't exist
if 'reset' not in st.session_state:
    st.session_state.reset = False

# Function to reset the form
def reset_form():
    st.session_state.reset = True

# Streamlit GUI
st.title("MediBot 👨‍⚕️🚑")

with st.chat_message(name="assistant", avatar="👨‍⚕️"):
    st.markdown('👨‍⚕️:Hello! Welcome to the MediBot!', unsafe_allow_html=True)
    st.markdown('👨‍⚕️:I am available to help you find information on medical centers and the services they provide. How can I assist you?', unsafe_allow_html=True)

# Create the input field for user prompt
user_prompt = st.text_input("Enter your request:", key="user_prompt", value="" if st.session_state.reset else st.session_state.get('user_prompt', ''))

# Handle the user's request and display the AI response
if user_prompt:    
    gemini_response = get_gemini_ai_response(user_prompt)   
    st.text_area("", gemini_response, height=200, key="gemini_response_area")
    
# Create the input field for user prompt
user_prompt2 = st.text_input("Enter the medical service required:", key="user_prompt2", value="" if st.session_state.reset else st.session_state.get('user_prompt2', ''))

# Handle the user's request and display the local response
if user_prompt2:
    keyword = user_prompt2.strip().lower()
    all_services = chatbot.get_all_services()
    
    if keyword not in all_services:
        closest_match = get_closest_match(keyword, all_services)
        if closest_match:
            st.warning(f"Did you mean '{closest_match}'? Showing results for '{closest_match}'.")
            keyword = closest_match
        else:
            st.warning("No matching service found. Please check your spelling.")
        
        local_response = chatbot.respond_to_prompt(keyword)
        st.text_area("", local_response, height=500, key="local_response_area")

# Add some space before the reset button
st.write("")
st.write("")

# Add the reset button at the bottom of the page
if st.button('Reset'):
    reset_form()
    st.rerun()

# Reset the reset flag
if st.session_state.reset:
    st.session_state.reset = False
