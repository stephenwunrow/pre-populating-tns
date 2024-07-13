from TNPrepper import TNPrepper

import re
from groq import Groq
import os
from dotenv import load_dotenv
import time


class ATSnippets(TNPrepper):
    def __init__(self):
        super().__init__()

        load_dotenv()

        api_key = os.getenv('API_KEY')
        book_name = os.getenv('BOOK_NAME')
        self.verse_text = f'output/{book_name}/ult_book.tsv'
        self.notes_text = f'output/{book_name}/combined_notes.tsv'

        # Initialize the Groq client with your API key
        self.groq_client = Groq(api_key=api_key)
        self.groq_model = 'llama3-70b-8192'

    # Function to wait between queries
    def __wait_between_queries(self, seconds):
        print(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)

    # Function to query the LLM
    def __query_llm(self, context, prompt):
        combined_prompt = f"Verse and context:\n{context}\n\nPrompt:\n{prompt}"
        response = None

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[

                    {
                        "role": "system",
                        "content": "You are a bible-believing scholar. You are analyzing a text and providing answers that exactly match that text. You should not provide explanations and interpretation unless you are specifically asked to do so."
                    },

                    {
                        "role": "user",
                        "content": combined_prompt,
                    }
                ],
                model=self.groq_model,
            )
            response = chat_completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"Request failed: {e}")
            print(f"Failed to get response for prompt: {prompt}")

        finally:
            print(combined_prompt)
            print(f'Response: {response}')
            print('---')

            # Waiting, to stay below our request limit (30 reqs/minute)
            self.__wait_between_queries(2)

            return response

    # Function for SupportReference: rc://*/ta/man/translate/translate-names
    def __process_support_reference_translate_names(self, note, context, verse_reference, ai_notes):
        # Extract verse text and context

        # Example of how to generate prompts and process responses
        bold_word_match = re.search(r'\*\*(.*?)\*\*', note['Note'])
        if not bold_word_match:
            bold_word = ''
        else:
            bold_word = bold_word_match.group(1)

        # Generate prompt
        prompt = (
            f"Given the context, does the name '{bold_word}' in {verse_reference} refer to a man, woman, god, province, region, city, or something else? "
            f"If the name refers to a person, identify only whether the person is a man or a woman. If the name refers to anything else, be as specific as possible."
            f"Provide a one-word answer that identifies the class of thing the name '{bold_word}' refers to."
        )

        # Query LLM for response
        response = self.__query_llm(context, prompt)

        if response is None:
            ai_notes.append(note)

        else:
            # Process response
            note['Note'] = note['Note'].replace('______', response.rstrip('.').lower())
            ai_notes.append(note)

    # Function for SupportReference: rc://*/ta/man/translate/figs-abstractnouns
    def __process_support_reference_abstract_nouns(self, note, context, verse_reference, ai_notes):
        if note['Note'].count('*') == 4:
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

        elif note['Note'].count('*') > 4:
            bold_phrase_match = re.search(r'ideas of (\*\*.+\*\*), you could', note['Note'])
            if not bold_phrase_match:
                bold_phrase = ''
            else:
                found_phrase = bold_phrase_match.group(1)
                bold_phrase = re.sub(r"\*\*", r"'", found_phrase)

            # Generate prompt 1
            prompt1 = (
                f"In {verse_reference}, the nouns {bold_phrase} are all abstract. Express the meaning in another way, without using these or any other abstract nouns. "
                f"Make your answer as short as possible, and respond with the rephrased text only."
            )

        # Query LLM for response 1
        response1 = self.__query_llm(context, prompt1)
        if response1 is None:
            ai_notes.append(note)

        else:
            # Generate prompt 2 using response 1
            response1_cleaned = response1.strip('"“”‘’….()\'')
            prompt2 = (
                f"Which exact words from {verse_reference} are the words '{response1_cleaned}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
            )

            # Query LLM for response 2
            response2 = self.__query_llm(context, prompt2)
            if response2 is None:
                ai_notes.append(note)

            else:
                # Process responses
                note['Note'] = note['Note'].replace('alternate_translation', response1_cleaned)
                note['Snippet'] = response2.strip('"“”‘’….()\'')
                ai_notes.append(note)

    # Function for SupportReference: rc://*/ta/man/translate/translate-ordinal
    def __process_support_reference_translate_ordinal(self, note, context, verse_reference, ai_notes):

        snippet = note['Snippet']

        # Generate prompt 1
        prompt1 = (
            f"In {verse_reference}, the word or phrase '{snippet}' is or contains an ordinal number. Provide a way to express the idea by using a cardinal number. Make your answer as short as possible, and respond with the rephrased text only. Do not include any explanation."
        )

        # Query LLM for response 1
        response1 = self.__query_llm(context, prompt1)
        if response1 is None:
            ai_notes.append(note)

        else:
            # Generate prompt 2 using response 1
            response1_cleaned = response1.strip('"“”‘’….()\'')
            prompt2 = (
                f"Which exact words from {verse_reference} are the words '{response1_cleaned}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
            )

            # Query LLM for response 2
            response2 = self.__query_llm(context, prompt2)
            if response2 is None:
                ai_notes.append(note)

            # Process responses
            note['Note'] = note['Note'].replace('alternate_translation', response1_cleaned)
            note['Snippet'] = response2.strip('"“”‘’….()\'')
            ai_notes.append(note)

    # Function for SupportReference: rc://*/ta/man/translate/figs-activepassive
    def __process_support_reference_figs_activepassive(self, note, context, verse_reference, ai_notes):

        snippet = note['Snippet']

        # Generate prompt 1
        prompt1 = (
            f"In {verse_reference}, the phrase '{snippet}' contains a passive form. Provide a way to express the idea in active form, including the agent of the action if you can infer it from the context. Make your answer as short as possible, and respond with the rephrased text only."
        )

        # Query LLM for response 1
        response1 = self.__query_llm(context, prompt1)
        if response1 is None:
            ai_notes.append(note)

        else:
            # Generate prompt 2 using response 1
            response1_cleaned = response1.strip('"“”‘’….()\'')
            prompt2 = (
                f"Which exact words from {verse_reference} are the words '{response1_cleaned}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."
            )

            # Query LLM for response 2
            response2 = self.__query_llm(context, prompt2)
            if response2 is None:
                ai_notes.append(note)

            # Process responses
            note['Note'] = note['Note'].replace('alternate_translation', response1_cleaned)
            note['Snippet'] = response2.strip('"“”‘’….()\'')
            ai_notes.append(note)

    # Function for SupportReference: rc://*/ta/man/translate/figs-go
    def __process_support_reference_figs_go(self, note, context, verse_reference, ai_notes):

        snippet = note['Snippet']

        # Generate prompt
        prompt = (
            f"Given the context, does the verb or verb phrase '{snippet}' in {verse_reference} indicate movement through space/time? "
            f"Answer with 'Yes' or 'No' only, and do not provide any explanation."
        )

        # Query LLM for response
        response = self.__query_llm(context, prompt)
        if response is None:
            ai_notes.append(note)

        else:
            # Process response
            if 'yes' in response.lower():
                ai_notes.append(note)
            # elif 'no' in response.lower():
            #     pass

    def run(self):

        ai_notes = list()

        # Map support references to their corresponding processing functions
        support_reference_handlers = {
            'rc://*/ta/man/translate/translate-names': self.__process_support_reference_translate_names,
            'rc://*/ta/man/translate/figs-abstractnouns': self.__process_support_reference_abstract_nouns,
            'rc://*/ta/man/translate/translate-ordinal': self.__process_support_reference_translate_ordinal,
            'rc://*/ta/man/translate/figs-activepassive': self.__process_support_reference_figs_activepassive,
            'rc://*/ta/man/translate/figs-go': self.__process_support_reference_figs_go,
            # Add more mappings as needed
        }

        # Acquire the name of the Bible book
        book_name = self._get_book_name()

        # Verse_texts should be the extracted ult created by usfm_extraction.py
        verse_texts = self._read_tsv(f'{self.verse_text}')

        # Note_texts should be however many notes from combined_notes.tsv you want to run through
        note_texts = self._read_tsv(f'{self.notes_text}')

        # Organize verse texts for easy access
        verse_map = {verse['Reference']: verse['Verse'] for verse in verse_texts}

        # Prepare the context and query the LLM for each note

        # If we are on DEV, we only process the first 5 notes
        if os.getenv('STAGE') == 'dev':
            note_texts = note_texts[:5]

        for note in note_texts:
            # Construct the verse reference using the book name and the first column of the note
            chapter_verse = note['Reference']
            verse_reference = f"{book_name} {chapter_verse}"

            # Extract the text of the verse and its surrounding verses
            verse_text = verse_map.get(verse_reference)
            if verse_text is None:
                print(f"Verse {verse_reference} not found in {self.verse_text}. Skipping note.")
                continue

            # Find previous and next verses if available
            chapter, verse = map(int, chapter_verse.split(':'))
            prev_verse_reference = f"{book_name} {chapter}:{verse - 1}" if verse > 1 else None
            next_verse_reference = f"{book_name} {chapter}:{verse + 1}"

            prev_verse_text = verse_map.get(prev_verse_reference) if prev_verse_reference else None
            next_verse_text = verse_map.get(next_verse_reference)

            # Construct context
            context = {
                f'{prev_verse_reference} {prev_verse_text}\n{verse_reference} {verse_text}\n{next_verse_reference} {next_verse_text}'}

            # Determine which processing function to use based on the SupportReference
            support_ref = note['SupportReference']
            if support_ref in support_reference_handlers:
                # Call the appropriate processing function for this SupportReference
                support_reference_handlers[support_ref](note, context, verse_reference, ai_notes)
            else:
                print(f"Unknown SupportReference: {support_ref}. Appending unmodified note.")
                ai_notes.append(note)

        result_lines = self._combine_names(ai_notes)

        # Write the results to a new TSV file
        fieldnames = note_texts[0].keys()  # Assuming all notes have the same keys
        self._write_output(book_name=book_name, file='ai_notes.tsv', headers=fieldnames, data=result_lines, fieldnames=fieldnames)


obj_at_snippets = ATSnippets()
obj_at_snippets.run()
