import os
import csv
import re
import requests
from collections import defaultdict
from tqdm import tqdm

# Create a directory to store the fetched data
data_dir = "data_files"
os.makedirs(data_dir, exist_ok=True)

# Mapping from book names or codes to acronyms
acronym_mapping = {
    "EXO": "02-EXO",
    "EZR": "15-EZR",
    "JOB": "18-JOB",
    "JON": "32-JON",
    "NEH": "16-NEH",
    "RUT": "08-RUT"
}

# Base URL with placeholder for the acronym
base_url = "https://git.door43.org/unfoldingWord/en_ult/raw/branch/master/{}.usfm"

# Function to fetch data from a given URL and save it to a file
def fetch_and_save_data(url, filename):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response.text)

# Download and store data for each acronym
for acronym in tqdm(acronym_mapping.values(), desc="Downloading data", unit="file"):
    url = base_url.format(acronym)
    filename = os.path.join(data_dir, f"{acronym}.usfm")
    try:
        fetch_and_save_data(url, filename)
    except requests.HTTPError as e:
        print(f"Failed to fetch data from {url}: {e}")

# Verify that all expected files are downloaded
for acronym in acronym_mapping.values():
    filename = os.path.join(data_dir, f"{acronym}.usfm")
    if not os.path.exists(filename):
        print(f"File {filename} is missing!")

# Function to read data from a local file
def read_data(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

# Function to process each row and add the x-lemma information
def process_row(reference, word, data):
    try:
        book, chapter_verse = reference.split()
        chapter, verse = chapter_verse.split(":")
    except ValueError:
        return None

    # Locate the chapter section
    chapter_pattern = re.compile(rf"\\c {chapter}\b")
    chapter_match = chapter_pattern.search(data)
    if not chapter_match:
        return None

    # Locate the verse section within the chapter
    verse_pattern = re.compile(rf"\\v {verse}\b")
    verse_match = verse_pattern.search(data, chapter_match.end())
    if not verse_match:
        return None

    # Search for the x-lemma and x-content within the verse
    lemma_pattern = re.compile(rf'x-lemma="(.*?)".+?x-content="{re.escape(word)}"')
    lemma_match = lemma_pattern.search(data, verse_match.end())
    if lemma_match:
        return lemma_match.group(1)
    return None

# Read the output.tsv file
input_file = "output/abstract_nouns.tsv"
output_file = "output/abstract_nouns_with_lemma.tsv"
lemma_count_file = "output/lemma_count.txt"

# Prepare the new data with x-lemma
new_data = []
lemma_count = defaultdict(int)  # Dictionary to count the occurrences of each lemma

# Read the existing TSV file and process each row
with open(input_file, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter='\t')
    headers = next(reader)
    new_data.append(headers + ["Lemma"])  # Add new header for Lemma

    for row in tqdm(reader, desc="Processing rows", unit="row"):
        reference, word = row
        book_code = reference.split()[0]  # Extract the book code from the reference
        acronym = acronym_mapping.get(book_code)  # Get the corresponding acronym from the mapping

        if not acronym:
            print(f"Failed to find acronym for book: {book_code}")
            new_data.append(row + [""])
            continue

        filename = os.path.join(data_dir, f"{acronym}.usfm")
        try:
            data = read_data(filename)
            lemma = process_row(reference, word, data)
            if lemma:
                new_data.append(row + [lemma])
                lemma_count[lemma] += 1  # Count the lemma
            else:
                new_data.append(row + [""])
        except FileNotFoundError as e:
            print(f"Failed to read data from {filename}: {e}")
            new_data.append(row + [""])

# Write the new data to the output_with_lemma.tsv file
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerows(new_data)

print(f"Data has been written to {output_file}")

# Write lemma counts to lemma_count.txt, ranked by occurrence (highest to lowest)
sorted_lemmas = sorted(lemma_count.items(), key=lambda item: item[1], reverse=True)
with open(lemma_count_file, 'w', encoding='utf-8') as file:
    for lemma, count in sorted_lemmas:
        file.write(f"{lemma}: {count}\n")

print(f"Lemma counts have been written to {lemma_count_file}")
