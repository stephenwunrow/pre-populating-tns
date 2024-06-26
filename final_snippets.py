import re
import csv
import requests
from bs4 import BeautifulSoup

# Function to read and parse TSV files
def read_tsv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        headers = next(reader)  # Assuming the first row is headers
        for row in reader:
            data.append(row)
    return data, headers

def create_search_dict(input_file):
    data, headers = read_tsv(input_file)
    search_dict = {}
    
    for row in data:
        if len(row) >= 8:  # Ensure the row has at least 8 columns
            reference = row[0]  # Extract the "Reference" column
            snippet = row[7]  # Extract the eighth column ("Snippet")
            
            # Modify the snippet as needed to create a search string
            search_string = modify_snippet(snippet)
            
            # Use a tuple (reference, snippet) as the key
            key = (reference, snippet)
            
            if key in search_dict:
                search_dict[key].append(search_string)
            else:
                search_dict[key] = [search_string]
    
    return search_dict

# Function to modify the snippet
def modify_snippet(snippet):
    # Replace spaces with the desired pattern
    modified_snippet = re.sub(r'[?!.,;:’”]*( |—|…)[“‘]*', r'\\b.*?\\\\w \\b', snippet)
    modified_snippet = re.sub(r'(.+)[!?.,:;”’…]+', r'\1', modified_snippet)
    modified_snippet = re.sub(r'[‘“…](.+)', r'\1', modified_snippet)

    # Surround each word with \b
    modified_snippet = r'\b' + modified_snippet + r'\b'

    # Final regex pattern
    final_pattern = re.compile(r'zaln-s[^z]*?\\w ' + modified_snippet + r'.*?zaln-e', re.DOTALL | re.IGNORECASE)
    return final_pattern

# Example usage
input_file = 'ai_notes.tsv'
search_dict = create_search_dict(input_file)

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

# Get inputs from the user
book_name = input("Enter the book name (e.g., 2 Chronicles): ")
version = input("Enter the version (e.g., ult or ust): ")

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

# Combine all lines into a single string
combined_text = soup.get_text(separator='\n')

def find_snippets(combined_text, search_dict, book_name):
    # Initialize variables
    chapter = None
    verse = None
    verse_data = []
    text_chunks = {}

    # Split the combined text by "\\v" to get verse chunks
    chunks = combined_text.split('\\v')

    for chunk in chunks:
        # Find chapter in the chunk
        chapter_match = re.search(r'\\c (\d+)', chunk)
        if chapter_match:
            chapter = int(chapter_match.group(1))

        # Find verse in the chunk
        verse_match = re.search(r'(\d+)', chunk)
        if verse_match:
            verse = int(verse_match.group(1))

        if chapter is not None and verse is not None:
            verse_ref = f'{chapter}:{verse}'
            text_chunks[verse_ref] = chunk

    for (ref, snippet), search_patterns in search_dict.items():
        if ref in text_chunks:
            chunk = text_chunks[ref]

            # Iterate over each search pattern for the current reference and snippet
            for search_pattern in search_patterns:
                matches = re.findall(search_pattern, chunk)
                
                if matches:
                    match = matches[0]
                    # Find the lexeme in the match
                    lexeme_match = re.findall(r'x-content="([^"]+?)"', match)
                    combined_lexemes = ' '.join(lexeme_match)

                    # Find all glosses in the match
                    gloss_matches = re.findall(r'\\w (.+?)\|', match)
                    combined_gloss = ' '.join(gloss_matches)

                    # Append to verse_data with lexeme, verse reference, snippet, and combined glosses
                    verse_data.append([f'{book_name} {ref}', snippet, combined_lexemes, combined_gloss])
    print(verse_data)
    return verse_data

# Call the function
results = find_snippets(combined_text, search_dict, book_name)

# Print results
for result in results:
    print(result)
