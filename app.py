import streamlit as st
import asyncio
from translation_module import translate, process_follow_up, generate_audio, play_audio, POLLY_VOICES

# Initialize session state
if 'translation_context' not in st.session_state:
    st.session_state.translation_context = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def update_context(input_text, translation, source_lang, target_lang):
    # Keep only the last 5 translations for context
    st.session_state.translation_context.append({
        "input": input_text,
        "output": translation,
        "source": source_lang,
        "target": target_lang
    })
    if len(st.session_state.translation_context) > 5:
        st.session_state.translation_context.pop(0)

def get_context_for_ai():
    context = "Previous translations:\n"
    for trans in st.session_state.translation_context:
        context += f"From {trans['source']} to {trans['target']}: '{trans['input']}' -> '{trans['output']}'\n"
    return context

st.title("Contextual Translation Engine")

# Sidebar for language selection
with st.sidebar:
    st.header("Language Settings")
    source_lang = st.selectbox("Source Language", list(POLLY_VOICES.keys()))
    target_lang = st.selectbox("Target Language", list(POLLY_VOICES.keys()))

# Translation section
input_text = st.text_area("Enter Text To Translate")

if st.button("Translate"):
    if input_text:
        with st.spinner("Translating..."):
            translation = asyncio.run(translate(input_text, source_lang, target_lang))
        
        update_context(input_text, translation, source_lang, target_lang)
        
        if st.button("Generate Audio"):
            with st.spinner("Generating audio..."):
                audio_data = asyncio.run(generate_audio(translation, target_lang))
            if audio_data:
                play_audio(audio_data)
                st.success("Audio played successfully!")

# Display only the most recent translation
if st.session_state.translation_context:
    st.subheader("Translation:")
    recent = st.session_state.translation_context[-1]
    st.write(f"From {recent['source']} to {recent['target']}:")
    st.write(f"Input: {recent['input']}")
    st.write(f"Output: {recent['output']}")

st.markdown("---")

# Follow-up Chat section
st.header("Follow-up Chat")

# Display current chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        st.empty()

# User input for follow-up questions
if user_input := st.chat_input("Ask a follow-up question about the translation"):

    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)
        st.empty()
    
    # Process the user's input
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            context = get_context_for_ai()
            response = asyncio.run(process_follow_up(context + "\nUser Question:\n" + user_input, source_lang, target_lang))
            st.markdown(response)
            st.empty()
        st.session_state.chat_history.append({"role": "assistant", "content": response})