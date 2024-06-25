import requests
from bs4 import BeautifulSoup
import re
import os

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
    "Song": "22-SNG",
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

# Get the book name from the user
book_name = os.getenv('BOOK_NAME')
version = os.getenv('VERSION')

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

# Initialize variables
chapter = None
verse = None
verse_words = []
verse_data = []

# Regex pattern to capture words, punctuation, and curly brace content
pattern = re.compile(r'\\w ([^|]*?)\||([“‘{(]+)\\|\*([)}.,;!?’”—]+)')

# Split the content into lines and process
for line in soup.get_text().splitlines():
    if line.startswith('\\c '):
        if verse_words:
            # Append previous verse words to verse_data
            verse_data.append(f'{book_name} {chapter}:{verse}\t{" ".join(verse_words)}')
        match = re.search(r'\\c\s+(\d+)', line)
        if match:
            chapter = int(match.group(1))
        verse_words = []
    elif line.startswith('\\v '):
        if verse_words:
            # Append previous verse words to verse_data
            verse_data.append(f'{book_name} {chapter}:{verse}\t{" ".join(verse_words)}')
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
                verse_words.extend(words)
            if match[1]:  # punctuation before zaln
                verse_words.append(match[1])
            if match[2]:  # punctuation after zaln
                verse_words.append(match[2])

# Append the last verse
if verse_words:
    verse_data.append(f'{book_name} {chapter}:{verse}\t{" ".join(verse_words)}')

# Define the cleanup function
def cleanup_lines(data):
    cleaned_data = []
    for line in data:
        line = re.sub(r'( )([.,;’”?!—})]+)', r'\2', line)
        line = re.sub(r'([({“‘—]+)( )', r'\1', line)
        line = line.strip()
        cleaned_data.append(line)
    return cleaned_data

# Clean the data
cleaned_data = cleanup_lines(verse_data)

# Write the parsed verses to ult_book.tsv

# Construct the directory path
directory_path = f'output/{book_name}'

# Ensure the directory exists
os.makedirs(directory_path, exist_ok=True)

with open(f'{directory_path}/ult_book.tsv', 'w', encoding='utf-8') as f:
    f.write('Reference\tVerse\n')  # write the header row
    for verse in cleaned_data:
        f.write(verse + '\n')
