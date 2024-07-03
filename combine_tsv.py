import csv
from collections import defaultdict
import random
import string
import re
import os

book_name = os.getenv('BOOK_NAME')

# Function to read and parse TSV files
def read_tsv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        headers = next(reader)  # Assuming the first row is headers
        for row in reader:
            data.append(row)
    return data

# Function to read verse texts from ult_book.tsv
def read_verse_texts(file_path):
    verse_texts = {}
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        headers = next(reader)  # Assuming the first row is headers
        for row in reader:
            reference = row[0]  # Assuming first column is Reference (e.g., Esther 1:14)
            verse_text = row[-1]  # Assuming last column is Verse Text
            # Split the reference to remove the book name prefix
            book_name, chapter_verse = reference.rsplit(' ', 1)
            verse_texts[chapter_verse] = verse_text
    return verse_texts

# Function to sort rows by chapter and verse, and then by sequence of snippet in verse text
def sort_rows(tsv_data, verse_texts):
    # Dictionary to store positions of snippets in verse_texts
    snippet_positions = defaultdict(dict)

    # Populate snippet_positions
    for row in tsv_data:
        chapter_verse = row[0]  # Assuming first column is Reference (e.g., "1:14")
        snippet = row[7]  # Assuming eighth column is snippet
        modified_snippet = re.escape(snippet)
        modified_snippet = re.sub(r'…', r'[\\w, ]{1,40}', modified_snippet)
        verse_text = verse_texts.get(chapter_verse, "")
        if verse_text and modified_snippet:
            positions = []
            pattern = re.compile(modified_snippet)
            
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
        return (chapter, verse, positions[0] if positions else float('inf'), snippet)

    # Sort rows
    sorted_data = sorted(tsv_data, key=sort_key)
    return sorted_data

def add_codes(sorted_data):
# Function to generate a random, unique four-letter and number combination
    def generate_random_code(existing_codes):
        while True:
            first_char = random.choice(string.ascii_lowercase)
            remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
            code = first_char + remaining_chars
            if code not in existing_codes:
                existing_codes.add(code)
                return code
            
    # Set to keep track of existing codes to ensure uniqueness
    existing_codes = set()

    modified_sorted_data = []
    for line in sorted_data:
        if len(line) > 1:
            random_code = generate_random_code(existing_codes)
            line[1] = random_code
        modified_sorted_data.append(line)

    # Replace sorted_data with modified_sorted_data
    sorted_data = modified_sorted_data
    return sorted_data

# Function to combine and write sorted data to ult_book.tsv
def combine_and_write(sorted_data, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet'])

        for row in sorted_data:
            writer.writerow(row)

# Main function to process multiple input files
def combine_multiple_tsv(input_files, output_file, verse_text_file):
    # Read verse texts from ult_book.tsv
    verse_texts = read_verse_texts(verse_text_file)

    combined_data = []
    for file_path in input_files:
        if os.path.exists(file_path): # File might not have been created
            data = read_tsv(file_path)
            combined_data.extend(data)

    print(combined_data)

    # Sort combined data
    sorted_data = sort_rows(combined_data, verse_texts)

    add_codes(sorted_data)

    # Write sorted data to output file
    combine_and_write(sorted_data, output_file)
    print(f"Combined and sorted data has been written to {output_file}")

# Example usage:
if __name__ == "__main__":

    # Construct the directory path
    directory_path = f'output/{book_name}'

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    # List of input files to combine
    input_files = [f'{directory_path}/transformed_ab_nouns.tsv', f'{directory_path}/transformed_names.tsv', 
                   f'{directory_path}/transformed_passives.tsv', f'{directory_path}/ordinals.tsv', 
                   f'{directory_path}/go.tsv', f'{directory_path}/transformed_ai_metaphors.tsv',
                   f'{directory_path}/transformed_ai_metonymy.tsv', f'{directory_path}/transformed_ai_rquestions.tsv']

    # Output file name
    output_file = f'{directory_path}/combined_notes.tsv'

    # File containing verse texts
    verse_text_file = f'{directory_path}/ult_book.tsv'

    # Combine and sort
    combine_multiple_tsv(input_files, output_file, verse_text_file)
