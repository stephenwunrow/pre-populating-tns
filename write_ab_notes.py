import csv
import random
import string

# Function to generate a random, unique four-letter and number combination
def generate_random_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

# File paths
input_file = 'output/en_new_ab_nouns.tsv'
output_file = 'output/transformed_ab_nouns.tsv'

# Standard link and note
standard_link = 'rc://*/ta/man/translate/figs-abstractnouns'
standard_note_template = 'If your language does not use an abstract noun for the idea of **{ab_noun}**, you could express the same idea in another way. Alternate translation: “alternate_translation”'

# Read the input file
with open(input_file, 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    # Skip the header
    next(reader)
    rows = [row for row in reader]

# Write to the output file
with open(output_file, 'w', encoding='utf-8') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    # Write the headers
    writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note'])
    
    for row in rows:
        if len(row) == 3:
            reference = row[0]
            ab_noun = row[1]
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
                standard_note_template.format(ab_noun=ab_noun)  # Note: standard note with {ab_noun}
            ]

            # Write the transformed row to the output file
            writer.writerow(transformed_row)

print(f"Data has been transformed and written to {output_file}")
