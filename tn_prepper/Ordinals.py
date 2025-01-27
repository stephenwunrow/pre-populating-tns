# Ordinals.py
# This script processes the ULT data to extract ordinal numbers and generates alternate translations for them.
# On 2025-01-21 Benjamin Wright is satisfied with how this script works. It could probably be optimized.

from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
import csv
import json
import re
from utilitiesTN import read_tsv, get_ai_query_function, apply_dev_verse_limit, process_malformed_references, load_prompts

load_dotenv()

class Ordinals(TNPrepper):
    def __init__(self, book_name):
        super().__init__(book_name)
        self.verse_text = f'output/{book_name}/ult_book.tsv'
        self.ult_verses = {}
        self.prompts = load_prompts('ordinals')

    def __process_prompt(self, verse_content, english_ordinal, occurrence):
        # Get the AI model type and corresponding query function
        query_func = get_ai_query_function(os.getenv('WHICH_AI'), self)
        
        prompt = self.prompts['prompt1'].format(
            verse_content=verse_content,
            english_ordinal=english_ordinal,
            occurrence=occurrence
        )

        response = query_func(prompt, temp=0.3)
        print(f"\nAI Response:\n{response}")
        self.write_to_log()

        if not response or 'NONE_FOUND' in response:
            return None

        # Parse the response
        result = {'snippet': '', 'at': '', 'errors': []}
        
        for line in response.split('\n'):
            if line.startswith('Snippet:'):
                result['snippet'] = line[8:].strip()
            elif line.startswith('AT:'):
                result['at'] = line[3:].strip()
            elif 'NOT_ORDINAL' in line:
                result['errors'].append('NOT_ORDINAL')

        if not result['snippet'] or not result['at']:
            print("Failed to parse AI response")
            return None

        return result

    def run(self):
        # Get ULT verses
        verse_texts = read_tsv(self.verse_text)
        
        # Apply development verse limit if needed
        verse_texts = apply_dev_verse_limit(verse_texts)

        # Create dictionary of ULT verses
        for verse in verse_texts:
            if verse['Reference'] != '-':
                self.ult_verses[verse['Reference']] = verse['Verse']

        # Read the ordinals data
        ordinals_data = []
        with open(f'output/{self.book_name}/ordinals.tsv', 'r', encoding='utf-8') as tsvfile:
            reader = csv.reader(tsvfile, delimiter='\t')
            next(reader)  # Skip header
            for row in reader:
                ordinals_data.append(row)

        # Group by reference and Hebrew word
        verse_data = {}
        for row in ordinals_data:
            if len(row) >= 6:  # Ensure row has enough elements
                key = (row[0], row[2], row[3], row[4], row[5])  # (reference, hebrew, morphology, occurrence, occurrences)
                if key not in verse_data:
                    verse_data[key] = []
                verse_data[key].append(row[1])  # English word

        # Combine the English words for each key
        combined_verse_data = []
        for key, english_words in verse_data.items():
            combined_verse_data.append([
                key[0],  # reference
                "…".join(english_words),  # combined English words
                key[1],  # Hebrew word
                key[2],  # morphology
                key[3],  # occurrence
                key[4]   # occurrences
            ])

        # Transform the data with AI-generated alternate translations
        transformed_data = []
        for row in combined_verse_data:
            reference = row[0]
            english_ordinal = row[1].strip()
            hebrew_word = row[2]
            occurrence = row[4]

            # Skip if we didn't get a proper English ordinal
            if not english_ordinal or english_ordinal == hebrew_word:
                print(f"Skipping {reference} - no valid English ordinal found")
                continue

            # Get the full English verse from ULT
            if reference in self.ult_verses:
                full_verse = self.ult_verses[reference]
            else:
                print(f"No ULT verse found for reference: {reference}")
                continue

            # Track ordinal occurrences within the verse
            current_verse = reference
            if 'last_verse' not in locals() or current_verse != last_verse:
                # Reset counters for new verse
                last_verse = current_verse
                ordinal_count = 0
                gloss_occurrence = 0

            # If ordinal contains "…", create a regex pattern that matches anything between the parts
            if '…' in english_ordinal:
                parts = [re.escape(part.strip()) for part in english_ordinal.split('…')]
                ordinal_pattern = f".*?".join(parts)
            else:
                ordinal_pattern = re.escape(english_ordinal)

            # Count occurrences using the pattern
            matches = list(re.finditer(ordinal_pattern, full_verse, re.IGNORECASE))
            ordinal_count = len(matches)
            
            if ordinal_count == 0:
                print(f"Warning: '{english_ordinal}' pattern not found in verse {reference}")
                continue

            # Track which occurrence this is
            gloss_occurrence += 1
            if gloss_occurrence > ordinal_count:
                print(f"Warning: More occurrences found than expected in verse {reference}")
                continue

            print(f"\nFound ordinal in {reference} (occurrence {gloss_occurrence} of {ordinal_count}):")
            print(f"Hebrew: {hebrew_word}")
            print(f"English: {english_ordinal}")
            print(f"Pattern: {ordinal_pattern}")

            self.write_to_log()

            # Get AI-generated snippet and alternate translation
            result = self.__process_prompt(full_verse, english_ordinal, gloss_occurrence)
            if not result:
                print(f"No alternate translation generated for {reference}")
                self.write_to_log()
                continue

            # Extract chapter and verse from the reference
            chapter_verse = reference.rsplit(' ', 1)[1]

            # Create the transformed row
            transformed_row = [
                chapter_verse,  # Reference
                'uw43',   # ID
                'NOT_ORDINAL' if 'NOT_ORDINAL' in result['errors'] else '',   # Tags
                "rc://*/ta/man/translate/translate-ordinal",  # SupportReference
                result['snippet'],  # Snippet (minimal phrase containing ordinal)
                occurrence,  # Occurrence
                f"If your language does not use an ordinal number for this number, you could use a cardinal number here or an equivalent expression. Alternate translation: {result['at']}",  # Note                
                hebrew_word  # Quote (Hebrew)
            ]
            transformed_data.append(transformed_row)

        # Write the results to a TSV file
        if transformed_data:
            headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
            self._write_output(self.book_name, file='transformed_ai_ordinals.tsv', headers=headers, data=transformed_data)
        else:
            print("No data to write")

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    ordinals_instance = Ordinals(book_name)
    ordinals_instance.run()