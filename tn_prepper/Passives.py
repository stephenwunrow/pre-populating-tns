from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os

load_dotenv()

class Passives(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def run(self):
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern
        identification_pattern = r'x-morph="([^"]*?V[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)

        modified_verse_data = self._figs_passive(verse_data)

        headers = ['Reference', 'Glosses', 'Lexeme', 'Morphology']
        file_name = 'passives.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=modified_verse_data)


        Other = self._passive_report(modified_verse_data)

        message = f'\n## Passives in English from {book_name} that are not Niphal, Qal passive, Hophal, or Pual\nReferences\tGlosses\tLexeme\tMorphology\n'
        data = Other
        report = self._write_report(data, message, book_name)

        # Standard link and note
        support_reference = 'rc://*/ta/man/translate/figs-activepassive'
        note_template = 'If your language does not use this passive form, you could express the idea in active form or in another way that is natural in your language. Alternate translation: “alternate_translation”'

        transformed_data = self._transform_passives(modified_verse_data, support_reference, note_template)

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        file_name = 'transformed_passives.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    passives_instance = Passives(book_name, version)
    passives_instance.run()