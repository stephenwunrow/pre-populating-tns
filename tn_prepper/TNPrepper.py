import os
import csv
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from pprint import pprint
import time


class TNPrepper():
    def __init__(self):
        self.output_base_dir = 'output'

    # Function to get the content of the file
    def _get_file_content(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return ''

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

        # Get the file content
        file_content = self._get_file_content(url)

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
    def _transform_data(self, verse_data, support_reference, note_template):
        if verse_data:

            transformed_data = list()
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
                        '',  # ID: random, unique four-letter and number combination
                        '',  # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,  # Quote: lexeme
                        '1',  # Occurrence: the number 1
                        note_template,  # Note: standard note with {gloss}
                        snippet
                    ]

                    transformed_data.append(transformed_row)

            return transformed_data

    def __setup_output(self, book_name, file_name):
        # Construct the output path
        output_path = f'output/{book_name}'

        # Ensure the directory exists
        os.makedirs(output_path, exist_ok=True)

        if '.tsv' not in file_name:
            file_name += '.tsv'

        # Path to the file you want to write
        return f'{output_path}/{file_name}'

    def _get_book_name(self):
        if os.getenv('BOOK_NAME'):
            book_name = os.getenv('BOOK_NAME')
        else:
            # Prompt the user for book name
            book_name = input("Enter the book name (e.g., 2 Chronicles): ")
        return book_name

    def _read_tsv(self, file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            return list(reader)

    def _write_output(self, book_name, file, headers, data, fieldnames=None):

        output_file = self.__setup_output(book_name, file)

        # Write results to a TSV file
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            if fieldnames:
                writer = csv.DictWriter(file, delimiter='\t', fieldnames=fieldnames)
                writer.writeheader()
            else:
                writer = csv.writer(file, delimiter='\t')
                writer.writerow(headers)  # Column headers

            writer.writerows(data)

        print(f"Data has been written to {output_file}")




    # SupportReference specific functions
    ## figs_go
    def _figs_go(self, verse_data):
        # Write all collected data to the output file only if there are abstract nouns found
        modified_verse_data = list()
        if verse_data:
            # Join all lines into a single string for search and replace
            all_text = '\n'.join(['\t'.join(line) for line in verse_data])

            # Define the search and replace pattern
            search_pattern = r'.+? (\d+:\d+)\t(.+?)\t(.+?)\t.+\n(.+? \1\t)(.+?\t\3.+)'
            replace_with = r'\4\2…\5'

            # Apply search and replace until no changes are detected
            while True:
                new_text = re.sub(search_pattern, replace_with, all_text)
                if new_text == all_text:
                    break
                all_text = new_text
            all_text = re.sub(r'(.+\b(go|goes|gone|going|went|come|comes|coming|came|take|takes|taken|taking|took|bring|brings|bringing|brought)\b)', r'~\1', all_text)
            all_text = re.sub(r'\n[^~].+', r'', all_text)
            all_text = re.sub(r'^[^~].+', r'', all_text)
            all_text = re.sub(r'^\n', r'', all_text)
            all_text = re.sub(r'~', r'', all_text)
            # Split the modified string back into lines
            modified_verse_data = [line.split('\t') for line in all_text.split('\n')]

        return modified_verse_data
    
    def _transform_figs_go(self, modified_verse_data, support_reference):
        word_mapping = {
            "goes": "comes",
            "gone": "come",
            "going": "coming",
            "go": "come",
            "went": "came",
            "has come": "has gone",
            "have come": "have gone",
            "had come": "had gone",
            "comes": "goes",
            "coming": "going",
            "came": "went",
            "come": "go",
            "takes": "brings",
            "taken": "brought",
            "taking": "bringing",
            "took": "brought",
            "take": "bring",
            "has brought": "has taken",
            "have brought": "have taken",
            "had brought": "had taken",
            "brings": "takes",
            "bringing": "taking",
            "bring": "take",
            "brought": "took"
        }

        if modified_verse_data:
            transformed_data = []
            for row in modified_verse_data:
                if len(row) == 4:
                    reference = row[0]
                    snippet = row[1]
                    lexeme = row[2]

                    key = ""
                    text = ""

                    for word in word_mapping:
                        if word in snippet:
                            key = word
                            key = re.sub(r'(has|have|had) ', r'', key)
                            text = word_mapping[key]
                            text = re.sub(r'(has|have|had) ', r'', text)
                            break  # Stop searching once a match is found
                    
                    AT = re.sub(rf'(.*){key}(.*)', rf'\1{text}\2', snippet)

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    note_template = f"In a context such as this, your language might say “{text}” instead of **{key}**. Alternate translation: “{AT}”"

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',    # ID: random, unique four-letter and number combination
                        '',             # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,         # Quote: lexeme
                        '1',            # Occurrence: the number 1
                        note_template.format(key=key, text=text, AT=AT),  # Note: standard note with {gloss}
                        snippet
                    ]
                    transformed_data.append(transformed_row)

            return transformed_data
        


    # LLM query stuff

    # Function to wait between queries
    def __wait_between_queries(self, seconds):
        print(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)

    # Function to query the LLM
    def _query_llm(self, context, prompt):
        combined_prompt = f"Verse and context:\n{context}\n\nPrompt:\n{prompt}"
        response = None

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a bible-believing scholar. You are analyzing a text and providing answers that exactly match that text. You should not provide explanations and interpretation unless you are specifically asked to do so."
                    },
                    {
                        "role": "user",
                        "content": combined_prompt,
                    }
                ],
                model=self.groq_model,
                temperature = 0.7

            )
            response = chat_completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"Request failed: {e}")
            print(f"Failed to get response for prompt: {prompt}")

        finally:
            print(combined_prompt)
            print(f'Response: {response}')
            print('---')

            # Waiting, to stay below our request limit (30 reqs/minute)
            self.__wait_between_queries(2)

            return response