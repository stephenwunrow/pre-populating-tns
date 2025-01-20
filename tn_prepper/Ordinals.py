from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
import csv

load_dotenv()

class Ordinals(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version
        self.ult_file = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, verse_content, english_ordinal):
        print("\nProcessing verse:")
        print(f"Verse content: {verse_content}")
        print(f"Ordinal to replace: {english_ordinal}")
        print("-" * 50)

        prompt = (
            "You will be given a Bible verse and an ordinal number from that verse. "
            "Please provide two things:\n"
            "1. The minimal phrase or clause from the verse that contains the ordinal (the snippet)\n"
            "2. A natural alternate translation of that snippet that replaces the ordinal with a cardinal number or equivalent expression\n"
            "If the snippet is immediately preceded by a conjunction, please include that conjunction in the snippet and alternate translation.\n"
            "Format your response exactly like this:\n"
            "Snippet: [the minimal phrase containing the ordinal]\n"
            "AT: [your alternate translation]\n\n"
            f"Verse: {verse_content}\n"
            f"Ordinal to replace: {english_ordinal}"
        )

        which_ai = os.getenv('WHICH_AI')
        
        if which_ai == 'openai':
            response = self._query_openai(verse_content, prompt)
        elif which_ai == 'gemini':
            response = self._query_gemini(verse_content, prompt)
        elif which_ai == 'claude':
            response = self._query_claude(verse_content, prompt)
        else:
            raise ValueError(f"Invalid AI model specified: {which_ai}")

        # Parse the response to get snippet and AT
        if response:
            try:
                lines = response.strip().split('\n')
                snippet = lines[0].replace('Snippet:', '').strip()
                at = lines[1].replace('AT:', '').strip()
                return {'snippet': snippet, 'at': at}
            except (IndexError, AttributeError):
                print(f"Error parsing AI response: {response}")
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
            return

        # Scrape data from proposed book for Hebrew
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern - capture morphology, Hebrew, and the English word
        identification_pattern = r'x-morph="([^"]*?Ao[^"]*?)".+?x-content="([^"]+?)".+?\\w ([^|]+?)\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)
        print(f"Verse data: {verse_data}")
        
        # Transform the data with AI-generated alternate translations
        transformed_data = []
        if verse_data:
            for row in verse_data:
                if len(row) >= 4:
                    reference = row[0]
                    english_ordinal = row[1].strip()  # The English ordinal word
                    hebrew_word = row[2]   # The Hebrew word

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

                    print(f"\nFound ordinal in {reference}:")
                    print(f"Hebrew: {hebrew_word}")
                    print(f"English: {english_ordinal}")

                    # Get AI-generated snippet and alternate translation
                    result = self.__process_prompt(full_verse, english_ordinal)
                    if not result:
                        print(f"No alternate translation generated for {reference}")
                        continue

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    # Create the transformed row
                    transformed_row = [
                        chapter_verse,  # Reference
                        '',   # ID
                        '',   # Tags
                        "rc://*/ta/man/translate/translate-ordinal",  # SupportReference
                        hebrew_word,  # Quote (Hebrew)
                        '1',  # Occurrence
                        f"If your language does not use ordinal numbers, you could use a cardinal number here or an equivalent expression. Alternate translation: [{result['at']}]",  # Note
                        result['snippet']  # Snippet (minimal phrase containing ordinal)
                    ]
                    transformed_data.append(transformed_row)

        if not transformed_data:
            print("No ordinals found or no alternate translations generated.")
            return

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name=self.book_name, file='ordinals.tsv', headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    ordinals_instance = Ordinals(book_name, version)
    ordinals_instance.run()