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
passive_flags = {}  # Dictionary

# Combine all lines into a single string
combined_text = soup.get_text(separator='\n')

# Split the combined text by "\\zaln-s"
chunks = combined_text.split('\\zaln-s')

with tqdm(total=len(chunks), desc="Processing Chunks") as pbar:
    for chunk in chunks:
        pbar.update(1)  # Update progress bar

        # Find all matches of the desired pattern
        matches = re.findall(r'x-morph="([^"]*?V[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|', chunk, re.DOTALL)
        if matches:  # Only proceed if there are matches
            for match in matches:
                lexeme = match[1]  # lexeme is the matched group from x-content
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

# Write all collected data to the output file only if there are abstract nouns found
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
    all_text = re.sub(r'(.+\b(am|are|is|was|were|be|being|been)\b.+\b.*?(arisen|awoke|been|borne|beaten|become|begun|bent|bet|bound|bitten|bled|blown|broken|brought|built|burst|bought|caught|chosen|come|cost|crept|cut|dealt|dug|dived|done|drawn|dreamed|dreamt|drunk|driven|eaten|fallen|fed|felt|fought|found|fitted|fit|fled|flung|flown|forbidden|forgotten|forgot|forgiven|frozen|got|gotten|given|gone|grown|hanged|hung|had|heard|hidden|hit|held|hurt|kept|kneeled|knelt|knitted|known|laid|led|left|lent|let|lain|lied|lighted|lit|lost|made|meant|met|paid|pled|proved|proven|put|quit|read|ridden|rung|risen|run|said|seen|sought|sold|sent|set|sewed|sewn|shaken|shone|shined|shot|showed|shown|shrunk|shut|sung|sunk|sat|slain|slept|slid|slit|spoken|spent|spun|spat|spit|split|spread|sprung|stood|stolen|stuck|stung|stunk|stridden|struck|strung|sworn|swept|swollen|swum|swung|taken|taught|torn|told|thought|thrown|understood|waked up|woken up|worn|wed|wept|welcomed|wet|won|wrung|written|ed|en)\b.+)', r'~\1', all_text)
    all_text = re.sub(r'\n[^~].+', r'', all_text)
    all_text = re.sub(r'^[^~].+', r'', all_text)
    all_text = re.sub(r'^\n', r'', all_text)
    all_text = re.sub(r'~', r'', all_text)
    # Split the modified string back into lines
    modified_verse_data = [line.split('\t') for line in all_text.split('\n')]

    with open('en_new_passives.tsv', 'w', encoding='utf-8') as f:
        f.write('Reference\tGlosses\tLexeme\tMorphology\n')
        for line in modified_verse_data:
            f.write('\t'.join(line) + '\n')

    print(f"Data has been written to en_new_passives.tsv")

def generate_report(modified_verse_data, book_name):
    Niphal = []
    Qal_passive = []
    Other = []

    # Define the regex patterns
    niphal_pattern = r'.+\tHe,.*?VN.+'
    qal_passive_pattern = r'.+\tHe,.*?Vqs.+'

    # Process each line to categorize
    for line in modified_verse_data:
        # Join the columns into a single string
        line_str = '\t'.join(line)
        if re.search(niphal_pattern, line_str):
            Niphal.append(line_str)
        elif re.search(qal_passive_pattern, line_str):
            Qal_passive.append(line_str)
        else:
            Other.append(line_str)

    print(Niphal)
    print(Qal_passive)
    print(Other)

    with open('report.txt', 'a', encoding='utf-8') as report_file:
        report_file.write(f'\n\nPassives in English from {book_name} that are not Niphal or Qal passive\n')
        report_file.write('References\tGlosses\tLexeme\tMorphology\n')
        for line in Other:
            report_file.write(f'{line}\n')

generate_report(modified_verse_data, book_name)

# Function to generate a random, unique four-letter and number combination
def generate_random_code():
    first_char = random.choice(string.ascii_lowercase)
    remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return first_char + remaining_chars

# Standard link and note
standard_link = 'rc://*/ta/man/translate/figs-activepassive'
standard_note_template = 'If your language does not use the passive form **{gloss}**, you could express the idea in active form or in another way that is natural in your language. Alternate translation: “alternate_translation”'

# Debugging: Print before writing transformed data
print("Transforming data for transformed_passives.tsv")

# Write to the output file only if rows exist after filtering
if modified_verse_data:
    with open('transformed_passives.tsv', 'w', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        # Write the headers
        writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note'])
        
        for row in modified_verse_data:
            if len(row) == 4:
                reference = row[0]
                gloss = row[1]
                lexeme = row[2]

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
                    standard_note_template.format(gloss=gloss)  # Note: standard note with {gloss}
                ]

                # Write the transformed row to the output file
                writer.writerow(transformed_row)

    print(f"Transformed data has been written to transformed_passives.tsv")
