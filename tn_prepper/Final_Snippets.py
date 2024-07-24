from TNPrepper import TNPrepper

import re
import csv
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from dotenv import load_dotenv
import os

load_dotenv()

class Final_Snippets(TNPrepper):
    def __init__(self, book_name, version, acronym, input_file):
        super().__init__()

        self.book_name = book_name
        self.version = version
        self.acronym = acronym
        self.input_file = input_file

    # Function to read and parse TSV files
    def __read_ai_notes(self, file_path):
        data = []
        with open(file_path, 'r', encoding='utf-8') as tsvfile:
            reader = csv.reader(tsvfile, delimiter='\t')
            headers = next(reader)  # Assuming the first row is headers
            for row in reader:
                data.append(row)
        return data, headers

    def _get_hbo(self, book_name, acronym):

        # URL of the file to download
        url = f"https://git.door43.org/unfoldingWord/hbo_uhb/raw/branch/master/{acronym}.usfm"

        # Function to get the content of the file
        def __get_file_content(url):
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                return ''

        # Get the file content
        file_content = __get_file_content(url)

        # Process the file content
        soup = BeautifulSoup(file_content, 'html.parser')

        # Combine all lines into a single string
        combined_text = soup.get_text(separator='\n')

        return combined_text
    
    def _find_unique_numbers(self, combined_text):
        # Initialize variables
        chapter = None
        verse = None
        unique_numbers = []
        current_number = 1  # Initialize a counter for consecutive numbering

        # Split the combined text by "\\v" to get verse chunks
        chunks = combined_text.split('\\v ')

        for chunk in chunks:

            # Find verse in the chunk
            verse_match = re.search(r'(\d+)', chunk)
            if verse_match:
                verse = int(verse_match.group(1))

            # Find Hebrew words in the chunk
            hebrew_words = re.findall(r'\\w (.+?)\|', chunk)

            if chapter is not None and verse is not None:
                verse_ref = f'{chapter}:{verse}'

                # Initialize a dictionary to keep track of word occurrences within the same verse
                word_occurrences = defaultdict(int)

                for word in hebrew_words:
                    word_occurrences[word] += 1
                    occurrence_number = word_occurrences[word]

                    unique_numbers.append((verse_ref, word, current_number, occurrence_number))
                    current_number += 1  # Increment the counter

                        # Find chapter in the chunk
            chapter_match = re.search(r'\\c (\d+)', chunk)
            if chapter_match:
                chapter = int(chapter_match.group(1))

        return unique_numbers
    
    def __combine_entries(self, ult_dict):
        # Add an index column starting at 1
        indexed_entries = [[i + 1] + list(entry) for i, entry in enumerate(ult_dict)]
        
        # Dictionary to store combined entries
        combined_entries = []
        
        # Group entries by (verse_ref, gloss, chunk_number)
        from collections import defaultdict
        grouped_entries = defaultdict(list)
        
        for entry in indexed_entries:
            index, verse_ref, hebrew_word, number, gloss, chunk_number = entry
            
            key = (verse_ref, gloss, chunk_number)
            grouped_entries[key].append((index, verse_ref, hebrew_word, number, gloss, chunk_number))
        
        # Process each group
        for key, entries in grouped_entries.items():
            if len(entries) == 1:
                # If there's only one entry, add it directly
                combined_entries.append(entries[0])
            else:
                # Sort entries by index
                entries.sort(key=lambda x: x[0])
                
                # Check if hebrew_word is the same for all entries in the group
                same_hebrew_word = all(entry[2] == entries[0][2] for entry in entries)
                
                if same_hebrew_word:
                    # If hebrew_word is the same, add each entry separately
                    combined_entries.extend(entries)
                else:
                    # If hebrew_word differs, combine hebrew_word and number entries
                    combined_entry = list(entries[0])  # Start with the first entry
                    combined_hebrew_words = [entries[0][2]]  # List to store combined hebrew_words
                    combined_numbers = [str(entries[0][3])]  # List to store combined numbers
                    
                    for entry in entries[1:]:
                        combined_hebrew_words.append(entry[2])
                        combined_numbers.append(str(entry[3]))  # Convert number to string
                    
                    # Combine hebrew_words and numbers
                    combined_entry[2] = ' '.join(combined_hebrew_words)
                    combined_entry[3] = ' '.join(combined_numbers)
                    
                    combined_entries.append(tuple(combined_entry))  # Add as tuple for immutability
        
        # Sort combined_entries by the index column
        combined_entries.sort(key=lambda x: x[0])
        
        # Remove the index column
        final_entries = [entry[1:] for entry in combined_entries]
        
        return final_entries

    def _construct_ult_dict(self, version, acronym, unique_numbers):
        # URL of the file to download
        url = f"https://git.door43.org/unfoldingWord/en_{version}/raw/branch/master/{acronym}.usfm"

        # Get the file content
        file_content = self._get_file_content(url)

        # Process the file content
        soup = BeautifulSoup(file_content, 'html.parser')

        # Combine all lines into a single string
        combined_text = soup.get_text(separator='\n')

        ult_dict = []
        text_chunks = {}
        chapter = None
        verse = None

        # Split the combined text by "\\v" to get verse chunks
        chunks = combined_text.split('\\v')

        for chunk in chunks:

            # Find verse in the chunk
            verse_match = re.search(r'(\d+)', chunk)
            if verse_match:
                verse = int(verse_match.group(1))

            if chapter is not None and verse is not None:
                verse_ref = f'{chapter}:{verse}'
                text_chunks[verse_ref] = chunk

            # Find chapter in the chunk
            chapter_match = re.search(r'\\c (\d+)', chunk)
            if chapter_match:
                chapter = int(chapter_match.group(1))

        for verse_ref, hebrew_word, number, occurrence_number in unique_numbers:
            if verse_ref in text_chunks:

                chunk = text_chunks[verse_ref]

                lexeme_chunks = chunk.split('-e\\*')

                chunk_number = 0  # Initialize a counter for consecutive numbering

                for lexeme_chunk in lexeme_chunks:

                    chunk_number += 1

                    escaped_hebrew_word = re.escape(hebrew_word)
                    hebrew_pattern = re.compile(rf'zaln-s.+?x-occurrence="{occurrence_number}" x-occurrences="\d" x-content="{escaped_hebrew_word}".+?\\w\*\\zaln', re.DOTALL)
                    matches = hebrew_pattern.findall(lexeme_chunk)
                    
                    for match in matches:
                        
                        # Find instances of certain English words within the match
                        gloss_pattern = re.compile(r'\\w \b(.+?)\b\|')
                        gloss_matches = gloss_pattern.findall(match)
                        
                        for gloss in gloss_matches:
                            ult_dict.append([verse_ref, hebrew_word, number, gloss, chunk_number])
                
                ult_dict_combined = self.__combine_entries(ult_dict)

                # Sort ult_dict_combined by chapter, verse, and then by chunk_number
                ult_dict_sorted = sorted(ult_dict_combined, key=lambda x: (self._parse_verse_ref(x[0]), x[4]))

        return ult_dict_sorted
    
    def __combine_possessives(self, ult_dict):
        ult_dict_combined = []
        temp_dict = {}

        i = 0
        while i < len(ult_dict):
            entry = list(ult_dict[i])  # Convert tuple to list
            reference = entry[0]
            hebrew_word = entry[1]
            unique_number = entry[2]
            gloss = entry[3]
            chunk_number = entry[4]
            
            if gloss == 's':
                if i > 0:
                    previous_entry = list(ult_dict[i - 1])  # Convert tuple to list
                    prev_reference = previous_entry[0]
                    prev_hebrew_word = previous_entry[1]
                    prev_unique_number = previous_entry[2]
                    prev_gloss = previous_entry[3]
                    prev_chunk_number = previous_entry[4]

                    if (reference == prev_reference and
                        chunk_number == prev_chunk_number and 
                        unique_number == prev_unique_number and 
                        hebrew_word == prev_hebrew_word):
                        
                        # Add '’s' to the gloss of the previous entry
                        previous_entry[3] = prev_gloss + '’s'
                        # Update the previous entry in ult_dict_combined
                        ult_dict_combined[-1] = previous_entry
                        # Skip the current entry
                        i += 1
                        continue
            
            ult_dict_combined.append(entry)
            i += 1

        return ult_dict_combined

    def _find_sequence(self, ult_dict_combined, input_file):
        data, headers = self.__read_ai_notes(input_file)
        snippet_data = []
        
        # Step 1: Create a dictionary with verse_ref as key and concatenated string of gloss words as value
        gloss_dict = {}
        for entry in ult_dict_combined:
            verse_ref = entry[0]
            gloss_word = entry[3]
            chunk_number = entry[4]
            
            if verse_ref not in gloss_dict:
                gloss_dict[verse_ref] = []
            
            # Append a tuple of (gloss_word, chunk_number) to the list
            gloss_dict[verse_ref].append((gloss_word, chunk_number))

        # Convert the list of tuples to a concatenated string for each verse_ref
        final_gloss_dict = {verse_ref: ' '.join([f'{gloss_word} {chunk_number}' for gloss_word, chunk_number in gloss_words]) for verse_ref, gloss_words in gloss_dict.items()}

        # Step 2: Find sequences
        for row in data:
            verse_ref = row[0]
            phrase = row[7].strip()
            lower_phrase = phrase.lower()
            mod_phrase = re.sub(r'[.,:;”‘“!?—*]', r'', lower_phrase)
            mod_phrase = re.sub('s’', 's', mod_phrase)
            mod_phrase = re.sub('…', ' .+?', mod_phrase)
            search_phrase = re.sub(r' ', r' \\d+ ', mod_phrase)
            search_phrase = search_phrase + ' \\d+'

            chunk_numbers = []
            numbers = []

            if verse_ref in final_gloss_dict:
                gloss_text = final_gloss_dict[verse_ref].lower()
                matches = re.findall(search_phrase, gloss_text)
                if matches:
                    for match in matches:
                        pairs = re.findall(r'(\w+) (\d+)', match)
                        if pairs:
                            for gloss_word, chunk_number in pairs:
                                for entry in ult_dict_combined:
                                    if entry[0] == verse_ref and entry[3].lower() == gloss_word.lower() and entry[4] == int(chunk_number):
                                        entry_2_str = str(entry[2])
                                        if ' ' in entry_2_str:
                                            for num in entry_2_str.split():
                                                numbers.append(int(num))
                                        else:
                                            numbers.append(int(entry[2]))
                                        chunk_numbers.append(int(entry[4]))

                # Sort numbers and chunk_numbers numerically
                numbers.sort()
                chunk_numbers.sort()

                snippet_data.append([verse_ref, phrase, numbers, chunk_numbers])
        
        return snippet_data
    
    def _write_origl_and_snippet(self, snippet_data, ult_dict_combined, unique_numbers):
        processed_data = []

        # Step 1: Include each unique number only once within brackets
        for row in snippet_data:
            verse_ref = row[0]
            phrase = row[1]
            numbers = sorted(set(row[2]))  # Remove duplicates
            chunk_numbers = sorted(set(row[3]))  # Remove duplicates

            # Step 2: Replace "number" with the corresponding Hebrew word
            hebrew_words = []
            for num in numbers:
                for entry in unique_numbers:
                    if entry[2] == num:
                        hebrew_words.append(entry[1])
                        break
            
            # Step 3: Replace "chunk_number" with the corresponding English words
            english_words = []
            for chunk_num in chunk_numbers:
                for entry in ult_dict_combined:
                    if entry[0] == verse_ref and int(entry[4]) == chunk_num:
                        english_words.append(entry[3])
            
            # Join hebrew_words with '&' where numbers are not consecutive
            hebrew_phrase = ''
            for i, word in enumerate(hebrew_words):
                if i > 0 and numbers[i] != numbers[i - 1] + 1:
                    hebrew_phrase += f' & {word}'
                else:
                    hebrew_phrase += f' {word}'

            hebrew_phrase = hebrew_phrase.strip()

            # Join the English words by a space
            english_phrase = ' '.join(english_words)

            # Append the processed row to processed_data
            processed_data.append([verse_ref, phrase, hebrew_phrase, english_phrase])
        
        return processed_data
    

    def _add_punctuation(self, origl_and_snippet):
        book_file = f'output/{book_name}/ult_book.tsv'
        data, headers = self.__read_ai_notes(book_file)
        data_str = ' '.join([' '.join(row) for row in data])

        for row in origl_and_snippet:
            verse_ref = row[0]
            phrase = row[1]
            hebrew_words = row[2]
            english_words = row[3]

            # Create a regex pattern to match the phrase with punctuation
            search_phrase = re.sub(r' ', '[ .,;’”“‘!?:—]+', english_words)

            # Find all matches of the search phrase in the data string
            matches = re.findall(search_phrase, data_str)
            if matches:
                # Update english_words with the first match found
                row[3] = matches[0]

        return origl_and_snippet
    
    def _process_ai_notes(self, input_file, origl_and_snippet):
        ai_notes, headers = self.__read_ai_notes(input_file)
        
        # Iterate over origl_and_snippet
        for row in origl_and_snippet:
            reference = row[0]
            snippet = row[1]
            hebrew_words = row[2]
            context = row[3]
            
            # Find corresponding line in ai_notes using reference and snippet
            for ai_row in ai_notes:
                if not re.match(r'\d', ai_row[0]):
                    ai_notes.remove(ai_row)
                if ai_row[0] == reference and ai_row[7] == snippet:
                    # Replace "Quote" (row 5 in ai_notes) with english_words (row 3 in origl_and_snippet)
                    ai_row[4] = hebrew_words

                    # Locate snippet in context and get pre-words and post-words
                    snippet_index = context.lower().find(snippet)
                    if snippet_index != -1:
                        pre_words = context[:snippet_index].strip('] [\'')
                        post_words = context[snippet_index + len(snippet):].strip('] [\'')
                        
                        # Add pre-words and post-words to the quoted text in row 7 of ai_notes
                        quote_text = re.findall(r'Alternate translation: “(.+?)”', ai_row[6])
                        new_AT = f'{pre_words} {quote_text} {post_words}'.strip('] [\'"')
                        new_AT = re.sub(r'\'s', r'’s', new_AT)
                        new_AT = re.sub(r'[\[\'\]]', r'', new_AT)
                        ai_row[6] = re.sub(r'(.+Alternate translation: “).+(”)', rf'\1{new_AT}\2', ai_row[6])

        return ai_notes
    

    # Function to sort rows by chapter and verse, and then by sequence of snippet in verse text
    def _sort_rows(self, ai_notes, book_name):

        verse_text_file = f'output/{book_name}/ult_book.tsv'

        # Function to read verse texts from ult_book.tsv
        def read_verse_texts(verse_text_file):
            verse_texts = {}
            with open(verse_text_file, 'r', encoding='utf-8') as tsvfile:
                reader = csv.reader(tsvfile, delimiter='\t')
                headers = next(reader)  # Assuming the first row is headers
                for row in reader:
                    reference = row[0]  # Assuming first column is Reference (e.g., Esther 1:14)
                    verse_text = row[-1]  # Assuming last column is Verse Text
                    # Split the reference to remove the book name prefix
                    book_name, chapter_verse = reference.rsplit(' ', 1)
                    verse_texts[chapter_verse] = verse_text
            return verse_texts
        
        verse_texts = read_verse_texts(verse_text_file)

        # Dictionary to store positions of snippets in verse_texts
        snippet_positions = defaultdict(dict)

        # Populate snippet_positions
        for row in ai_notes:
            chapter_verse = row[0]  # Assuming first column is Reference (e.g., "1:14")
            snippet = row[7]  # Assuming eighth column is snippet
            modified_snippet = re.escape(snippet)
            modified_snippet = re.sub(r'…', r'[\\w, ]{1,40}', modified_snippet)
            verse_text = verse_texts.get(chapter_verse, "")
            if verse_text and modified_snippet:
                positions = []
                pattern = re.compile(modified_snippet, re.IGNORECASE)
                
                for match in pattern.finditer(verse_text):
                    positions.append(match.start())
                
                snippet_positions[chapter_verse][snippet] = positions

        # Sort function
        def sort_key(row):
            chapter_verse = row[0]  # Assuming first column is Reference (e.g., "1:14")
            snippet = row[7]  # Assuming eighth column is snippet
            
            # Split chapter_verse into chapter and verse components
            chapter, verse = map(int, chapter_verse.split(':'))

            # Get positions of snippet in the verse_text for this chapter_verse
            positions = snippet_positions.get(chapter_verse, {}).get(snippet, [])

            # Return tuple for sorting: (chapter, verse, first position of snippet or large number, snippet)
            return (chapter, verse, positions[0] if positions else float('inf'), -len(snippet), snippet)

        # Sort rows
        sorted_data = sorted(ai_notes, key=sort_key)
        for row in sorted_data:
            del row[7]
        return sorted_data

    
    def run(self):

        combined_text = self._get_hbo(book_name, acronym)
        unique_numbers = self._find_unique_numbers(combined_text)

        data = unique_numbers
        headers = ['Reference', 'Hebrew word', 'Unique number', 'Occurrence number']
        file = '1_unique_numbers.tsv'
        self._write_output(book_name, file, headers, data)

        ult_dict = self._construct_ult_dict(version, acronym, unique_numbers)
        ult_dict_combined = self.__combine_possessives(ult_dict)

        data = ult_dict_combined
        headers = ['Reference', 'Hebrew word', 'Unique number', 'Gloss', 'Chunk number']
        file = '2_ult_dict.tsv'
        self._write_output(book_name, file, headers, data)

        snippet_data = self._find_sequence(ult_dict_combined, input_file)
        
        data = snippet_data
        headers = ['Reference', 'Phrase', 'Unique numbers', 'Chunk numbers']
        file = '3_snippet_data.tsv'
        self._write_output(book_name, file, headers, data)

        origl_and_snippet = self._write_origl_and_snippet(snippet_data, ult_dict_combined, unique_numbers)

        origl_and_snippet = self._add_punctuation(origl_and_snippet)

        data = origl_and_snippet
        headers = ['Reference', 'Snippet', 'Hebrew phrase', 'English phrase']
        file = '4_origl_and_snippet.tsv'
        self._write_output(book_name, file, headers, data)

        ai_notes = self._process_ai_notes(input_file, origl_and_snippet)

        sorted_data = self._sort_rows(ai_notes, book_name)

        data = sorted_data
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note']
        file = 'final_notes.tsv'
        self._write_output(book_name, file, headers, data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

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

    if book_name in acronym_mapping:
        acronym = acronym_mapping[book_name]

    input_file = f'output/{book_name}/ai_notes.tsv'

    final_snippets_instance = Final_Snippets(book_name, version, acronym, input_file)
    final_snippets_instance.run()