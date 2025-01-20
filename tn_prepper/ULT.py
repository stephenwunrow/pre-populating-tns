from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
import re

load_dotenv()

class ULT(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def run(self):
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)
        
        def create_ult(soup, book_name):
            # Initialize variables
            chapter = None
            verse = None
            verse_words = []
            verse_data = []

            # Extract the text from the BeautifulSoup object
            text = soup.get_text()

            # Perform the regex substitution on the extracted text
            text = re.sub(r' \\v', r'\n\\v', text)

            # Regex pattern to capture words, punctuation, and curly brace content
            pattern = re.compile(r'\\w ([^|]*?)\||(["\'{(]+)\\|\*([)}.,:;!?\'"\u2014]+)')

            # Split the content into lines and process
            for line in text.splitlines():
                # Check for section marker
                if '\\ts\\*' in line:
                    if verse_words and chapter and verse:
                        # Add current verse before section marker
                        verse_data.append(f'{book_name} {chapter}:{verse}\t{"".join(verse_words)}')
                    # Add section marker line
                    verse_data.append(f'-')
                    verse_words = []
                    continue

                if line.startswith('\\c '):
                    if verse_words:
                        # Append previous verse words to verse_data
                        verse_data.append(f'{book_name} {chapter}:{verse}\t{"".join(verse_words)}')
                    match = re.search(r'\\c\s+(\d+)', line)
                    if match:
                        chapter = int(match.group(1))
                    verse_words = []
                elif line.startswith('\\v '):
                    if verse_words:
                        # Append previous verse words to verse_data
                        verse_data.append(f'{book_name} {chapter}:{verse}\t{"".join(verse_words)}')
                    match = re.search(r'\\v\s+(\d+)', line)
                    if match:
                        verse = int(match.group(1))
                    verse_words = []
                    # Handle the rest of the line to capture the first word
                    remainder = line[match.end():].strip()
                    matches = pattern.findall(remainder)
                    for match in matches:
                        if match[0]:  # words
                            words = [word.strip() for word in match[0].split()]
                            if verse_words and not verse_words[-1].endswith((' ', '"', "'", '(', '{', '[')):
                                verse_words.append(' ')  # Add space between words only when needed
                            verse_words.extend(words)
                        if match[1]:  # punctuation before zaln
                            verse_words.append(match[1])
                        if match[2]:  # punctuation after zaln
                            verse_words.append(match[2])
                else:
                    matches = pattern.findall(line)
                    for match in matches:
                        if match[0]:  # words
                            words = [word.strip() for word in match[0].split()]
                            if verse_words and not verse_words[-1].endswith((' ', '"', "'", '(', '{', '[')):
                                verse_words.append(' ')  # Add space between words only when needed
                            verse_words.extend(words)
                        if match[1]:  # punctuation before zaln
                            verse_words.append(match[1])
                        if match[2]:  # punctuation after zaln
                            verse_words.append(match[2])

            # Append the last verse
            if verse_words:
                verse_data.append(f'{book_name} {chapter}:{verse}\t{"".join(verse_words)}')

            return verse_data

        # Define the cleanup function
        def cleanup_lines(verse_data):
            cleaned_data = []
            for line in verse_data:
                # Fix spacing and punctuation first
                line = re.sub(r'\s+', ' ', line)  # Normalize spaces
                line = re.sub(r'( )([.,;:?!—})\]]+)', r'\2', line)  # Remove spaces before closing punctuation
                line = re.sub(r'([({[\u2014]+)( )', r'\1', line)  # Remove spaces after opening punctuation
                line = re.sub(r'(\w[\u2019]) (s)', r'\1\2', line)  # Fix possessives
                
                # Handle quotes and curly braces last
                line = re.sub(r'"\s*([^"]+?)\s*"', r'"\1"', line)  # Fix spacing around quoted text
                line = re.sub(r'\{\s*([^}]+?)\s*\}', r'\1', line)  # Remove curly braces but preserve contents and spacing
                
                line = line.strip()
                cleaned_data.append(line)
            return cleaned_data

        # Create the data
        verse_data = create_ult(soup, self.book_name)

        # Clean the data
        cleaned_data = cleanup_lines(verse_data)

        headers = ['Reference', 'Verse']
        file_name = 'ult_book.tsv'
        data = cleaned_data
        self._write_tsv(book_name, file_name, headers, data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    ult_instance = ULT(book_name, version)
    ult_instance.run()