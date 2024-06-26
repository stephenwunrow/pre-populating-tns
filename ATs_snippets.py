import csv
import re
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
verse_text = os.getenv('VERSE_TEXT')
notes_text = os.getenv('NOTES_TEXT')


# Initialize the Groq client with your API key
client = Groq(api_key=api_key)

# Instruction message to guide the LLM
instruction_message = (
    "You are a bible-believing scholar. You are analyzing a text and providing answers that exactly match that text. You should not provide explanations and interpretation unless you are specifically asked to do so."
)

# Function to query the LLM
def query_llm(context, prompt):
    combined_prompt = f"Verse and context:\n{context}\n\nPrompt:\n{prompt}"
    print(combined_prompt)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": combined_prompt,
                }
            ],
            model="llama3-70b-8192",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# Function to read a TSV file and return its contents as a list of dictionaries
def read_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        return list(reader)

# Function to write a list of dictionaries to a TSV file
def write_tsv(file_path, fieldnames, data):
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, delimiter='\t', fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

ai_notes = []

# Function for SupportReference: rc://*/ta/man/translate/translate-names
def process_support_reference_translate_names(note, context, verse_reference, ai_notes):
    # Extract verse text and context

    # Example of how to generate prompts and process responses
    bold_word_match = re.search(r'\*\*(.*?)\*\*', note['Note'])
    if not bold_word_match:
        bold_word = ''
    else:
        bold_word = bold_word_match.group(1)
    
    # Generate prompt
    prompt = (
        f"Given the context, does the name {bold_word} in {verse_reference} refer to a man, woman, god, province, region, city, or something else? "
        f"If the name refers to a person, identify only whether the person is a man or a woman. If the name refers to anything else, be as specific as possible."
        f"Provide a one-word answer that identifies the class of thing the name {bold_word} refers to."
    )

    # Query LLM for response
    response = query_llm(context, prompt)
    print(f'Response: {response}')
    if response is None:
        print(f"Failed to get response for prompt: {prompt}")
        ai_notes.append(note)
    
    # Process response
    note['Note'] = note['Note'].replace('______', response.rstrip('.').lower())
    ai_notes.append(note)

# Function for SupportReference: rc://*/ta/man/translate/figs-abstractnouns
def process_support_reference_abstract_nouns(note, context, verse_reference, ai_notes):

    # Example of how to generate prompts and process responses
    bold_word_match = re.search(r'\*\*(.*?)\*\*', note['Note'])
    if not bold_word_match:
        bold_word = ''
    else:
        bold_word = bold_word_match.group(1)
    
    # Generate prompt 1
    prompt1 = (
        f"In {verse_reference}, the noun '{bold_word}' is abstract. Express the meaning in another way, without using this or any other abstract noun. "
        f"Make your answer as short as possible, and respond with the rephrased text only."
    )
    
    # Query LLM for response 1
    response1 = query_llm(context, prompt1)
    print(f'Response: {response1}')
    if response1 is None:
        print(f"Failed to get response for prompt 1: {prompt1}")
        ai_notes.append(note)
    
    # Generate prompt 2 using response 1
    prompt2 = (
        f"Which exact words from {verse_reference} are the words '{response1.strip('"“”‘’….()\'')}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
    )
    
    # Query LLM for response 2
    response2 = query_llm(context, prompt2)
    print(f'Response: {response2}')
    if response2 is None:
        print(f"Failed to get response for prompt 2: {prompt2}")
        ai_notes.append(note)
    
    # Process responses
    note['Note'] = note['Note'].replace('alternate_translation', response1.strip('"“”‘’….()\''))
    note['Snippet'] = response2.strip('"“”‘’….()\'')
    ai_notes.append(note)

# Function for SupportReference: rc://*/ta/man/translate/translate-ordinal
def process_support_reference_translate_ordinal(note, context, verse_reference, ai_notes):

    snippet = note['Snippet']

    # Generate prompt 1
    prompt1 = (
        f"In {verse_reference}, the word or phrase '{snippet}' is or contains an ordinal number. Provide a way to express the idea by using a cardinal number. Make your answer as short as possible, and respond with the rephrased text only. Do not include any explanation."
    )
    
    # Query LLM for response 1
    response1 = query_llm(context, prompt1)
    print(f'Response: {response1}')
    if response1 is None:
        print(f"Failed to get response for prompt 1: {prompt1}")
        ai_notes.append(note)
    
    # Generate prompt 2 using response 1
    prompt2 = (
        f"Which exact words from {verse_reference} are the words '{response1.strip('"“”‘’….()\'')}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
    )
    
    # Query LLM for response 2
    response2 = query_llm(context, prompt2)
    print(f'Response: {response2}')
    if response2 is None:
        print(f"Failed to get response for prompt 2: {prompt2}")
        ai_notes.append(note)
    
    # Process responses
    note['Note'] = note['Note'].replace('alternate_translation', response1.strip('"“”‘’….()\''))
    note['Snippet'] = response2.strip('"“”‘’….()\'')
    ai_notes.append(note)

