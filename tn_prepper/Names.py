from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os

load_dotenv()

class Names(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def run(self):
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern
        identification_pattern = r'x-morph="([^"]*?[^V]Np[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)

        joined_name_count, modified_verse_data = self._translate_names(verse_data)

        message = f'\n## Names from {book_name}\nName\tFrequency\n'
        data = joined_name_count
        report = self._write_report(data, message, book_name)

        headers = ['Reference', 'Glosses', 'Lexeme', 'Morphology', 'Name']
        file_name = 'names.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=modified_verse_data)

        # Standard link and note
        support_reference = 'rc://*/ta/man/translate/translate-names'

        transformed_data = self._transform_names(modified_verse_data, support_reference)

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        file_name = 'transformed_names.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    names_instance = Names(book_name, version)
    names_instance.run()