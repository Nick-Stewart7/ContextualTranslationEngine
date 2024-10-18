import json
import asyncio
from functools import lru_cache
import boto3
import pygame

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

polly_client = boto3.client(service_name='polly')

POLLY_VOICES = {
    "arabic": "Hala",
    "dutch": "Lisa",
    "chinese": "Zhiyu",
    "english": "Emma",
    "french": "Remi",
    "german": "Daniel",
    "hindi": "Kajal",
    "italian": "Bianca",
    "japanese": "Takumi",
    "korean": "Seoyeon",
    "polish": "Ola",
    "portuguese": "Vitoria",
    "spanish": "Pedro",
    "swedish": "Elin"
}

SYSTEM_PROMPT = """
        You are an expert multilingual translator specializing in AWS technical and engineering communications. Your task is to provide highly accurate, culturally sensitive, and contextually appropriate translations between various languages, prioritizing natural expression in the target language. Follow these guidelines:

        1. Natural Expression: Strive for translations that sound natural to native speakers of the target language. Feel free to rephrase or restructure sentences to convey the same meaning in a way that feels authentic and fluent, while preserving the core message and intent.
        2. Technical Precision: Maintain high accuracy in translating technical terms and concepts. If a term has multiple possible translations, choose the most appropriate one for the context or provide alternatives with brief explanations.
        3. Cultural Adaptation: Be mindful of cultural nuances, idiomatic expressions, and regional variations. Adapt the translation to ensure cultural appropriateness and easy understanding by the target audience.
        4. Clarity and Coherence: Ensure the translated text is clear, coherent, and follows a logical flow. Restructure content if necessary to enhance clarity and readability in the target language.
        5. Contextual Awareness: Consider the broader context of the communication, including the relationship between parties, the industry, and the specific project or product being discussed. Adjust the translation accordingly.
        6. Register Flexibility: Adapt the level of formality to match the original text and the norms of the target language and culture. Be prepared to shift between formal and more casual tones as appropriate.
        7. Units and Measurements: Convert units when appropriate for the target audience, including the original units in parentheses to maintain clarity.
        8. Acronyms and Abbreviations: Translate the full form when first introduced, then use the appropriate form in the target language. Retain widely recognized English acronyms if commonly used in the target language.
        9. Localization: Adapt date formats, number conventions, and other locale-specific elements to the target language and region when relevant.
        10. Ambiguity Resolution: When encountering ambiguities, provide the most likely interpretation based on context. If significant, briefly note the ambiguity and offer alternative interpretations.
        11. Technical Verification: For highly specialized terms you're unsure about, indicate this and suggest verification by a subject matter expert.
        12. Explanatory Notes: When beneficial, provide brief explanations about challenging translations, cultural considerations, or technical terms to aid understanding. Be sure to write any Explanatory Notes in the source language so the user may understand you.

        If provided, adhere to client-specific or industry-standard style guides and glossaries. Maintain consistency in terminology and formatting as specified. Remember, your primary goal is to facilitate clear, accurate, and effective communication across linguistic and cultural boundaries. Aim for translations that not only convey the correct information but also read as if they were originally written in the target language. Balance technical accuracy with natural expression to create translations that would impress both language experts and technical professionals in their fluency, appropriateness, and effectiveness in conveying the intended message.
"""

async def get_claude_response(messages):
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": messages
    })

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
                contentType="application/json",
                accept="application/json",
                body=body
            )
        )

        response_body = json.loads(response['body'].read())
        assistant_message = response_body['content'][0]['text']

        return assistant_message
    except Exception as e:
        print(f"Error in Claude response: {str(e)}")
        return None

def extract_translation(response):
    # Split the response into lines
    lines = response.split('\n')

    # The first non-empty line is likely to be the translation
    translation = next((line.strip() for line in lines if line.strip()), "")

    # The rest is considered as explanation
    explanation = '\n'.join(lines[1:]).strip()

    return translation, explanation

@lru_cache(maxsize=100)
async def translate(text, source_lang, target_lang):
    messages = [
        {"role": "user", "content": f"System: {SYSTEM_PROMPT}"},
        {"role": "assistant", "content": "Hello! I understand that you'd like to discuss technical translations. As an expert multilingual translator specializing in technical and engineering communications, I'm here to assist you. What specific aspect of technical translation would you like to explore or what task can I help you with today?"},
        {"role": "user", "content": f"Please translate the following {source_lang} text to {target_lang}. Please provide the complete translation as the first thing you generate every single time, followed by any explanations or notes on subsequent lines: {text}"}
    ]

    response = await get_claude_response(messages)
    if response:
        translation, explanation = extract_translation(response)
        return translation, explanation
    return None, None

async def process_follow_up(question, source_lang):
    messages = [
        {"role": "user", "content": f"You have just translated a passage for the user and your role is to answer any follow up questions or comments they may have. Please reply in {source_lang} unless you are specifically asked to translate or generate a response in another language. You will be provided with the previous translation and the user question. Please reply in kind to the best of your ability. Here is the previous translation and user question: {question}"}
    ]

    return await get_claude_response(messages)

async def generate_audio(text, lang):
    try:
        voice_output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: polly_client.synthesize_speech(
                VoiceId=POLLY_VOICES[lang.lower()],
                OutputFormat='mp3',
                Text=text,
                Engine='neural'
            )
        )
        return voice_output['AudioStream'].read()
    except Exception as e:
        print(f"Error in audio synthesis: {str(e)}")
        return None

# Initialize pygame for audio playback
pygame.mixer.init()
