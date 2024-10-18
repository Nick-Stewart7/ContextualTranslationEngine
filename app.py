import streamlit as st
import asyncio
from translation_module import translate, process_follow_up, generate_audio, POLLY_VOICES

# Initialize session state
if 'translation_context' not in st.session_state:
    st.session_state.translation_context = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'translation' not in st.session_state:
    st.session_state.translation = None
if 'explanation' not in st.session_state:
    st.session_state.explanation = None
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

def update_context(input_text, translation, source_lang, target_lang):
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

async def async_translate(text, source_lang, target_lang):
    translation, explanation = await translate(text, source_lang, target_lang)
    return translation, explanation

async def async_generate_audio(text, lang):
    audio_data = await generate_audio(text, lang)
    return audio_data

st.title("Contextual Translation Engine")

# Sidebar for language selection
with st.sidebar:
    st.header("Language Settings")
    source_lang = st.selectbox("Source Language", list(POLLY_VOICES.keys()))
    target_lang = st.selectbox("Target Language", list(POLLY_VOICES.keys()))

# Translation section
st.session_state.input_text = st.text_area("Enter Text To Translate", value=st.session_state.input_text)

if st.button("Translate"):
    if st.session_state.input_text:
        with st.spinner("Translating..."):
            st.session_state.translation, st.session_state.explanation = asyncio.run(async_translate(st.session_state.input_text, source_lang, target_lang))
        update_context(st.session_state.input_text, st.session_state.translation, source_lang, target_lang)

# Display translation if available
if st.session_state.translation:
    st.subheader("Translation:")
    st.text_area("Translation:", value=st.session_state.translation, height=100)
    
    if st.session_state.explanation:
        with st.expander("View Explanation"):
            st.write(st.session_state.explanation)
    
    # Generate Audio button
    if st.button("Generate Audio"):
        with st.spinner("Generating audio..."):
            st.session_state.audio_data = asyncio.run(async_generate_audio(st.session_state.translation, target_lang))
        
        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format='audio/mp3')
        else:
            st.error("Failed to generate audio. Please try again.")

st.markdown("---")

# Follow-up Chat section
st.subheader("Follow-up Chat")

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