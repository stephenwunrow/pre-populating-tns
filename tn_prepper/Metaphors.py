from TNPrepper import TNPrepper

import re
from groq import Groq
import os
from dotenv import load_dotenv
import time
import csv


class ATSnippets(TNPrepper):
    def __init__(self):
        super().__init__()

        load_dotenv()

        api_key = os.getenv('API_KEY')
        self.verse_text = os.getenv('VERSE_TEXT')

        # Initialize the Groq client with your API key
        self.groq_client = Groq(api_key=api_key)
        self.groq_model = 'llama3-70b-8192'

    # Function for metaphors
    def __process_metaphors(self, context, verse_reference):
        # Generate prompt
        prompt1 = (
            f"Given the context, does verse {verse_reference} contain a metaphor? "
            f"Be sure that the word or phrase is not better classified under a different label, such as simile or personification. "
            f"If there is a metaphor present, answer 'Yes'. If there is no metaphor present, answer 'No'. Do not provide any explanation."
        )

        # Query LLM for response
        response1 = self._query_llm(context, prompt1)

        # Process response
        if 'yes' in response1.lower():
            prompt2 = (
                f"Which exact words from {verse_reference} contain the metaphor? Respond with the exact words from the verse only. Do not include any explanation."
            )
            response2 = self._query_llm(context, prompt2)
            stripped_response2 = response2.strip('\'"“”‘’.,;:!?')

            prompt3 = (
                f"Explain in one sentence the meaning of the metaphor in the words '{stripped_response2}'. Be as brief as possible, and begin your sentence with the phrase 'This metaphor'."
            )
            response3 = self._query_llm(context, prompt3)
            stripped_response3 = response3.strip('\'"“”‘’.,;:!?')

            prompt4 = (
                f"In {verse_reference}, the phrase '{stripped_response2}' contains a metaphor. Provide a way to express the idea without using a metaphor. Make your answer as short as possible, and respond with the rephrased text only."

            )
            response4 = self._query_llm(context, prompt4)
            stripped_response4 = response4.strip('\'"“”‘’.,;:!?')

            prompt5 = (
                f"Which exact words from {verse_reference} are the words '{stripped_response4}' semantically equivalent to? Respond with the exact words from the verse only. Do not include any explanation."

            )
            response5 = self._query_llm(context, prompt5)
            stripped_response5 = response5.strip('\'"“”‘’.,;:!?')


            return stripped_response2, stripped_response3, stripped_response4, stripped_response5

        return None, None, None, None

    def _read_tsv(self, file_path):
        verse_texts = []
        with open(file_path, 'r', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                verse_texts.append(row)
        return verse_texts

    def run(self):
        ai_data = []

        # Verse_texts should be the extracted ult created by usfm_extraction.py
        verse_texts = self._read_tsv(self.verse_text)

        # Check the stage and slice the list if in development stage
        if os.getenv('STAGE') == 'dev':
            verse_texts = verse_texts[:5]

        # Organize verse texts for easy access
        verse_map = {verse['Reference']: verse['Verse'] for verse in verse_texts}

        for reference, verse_text in verse_map.items():
            # Split reference into book, chapter, and verse
            book_name, chapter_and_verse = reference.split()
            chapter, verse = chapter_and_verse.split(':')

            # Determine previous and next verse references
            prev_verse_reference = f"{book_name} {chapter}:{int(verse) - 1}" if int(verse) > 1 else None
            next_verse_reference = f"{book_name} {chapter}:{int(verse) + 1}"

            # Retrieve previous and next verse texts
            prev_verse_text = verse_map.get(prev_verse_reference, "")
            next_verse_text = verse_map.get(next_verse_reference, "")

            # Construct context
            context = f"{prev_verse_reference} {prev_verse_text}\n{reference} {verse_text}\n{next_verse_reference} {next_verse_text}"

            # Process metaphors
            response2, response3, response4, response5 = self.__process_metaphors(context, reference)

            if response2 and response3 and response4 and response5:
                ai_data.append([reference, response2, response3, response4, response5])

        # Write the results to a new TSV file
        headers = ['Reference', 'Metaphor', 'Explanation', 'Alternate Translation', 'Snippet']
        self._write_output(book_name='Obadiah', file='ai_metaphors.tsv', headers=headers, data=ai_data)

        if ai_data:
            transformed_data = list()
            for row in ai_data:

                if len(row) == 5:
                    reference = row[0]
                    snippet = row[4]
                    explanation = row[2]
                    alternate_translation = row[3]
                    support_reference = 'rc://*/ta/man/translate/figs-metaphor'
                    note_template = f'{explanation}. If it would be helpful in your language, you could state the meaning plainly. Alternate translation: “{alternate_translation}”'
                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',  # ID: random, unique four-letter and number combination
                        '',  # Tags: blank
                        support_reference,  # SupportReference: standard link
                        'hebrew_placeholder',  # Quote: lexeme
                        '1',  # Occurrence: the number 1
                        note_template,  # Note: standard note with {gloss}
                        snippet
                    ]

                    transformed_data.append(transformed_row)

        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name='Obadiah', file='transformed_ai_metaphors.tsv', headers=headers, data=transformed_data)

if __name__ == "__main__":
    obj_at_snippets = ATSnippets()
    obj_at_snippets.run()
