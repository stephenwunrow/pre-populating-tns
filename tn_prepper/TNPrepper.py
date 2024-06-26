import os
import csv
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

class TNPrepper():
    def __init__(self):
        self.output_base_dir = 'output'
        pass

    # Scrapes ult or ust and reads it, returning "soup"
    def _scrape_and_read_data(self, book_name, version):
        # Mapping of book names to their respective acronyms
        acronym_mapping = {
            "Genesis": "01-GEN",
            "Exodus": "02-EXO",
            "Leviticus": "03-LEV",
            "Numbers": "04-NUM",
            "Deuteronomy": "05-DEU",
            "Joshua": "06-JOS",
            "Judges": "07-JDG",
            "Ruth": "08-RUT",
            "1 Samuel": "09-1SA",
            "2 Samuel": "10-2SA",
            "1 Kings": "11-1KI",
            "2 Kings": "12-2KI",
            "1 Chronicles": "13-1CH",
            "2 Chronicles": "14-2CH",
            "Ezra": "15-EZR",
            "Nehemiah": "16-NEH",
            "Esther": "17-EST",
            "Job": "18-JOB",
            "Psalms": "19-PSA",
            "Proverbs": "20-PRO",
            "Song of Solomon": "22-SNG",
            "Isaiah": "23-ISA",
            "Jeremiah": "24-JER",
            "Lamentations": "25-LAM",
            "Ezekiel": "26-EZK",
            "Daniel": "27-DAN",
            "Hosea": "28-HOS",
            "Joel": "29-JOL",
            "Amos": "30-AMO",
            "Obadiah": "31-OBA",
            "Jonah": "32-JON",
            "Micah": "33-MIC",
            "Nahum": "34-NAM",
            "Habakkuk": "35-HAB",
            "Zephaniah": "36-ZEP",
            "Haggai": "37-HAG",
            "Zechariah": "38-ZEC",
            "Malachi": "39-MAL",
            "Matthew": "41-MAT",
            "Mark": "42-MRK",
            "Luke": "43-LUK",
            "John": "44-JHN",
            "Acts": "45-ACT",
            "Romans": "46-ROM",
            "1 Corinthians": "47-1CO",
            "2 Corinthians": "48-2CO",
            "Galatians": "49-GAL",
            "Ephesians": "50-EPH",
            "Philippians": "51-PHP",
            "Colossians": "52-COL",
            "1 Thessalonians": "53-1TH",
            "2 Thessalonians": "54-2TH",
            "1 Timothy": "55-1TI",
            "2 Timothy": "56-2TI",
            "Titus": "57-TIT",
            "Philemon": "58-PHM",
            "Hebrews": "59-HEB",
            "James": "60-JAS",
            "1 Peter": "61-1PE",
            "2 Peter": "62-2PE",
            "1 John": "63-1JN",
            "2 John": "64-2JN",
            "3 John": "65-3JN",
            "Jude": "66-JUD",
            "Revelation": "67-REV"
        }

        # Get the acronym from the acronym mapping
        if book_name in acronym_mapping:
            acronym = acronym_mapping[book_name]
        else:
            print("Invalid book name. Please enter a valid book name.")
            exit()

        # URL of the file to download
        url = f"https://git.door43.org/unfoldingWord/en_{version}/raw/branch/master/{acronym}.usfm"

        # Function to get the content of the file
        def get_file_content(url):
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                return ''

        # Get the file content
        file_content = get_file_content(url)

        # Process the file content
        soup = BeautifulSoup(file_content, 'html.parser')
        return soup

    # NOTE: there may be too much variation among the functions to use this for all of them
    # Searches "identification_pattern" and returns "verse_data"
        # "identification_pattern" should have two match groups, 
        # the first for morphology (x-morph) and the second for the Hebrew word (x-content),
        # and it should end with \\w .+?\|
    def _create_verse_data(self, soup, book_name, identification_pattern):
        # Initialize variables
        chapter = None
        verse = None
        verse_data = []

        # Combine all lines into a single string
        combined_text = soup.get_text(separator='\n')

        # Split the combined text by "\\zaln-s"
        chunks = combined_text.split('\\zaln-s')

        with tqdm(total=len(chunks), desc="Processing Chunks") as pbar:
            for chunk in chunks:
                pbar.update(1)  # Update progress bar

                # Find all matches of the desired pattern
                matches = re.findall(identification_pattern, chunk, re.DOTALL)
                if matches:  # Only proceed if there are matches
                    for match in matches:
                        lexeme = match[1]
                        morphology = match[0]

                        # Find all glosses in the chunk
                        gloss_matches = re.findall(r'\\w (.+?)\|', chunk)
                        if gloss_matches:
                            # Combine all glosses into a single string
                            combined_gloss = ' '.join(gloss_matches)

                            # Append to verse_data with lexeme, verse reference, and combined glosses
                            verse_data.append([f'{book_name} {chapter}:{verse}', combined_gloss, lexeme, morphology])

                # Find chapter in the chunk
                chapter_match = re.search(r'\\c (\d+)', chunk)
                if chapter_match:
                    chapter = int(chapter_match.group(1))
                
                # Find verse in the chunk
                verse_match = re.search(r'\\v (\d+)', chunk)
                if verse_match:
                    verse = int(verse_match.group(1))
    
        return verse_data

    # NOTE: there may be too much variation among the functions to use this for all of them
    # Takes "verse_data" and transforms it into TN form
        # Provide the appropriate "SupportReference" and "note_template" for the type of note
        # Provide the output file name (e.g., "transformed_ordinals.tsv")
    def _transform_data(self, verse_data, output_path, SupportReference, note_template, file_name):
        if verse_data:
            with open(f'{output_path}/{file_name}', 'w', encoding='utf-8') as outfile:
                writer = csv.writer(outfile, delimiter='\t')
                # Write the headers
                writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet'])
                
                for row in verse_data:
                    if len(row) == 4:
                        reference = row[0]
                        snippet = row[1]
                        lexeme = row[2]

                        # Extract chapter and verse from the reference
                        chapter_verse = reference.rsplit(' ', 1)[1]

                        # Create the new row
                        transformed_row = [
                            chapter_verse,  # Reference without the book name
                            '',    # ID: random, unique four-letter and number combination
                            '',             # Tags: blank
                            SupportReference,  # SupportReference: standard link
                            lexeme,         # Quote: lexeme
                            '1',            # Occurrence: the number 1
                            note_template,  # Note: standard note with {gloss}
                            snippet
                        ]

                        # Write the transformed row to the output file
                        writer.writerow(transformed_row)

    def __setup_output(self, book_name, file_name):
        # Construct the output path
        output_path = f'output/{book_name}'

        # Ensure the directory exists
        os.makedirs(output_path, exist_ok=True)

        # Path to the file you want to write
        return f'{output_path}/{file_name}.tsv'


    def _write_output(self, book_name, file, headers, data):
        output_file = self.__setup_output(book_name, file)

        # Write results to a TSV file
        #output_file = self.output_base_dir + '/' + book + "/abstract_nouns.tsv"

        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(headers)  # Column headers
            writer.writerows(data)

        print(f"Data has been written to {output_file}")