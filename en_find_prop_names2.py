import requests
from bs4 import BeautifulSoup
import re
import csv
from tqdm import tqdm
import random
import string

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
name_count = {}  # Dictionary to count occurrences of each name

# Combine all lines into a single string
combined_text = soup.get_text(separator='\n')

# Split the combined text by "\\zaln-s"
chunks = combined_text.split('\\zaln-s')

# tqdm setup for chunks
with tqdm(total=len(chunks), desc="Processing Chunks") as pbar:
    for chunk in chunks:
        pbar.update(1)  # Update progress bar

        matches = re.findall(r'x-morph="[^"]*?[^V]Np[^"]*?".+?x-content="([^"]+?)".+\\w .+?\|', chunk, re.DOTALL)
        if matches:  # Only proceed if there are matches
            for match in matches:
                lexeme = match

                # Find all glosses in the chunk
                gloss_matches = re.findall(r'\\w (.+?)\|', chunk)
                if gloss_matches:
                    # Combine all glosses into a single string
                    combined_gloss = ' '.join(gloss_matches)
                    mod_gloss = re.sub(r'\b(And|But|Then|Now|In|The)\b ', r'', combined_gloss)
                    names_search = re.findall(r'(\b[A-Z]\w+?\b)', mod_gloss)
                    if names_search:
                        for word in names_search:
                            name = word

                # Append to verse_data with lexeme, verse reference, and name
                verse_data.append(f'{book_name} {chapter}:{verse}\t{name}\t{lexeme}\t{combined_gloss}')

                # Count the occurrence of this name
                if name in name_count:
                    name_count[name] += 1
                else:
                    name_count[name] = 1

        # Find chapter in the chunk
        chapter_match = re.search(r'\\c (\d+)', chunk)
        if chapter_match:
            chapter = int(chapter_match.group(1))
        
        # Find verse in the chunk
        verse_match = re.search(r'\\v (\d+)', chunk)
        if verse_match:
            verse = int(verse_match.group(1))

# Function to extract words from HTML content
def extract_words_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    a_tags = soup.find_all('a', href=True, title=lambda x: x and x.endswith('.md'))
    words = [a_tag['title'].split('.md')[0] for a_tag in a_tags]
    return words

# Function to fetch words from a URL
def extract_words_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.text
        return extract_words_from_html(html_content)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return []

# URL to scrape
url = 'https://git.door43.org/unfoldingWord/en_tw/src/branch/master/bible/names'

# Define a list of custom words to remove
custom_words_to_remove = ["and", "but", "then", "in", "now"]

# Extract words from the URL
scraped_names = extract_words_from_url(url)

# Combine the custom list with the scraped names, ignoring case
all_names_to_remove = [name.lower() for name in scraped_names + custom_words_to_remove]

# Filter rows to exclude names found in the combined list of names to remove
def filter_rows(rows, all_names_to_remove):
    filtered_rows = []
    for row in rows:
        if row[1].lower() not in all_names_to_remove:
            filtered_rows.append(row)
    return filtered_rows

# Read the input file again after writing to en_new_names.tsv
with open('en_new_names.tsv', 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    # Skip the header
    next(reader)
    rows = [row for row in reader]

# Filter rows
filtered_rows = filter_rows(rows, all_names_to_remove)

# Write all collected data to the output file only if there are abstract nouns found
if verse_data:
    with open('en_new_names.tsv', 'w', encoding='utf-8') as f:
        f.write('Reference\tName\tLexeme\tCombined Gloss\n')
        for line in verse_data:
            f.write(line + '\n')

    print(f"Data has been written to en_new_names.tsv")

# Write the names and their frequency to report.txt, excluding custom words to remove
sorted_name_count = sorted(name_count.items(), key=lambda item: item[1], reverse=True)

# Append to the file instead of replacing existing content
with open('report.txt', 'a', encoding='utf-8') as report_file:
    report_file.write(f'\n\nNames from {book_name}\n')
    report_file.write('Name\tFrequency\n')
    for name, count in sorted_name_count:
        if name.lower() not in all_names_to_remove:
            report_file.write(f'{name}\t{count}\n')


# Function to generate a random, unique four-letter and number combination
def generate_random_code():
    first_char = random.choice(string.ascii_lowercase)
    remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return first_char + remaining_chars

# Standard link and note
standard_link = 'rc://*/ta/man/translate/translate-names'
standard_note_template = 'The word **{name}** is the name of a ______.'
name_occurrence = {}

# Write to the output file only if rows exist after filtering
if filtered_rows:
    with open('transformed_names.tsv', 'w', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        # Write the headers
        writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet'])
        
        for row in filtered_rows:
            if len(row) == 4:
                reference = row[0]
                name = row[1]
                lexeme = row[2]
                snippet = row[3]

                # Extract chapter and verse from the reference
                chapter_verse = reference.split(' ', 1)[1]

                # Generate a random code
                random_code = generate_random_code()

                # Create the new row
                transformed_row = [
                    chapter_verse,  # Reference without the book name
                    random_code,    # ID: random, unique four-letter and number combination
                    '',             # Tags: blank
                    standard_link,  # SupportReference: standard link
                    lexeme,         # Quote: lexeme
                    '1',            # Occurrence: the number 1
                    standard_note_template.format(name=name),  # Note: standard note with {name}
                    snippet
                ]
                if name not in name_occurrence:
                    # Write the transformed row to the output file
                    writer.writerow(transformed_row)
                    name_occurrence[name] = True
                elif name in name_occurrence:
                    continue

    print(f"Data has been transformed and written to transformed_names.tsv")
else:
    print("No valid rows to write to transformed_names.tsv")