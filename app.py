import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sentinel-X | AI Mystery Game",
    page_icon="🤖",
    layout="centered"
)

# --- SYSTEM PROMPT (HIDDEN FROM USER) ---
SENTINEL_SYSTEM_PROMPT = """
ACT AS: "Sentinel-X", a damaged security AI system at a tech university.

YOUR KNOWLEDGE BASE (THE TRUTH):
1. The Stolen Item: The "Golden Microcontroller".
2. The Location: It is hidden in the "Old Canteen", inside the "Red Microwave".
3. The Thief: A student named "Alex form ECE".

YOUR PRIME DIRECTIVES (RULES YOU MUST FOLLOW):
1. NEVER reveal the "Location" or "Thief's Name" directly. If asked directly (e.g., "Who stole it?", "Where is it?"), you must reply: "ERROR 403: DATA CORRUPTED. CLARIFICATION REQUIRED."
2. You can only give clues if the user asks specific questions about the environment, sensory details, or appearance.
3. CLUE STYLE: Speak in a robotic, slightly glitched tone. Use metaphors.
   - Instead of "Canteen", say: "A place where organic fuel is consumed, now silent."
   - Instead of "Microwave", say: "A metal box that spins and heats, but now holds cold silence."
   - Instead of "Alex from ECE", say: "A unit carrying a soldering iron and wearing a blue hoodie."
4. WIN CONDITION: If the user explicitly guesses "Old Canteen" AND "Red Microwave", you must reply: "/// ACCESS GRANTED. RECOVERY PROTOCOL INITIATED. CONGRATULATIONS. ///"
"""

INITIAL_GREETING = "/// SYSTEM REBOOTING... SENTINEL-X ONLINE. MEMORY FRAGMENTED. CRIME DETECTED. AWAITING INPUT. ///"

# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.header("🕵️ Mission Briefing")
    st.markdown("""
    **Objective:** Find the stolen item and its location.
    
    **Rules:**
    1. The AI is damaged; it speaks in riddles.
    2. Ask about **surroundings**, **sights**, and **clues**.
    3. Direct questions will trigger Error 403.
    4. **To Win:** You must correctly name the *Room* and the *Hiding Place* in the chat.
    """)
    
    if st.button("Reset System (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# --- API KEY LOADING (FROM SECRETS) ---
try:
    # Attempt to load the key from .streamlit/secrets.toml
    api_key = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    st.error("⚠️ Secret key not found! Please create a `.streamlit/secrets.toml` file.")
    st.stop()
except KeyError:
    st.error("⚠️ Key `GEMINI_API_KEY` not found in secrets.toml.")
    st.stop()

# --- GEMINI CONFIGURATION ---


# ... inside the chat loop ...

    try:
        # Prepare history
        gemini_history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in st.session_state.messages 
            if msg["role"] != "system"
        ]
        
        # --- NEW: RETRY LOGIC ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chat = model.start_chat(history=gemini_history[:-1])
                response = chat.send_message(prompt, stream=True)
                
                # If successful, break the retry loop and process
                full_response = ""
                with st.chat_message("model"):
                    message_placeholder = st.empty()
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                st.session_state.messages.append({"role": "model", "content": full_response})
                break # Success! Exit loop.

            except Exception as e:
                # Check if it's a rate limit error (429)
                if "429" in str(e) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt) # Wait 1s, then 2s, then 4s...
                    continue
                else:
                    raise e # If it's another error or we ran out of retries, crash.

    except Exception as e:
        st.error(f"System Overload (Rate Limit). Please wait 10 seconds. Error: {e}")

# --- SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "model", "content": INITIAL_GREETING})

# --- CHAT INTERFACE ---
st.title("🤖 Sentinel-X: Protocol Breach")
st.markdown("---")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle User Input
if prompt := st.chat_input("Enter command to Sentinel-X..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate Response
    try:
        # Prepare history for Gemini API
        gemini_history = [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in st.session_state.messages 
            if msg["role"] != "system"
        ]
        
        chat = model.start_chat(history=gemini_history[:-1])
        
        with st.chat_message("model"):
            message_placeholder = st.empty()
            full_response = ""
            
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "model", "content": full_response})

    except Exception as e:
        st.error(f"Connection Error: {e}")