# Function for SupportReference: rc://*/ta/man/translate/figs-activepassive
def process_support_reference_figs_activepassive(note, context, verse_reference, ai_notes):

    snippet = note['Snippet']

    # Generate prompt 1
    prompt1 = (
        f"In {verse_reference}, the phrase '{snippet}' contains a passive form. Provide a way to express the idea in active form, including the agent of the action if you can infer it from the context. Make your answer as short as possible, and respond with the rephrased text only."
    )
    
    # Query LLM for response 1
    response1 = query_llm(context, prompt1)
    print(f'Response: {response1}')
    if response1 is None:
        print(f"Failed to get response for prompt 1: {prompt1}")
        ai_notes.append(note)
    
    # Generate prompt 2 using response 1
    prompt2 = (
        f"Which exact words from {verse_reference} are the words '{response1.strip('"“”‘’….()\'')}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
    )
    
    # Query LLM for response 2
    response2 = query_llm(context, prompt2)
    print(f'Response: {response2}')
    if response2 is None:
        print(f"Failed to get response for prompt 2: {prompt2}")
        ai_notes.append(note)
    
    # Process responses
    note['Note'] = note['Note'].replace('alternate_translation', response1.strip('"“”‘’….()\''))
    note['Snippet'] = response2.strip('"“”‘’….()\'')
    ai_notes.append(note)

# Function for SupportReference: rc://*/ta/man/translate/figs-go
def process_support_reference_figs_go(note, context, verse_reference, ai_notes):

    snippet = note['Snippet']
    
    # Generate prompt
    prompt = (
        f"Given the context, does the verb or verb phrase '{snippet}' in {verse_reference} indicate movement through space/time? "
        f"Answer with 'Yes' or 'No' only, and do not provide any explanation."
    )

    # Query LLM for response
    response = query_llm(context, prompt)
    print(f'Response: {response}')
    if response is None:
        print(f"Failed to get response for prompt: {prompt}")
        ai_notes.append(note)
    
    # Process response
    if 'yes' in response.lower():
        ai_notes.append(note)
    elif 'no' in response.lower():
        pass

# Map support references to their corresponding processing functions
support_reference_handlers = {
    'rc://*/ta/man/translate/translate-names': process_support_reference_translate_names,
    'rc://*/ta/man/translate/figs-abstractnouns': process_support_reference_abstract_nouns,
    'rc://*/ta/man/translate/translate-ordinal': process_support_reference_translate_ordinal,
    'rc://*/ta/man/translate/figs-activepassive': process_support_reference_figs_activepassive,
    'rc://*/ta/man/translate/figs-go': process_support_reference_figs_go,
    # Add more mappings as needed
}

# Prompt the user for book name
book_name = input("Enter the book name (e.g., 2 Chronicles): ")

# Verse_texts should be the extracted ult created by usfm_extraction.py
verse_texts = read_tsv(f'{verse_text}')

# Note_texts should be however many notes from combined_notes.tsv you want to run through
note_texts = read_tsv(f'{notes_text}')

# Organize verse texts for easy access
verse_map = {verse['Reference']: verse['Verse'] for verse in verse_texts}

# Prepare the context and query the LLM for each note
for note in note_texts:
    # Construct the verse reference using the book name and the first column of the note
    chapter_verse = note['Reference']
    verse_reference = f"{book_name} {chapter_verse}"
    
    # Extract the text of the verse and its surrounding verses
    verse_text = verse_map.get(verse_reference)
    if verse_text is None:
        print(f"Verse {verse_reference} not found in verse_text.tsv. Skipping note.")
        continue

    # Find previous and next verses if available
    chapter, verse = map(int, chapter_verse.split(':'))
    prev_verse_reference = f"{book_name} {chapter}:{verse - 1}" if verse > 1 else None
    next_verse_reference = f"{book_name} {chapter}:{verse + 1}"

    prev_verse_text = verse_map.get(prev_verse_reference) if prev_verse_reference else None
    next_verse_text = verse_map.get(next_verse_reference)

    # Construct context
    context = {f'{prev_verse_reference} {prev_verse_text}\n{verse_reference} {verse_text}\n{next_verse_reference} {next_verse_text}'}

    # Determine which processing function to use based on the SupportReference
    support_ref = note['SupportReference']
    if support_ref in support_reference_handlers:
        # Call the appropriate processing function for this SupportReference
        note = support_reference_handlers[support_ref](note, context, verse_reference, ai_notes)
    else:
        print(f"Unknown SupportReference: {support_ref}. Appending unmodified note.")
        ai_notes.append(note)

# Write the results to a new TSV file
fieldnames = note_texts[0].keys()  # Assuming all notes have the same keys
write_tsv('ai_notes.tsv', fieldnames, ai_notes)

print("Results saved to ai_notes.tsv")
