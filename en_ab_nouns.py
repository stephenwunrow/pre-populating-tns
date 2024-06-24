import requests
import csv
import re
from collections import defaultdict

# List of three-letter acronyms to replace "JON" in the URL
acronyms = ["EXO", "EST", "EZR", "JOB", "JON", "NEH", "RUT", "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"]  # Add more acronyms as needed

# Base URL with placeholder for the acronym
base_url = "https://git.door43.org/unfoldingWord/en_tn/raw/branch/master/tn_{}.tsv"

# Function to fetch data from a given URL
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.text

# Function to process data and extract relevant information based on a regex pattern
def process_data(data, pattern, book_name, ab_noun_counts):
    result = []
    rows = data.splitlines()
    for row in rows:
        match = re.search(pattern, row)
        if match:
            reference, snippet, note = match.groups()
            # Include the book name in the reference
            full_reference = f"{book_name} {reference}"
            # Check for abstract nouns
            ab_nouns = re.findall(r'\*\*(.+?)\*\*', note) if note else []
            if ab_nouns:
                for ab_noun in ab_nouns:
                    # Split at commas if there are multiple abstract nouns in one entry
                    nouns = [noun.strip() for noun in ab_noun.split(',')]
                    for noun in nouns:
                        result.append([full_reference, snippet, noun])
                        ab_noun_counts[noun] += 1
            else:
                result.append([full_reference, snippet])
    return result

# Regex pattern to match the desired format
pattern = re.compile(r'(\d+:\d+)\t.+?\t.*?\trc://\*/ta/man/translate/figs-abstractnouns\t(.+?)\t\d\t(.+)', re.IGNORECASE)

# Main script
all_results = []
ab_noun_counts = defaultdict(int)

for acronym in acronyms:
    url = base_url.format(acronym)
    try:
        data = fetch_data(url)
        results = process_data(data, pattern, acronym, ab_noun_counts)
        all_results.extend(results)
    except requests.HTTPError as e:
        print(f"Failed to fetch data from {url}: {e}")

# Write detailed results to a TSV file
output_file = "en_abstract_nouns.tsv"

with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(["Reference", "Word", "Abstract Noun"])  # Column headers
    writer.writerows(all_results)

print(f"Detailed data has been written to {output_file}")

# Write abstract noun counts to a new TSV file, sorted by count in descending order
ab_noun_list_file = "en_ab_noun_list.tsv"

with open(ab_noun_list_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter='\t')
    writer.writerow(["Abstract Noun", "Count"])  # Column headers
    # Sort the abstract nouns by count in descending order
    for noun, count in sorted(ab_noun_counts.items(), key=lambda item: item[1], reverse=True):
        writer.writerow([noun, count])

print(f"Abstract noun counts have been written to {ab_noun_list_file}")
