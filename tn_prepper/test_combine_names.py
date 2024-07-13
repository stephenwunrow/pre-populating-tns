import csv
import re
from itertools import permutations
from collections import defaultdict

def read_tsv(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        return list(reader)

def write_tsv(data, file_path):
    fieldnames = ['Reference', 'Glosses', 'Lexeme', 'Morphology', 'Name']
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)

def combine_rows(combined_verse_data, verse_text_data):
    verse_dict = {row['Reference']: row['Verse'] for row in verse_text_data}
    combined_data_dict = defaultdict(list)

    for row in combined_verse_data:
        reference = row['Reference']
        combined_data_dict[reference].append(row)

    combined_data = []

    for reference, rows in combined_data_dict.items():
        verse = verse_dict.get(reference, "")
        if not verse:
            continue

        names = [re.escape(row['Name']) for row in rows]

        # Try all permutations of names to find a valid sequence in the verse text
        found_valid_sequence = False

        for perm in permutations(names):
            pattern_parts = []
            for i in range(len(perm) - 1):
                pattern_parts.append(perm[i])
                pattern_parts.append(r'[^.?!]+?')
            pattern_parts.append(perm[-1])

            names_joined_pattern = ''.join(pattern_parts)

            # Searching for matches in the verse
            combined_rows = []

            for match in re.finditer(names_joined_pattern, verse, re.IGNORECASE):
                start, end = match.span()
                glosses = '…'.join(row['Glosses'] for row in rows)
                lexeme = ' & '.join(row['Lexeme'] for row in rows)
                morphology = '; '.join(row['Morphology'] for row in rows)
                name = ', '.join(row['Name'] for row in rows)

                combined_rows.append({
                    'Reference': reference,
                    'Glosses': glosses,
                    'Lexeme': lexeme,
                    'Morphology': morphology,
                    'Name': name
                })

            if combined_rows:
                combined_data.extend(combined_rows)
                found_valid_sequence = True
                break  # Stop searching if a valid sequence is found

        # If no valid sequence was found, handle this case (e.g., append rows individually or handle differently)
        if not found_valid_sequence:
            # Example fallback: append rows individually if no valid sequence was found
            combined_data.extend(rows)

    return combined_data

# Example usage:
combined_verse_data_path = 'output/Obadiah/abnouns.tsv'
verse_text_data_path = 'output/Obadiah/ult_book.tsv'
output_path = 'output/Obadiah/combined_abnouns.tsv'

combined_verse_data = read_tsv(combined_verse_data_path)
verse_text_data = read_tsv(verse_text_data_path)

combined_data = combine_rows(combined_verse_data, verse_text_data)
write_tsv(combined_data, output_path)
