# Ordinals.py
# This script processes the ULT data to extract ordinal numbers and generates alternate translations for them.
# On 2025-01-21 Benjamin Wright is satisfied with how this script works. It could probably be optimized.

from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
import csv
import json
import re

load_dotenv()

class Ordinals(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version
        self.ult_file = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, verse_content, english_ordinal, occurrence):
        # print("-" * 50)

        prompt = (
            "You will be given a Bible verse and an ordinal number from that verse. You will also be given the occurrence number of the ordinal number. If there are multiple occurrences of the ordinal number in the verse, please only address this specific occurrence."
            "Please provide your response in the following JSON format:\n"
            "{\n"
            '  "snippet": "the minimal phrase containing the ordinal",\n'
            '  "alternates": ["cardinal number form", "equivalent expression"],\n'
            '  "errors": ["any errors encountered"]\n'
            "}\n\n"
            "Notes:\n"
            "1. The snippet should be a minimal phrase or clause from the verse that contains the ordinal which the alternate translation can replace\n"
            "2. The alternate translation(s) should always seamlessly replace the snippet in the verse. Make sure the verse is grammatically correct. You may need to add punctuation or other words to make it work.\n"
            "3. The alternate translation should **not** contain an ordinal number\n"
            "4. The first alternate should always use the cardinal number form (write out numbers <= 10)\n"
            "5. The second alternate (equivalent expression) is optional. Do not include it if you are just using the cardinal number form in another way.\n"
            "6. If the snippet is immediately preceded by a conjunction, include that conjunction in the snippet and alternate translation\n"
            "7. If the 'Ordinal to replace' does not contain an ordinal number, write 'NOT_ORDINAL' in the errors field (and nothing else) but still process the verse and return a snippet and alternate translations(s) as if it did contain an ordinal number\n"
            "The most common way to suggest this transformation is like this: `the third ruler` -> `ruler number three`\n"
            f"Verse: {verse_content}\n"
            f"Ordinal to replace: {english_ordinal} (occurrence {occurrence})"
        )

        which_ai = os.getenv('WHICH_AI')
        
        if which_ai == 'openai':
            response = self._query_openai(verse_content, prompt)
        elif which_ai == 'gemini':
            response = self._query_gemini(verse_content, prompt)
        elif which_ai == 'claude':
            response = self._query_claude(prompt=prompt)
        else:
            raise ValueError(f"Invalid AI model specified: {which_ai}")

        # Parse the response to get snippet and AT
        if response:
            try:
                result = json.loads(response)
                snippet = result.get('snippet', '').strip()
                alternates = result.get('alternates', [])
                at = '] or ['.join(alternates) if alternates else '' # multiple ATs
                at = f'[{at}]' if at else '' # enclose the ATs in brackets
                errors = result.get('errors', [])
                return {'snippet': snippet, 'at': at, 'errors': errors}
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"Error parsing AI response: {response}")
                print(f"Error details: {e}")
                return None
        return None

    def _read_ult_verses(self):
        """Read verses from ULT TSV file"""
        verses = {}
        try:
            with open(self.ult_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    if row['Reference'] != '-':  # Skip section markers
                        verses[row['Reference']] = row['Verse']
        except FileNotFoundError:
            print(f"ULT file not found: {self.ult_file}")
            return {}
        return verses

    def run(self):
        # Get ULT verses
        ult_verses = self._read_ult_verses()
        if not ult_verses:
            print("No ULT verses found. Please run ULT.py first.")
            self.write_to_log()
            return

        # Scrape data from proposed book for Hebrew
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern - capture morphology, Hebrew occurrence data, Hebrew word, & English word
        identification_pattern = r'x-morph="([^"]*?Ao[^"]*?)".+?x-occurrence="(\d+)" x-occurrences="(\d+)".+?x-content="([^"]+?)".+?\\w ([^|]+)\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)
        # print(f"Verse data: {verse_data}")
        print(f"Number of segments: {len(verse_data)}")
        self.write_to_log()

        # Check stage first
        if os.getenv('STAGE') == 'dev':
            # Then check for verse limit in dev mode
            dev_verse_limit = os.getenv('DEV_NUMBER_OF_VERSES')
            if dev_verse_limit:
                try:
                    dev_verse_limit = int(dev_verse_limit)
                    verse_data = verse_data[:dev_verse_limit]
                    print(f"Dev mode: Processing first {dev_verse_limit} verses")
                except ValueError:
                    print("Warning: Invalid 'DEV_NUMBER_OF_VERSES' value, processing all verses")
            else:
                print("Dev mode: No verse limit specified, processing all verses")

        # Combine consecutive rows with matching fields
        combined_verse_data = []
        last_row = None

        for row in verse_data:
            if len(row) >= 6:
                if last_row and \
                   last_row[0] == row[0] and \
                   last_row[2] == row[2] and \
                   last_row[3] == row[3] and \
                   last_row[4] == row[4] and \
                   last_row[5] == row[5]:
                    # Combine English words from matching rows
                    last_row[1] = f"{last_row[1]} … {row[1]}"
                else:
                    if last_row:
                        combined_verse_data.append(last_row)
                    last_row = row.copy()  # Create a copy to avoid modifying original data

        # Add the last row if it exists
        if last_row:
            combined_verse_data.append(last_row)

        print("Combined verse data:")
        for row in combined_verse_data[:2]:
            print(f"  {row}")
        print(f"Number of combined segments: {len(combined_verse_data)}")
        self.write_to_log()
        # Filter combined_verse_data to only include specific verses (testing)
        # combined_verse_data = [row for row in combined_verse_data if row[0] in ['Daniel 7:16', 'Daniel 8:3', 'Daniel 11:29']]

        print("-" * 50)
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
            if reference in ult_verses:
                full_verse = ult_verses[reference]
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
                'NOT_ORDINAL' if  'NOT_ORDINAL' in result['errors'] else '',   # Tags
                "rc://*/ta/man/translate/translate-ordinal",  # SupportReference
                result['snippet'],  # Snippet (minimal phrase containing ordinal)
                occurrence,  # Occurrence
                f"If your language does not use an ordinal number for this number, you could use a cardinal number here or an equivalent expression. Alternate translation: {result['at']}",  # Note                
                hebrew_word  # Quote (Hebrew)
            ]
            transformed_data.append(transformed_row)
            print(f"Transformed row: {transformed_row}")
            self.write_to_log()

        if not transformed_data:
            print("No ordinals found or no alternate translations generated.")
            self.write_to_log()
            return

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name=self.book_name, file='ordinals.tsv', headers=headers, data=transformed_data)
        self.write_to_log()

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    ordinals_instance = Ordinals(book_name, version)
    ordinals_instance.run()