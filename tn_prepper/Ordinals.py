from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os

load_dotenv()

class Ordinals(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def run(self):

        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern
        identification_pattern = r'x-morph="([^"]*?Ao[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)

        # Transform the data
        support_reference = "rc://*/ta/man/translate/translate-ordinal"
        note_template = "If your language does not use ordinal numbers, you could use a cardinal number here or an equivalent expression. Alternate translation: “alternate_translation”"
        file_name = "ordinals.tsv"

        transformed_data = self._transform_data(verse_data, support_reference, note_template)

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    ordinals_instance = Ordinals(book_name, version)
    ordinals_instance.run()