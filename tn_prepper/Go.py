from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os

load_dotenv()

class Go(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()

        self.book_name = book_name
        self.version = version

    def run(self):

        go_instance = Go("Obadiah", "ult")
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern
        identification_pattern = r'x-morph="([^"]*?V[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)

        modified_verse_data = self._figs_go(verse_data)

        headers = ['Reference', 'Glosses', 'Lexeme', 'Morphology']
        file_name = 'new_figs_go.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=modified_verse_data)

        # Transform the data
        support_reference = "rc://*/ta/man/translate/figs-go"
        file_name = "go.tsv"

        transformed_data = self._transform_figs_go(modified_verse_data, support_reference)

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    go_instance = Go(book_name, version)
    go_instance.run()