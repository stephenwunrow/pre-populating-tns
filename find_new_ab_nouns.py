import requests
from bs4 import BeautifulSoup
import re

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

# Initialize variables
chapter = None
verse = None
verse_data = []

lemmas = []
with open('output/lemma_count.txt', 'r') as file:
    for line in file:
        for word in line.split():
            lemma = word.split(':')[0].strip()
            lemmas.append(lemma)

# Build the search patterns
patterns = {lemma: re.compile(rf'x-lemma="{lemma}".+?zaln-s', re.DOTALL) for lemma in lemmas}

# Combine all lines into a single string
combined_text = soup.get_text(separator='\n')

# Split the combined text by verses
verse_lines = combined_text.split('\\v ')

for verse_line in verse_lines:
    if '\\c ' in verse_line:
        chapter_match = re.search(r'\\c (\d+)', verse_line)
        if chapter_match:
            chapter = int(chapter_match.group(1))
    verse_match = re.match(r'(\d+)', verse_line)
    if verse_match:
        verse = int(verse_match.group(1))
        glosses = {lemma: [] for lemma in lemmas}
        for lemma, pattern in patterns.items():
            matches = pattern.findall(verse_line)
            for match in matches:
                gloss_list = re.findall(r'\\w (.+?)\|', match)
                if gloss_list:
                    # Join glosses into a single string
                    gloss_str = " ".join(gloss_list)
                    # Append to verse_data with lemma, verse reference, and glosses
                    verse_data.append(f'{book_name} {chapter}:{verse}\t{lemma}\t{gloss_str}')

# Define the cleanup function (unchanged)
def cleanup_lines(data):
    cleaned_data = []
    for line in data:
        line = re.sub(r'( )([.,;’”?!—})]+)', r'\2', line)
        line = re.sub(r'([({“‘—]+)( )', r'\1', line)
        line = line.strip()
        cleaned_data.append(line)
    return cleaned_data

# Clean the data (unchanged)
cleaned_data = cleanup_lines(verse_data)

# Write the parsed verses to output.tsv (unchanged)
with open('output/new_ab_nouns.tsv', 'w', encoding='utf-8') as f:
    f.write('Reference\tLemma\tGloss\n')  # write the header row
    for verse in cleaned_data:
        f.write(verse + '\n')
