from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os

load_dotenv()

class Passives(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def run(self):
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

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
modified_verse_data = list()
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

    # Construct the directory path
    directory_path = f'output/{book_name}'

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    with open(f'{directory_path}/en_new_passives.tsv', 'w', encoding='utf-8') as f:
        f.write('Reference\tGlosses\tLexeme\tMorphology\n')
        for line in modified_verse_data:
            f.write('\t'.join(line) + '\n')

    print(f"Data has been written to en_new_passives.tsv")

def generate_report(modified_verse_data, book_name):
    Niphal = []
    Qal_passive = []
    Hophal = []
    Pual = []
    Other = []

    # Define the regex patterns
    niphal_pattern = r'.+\tHe,.*?VN.+'
    qal_passive_pattern = r'.+\tHe,.*?(Vqs|VQ).+'
    hophal_pattern = r'.+\tHe,.*?(VH).+'
    pual_pattern = r'.+\tHe,.*?(VP).+'

    # Process each line to categorize
    for line in modified_verse_data:
        # Join the columns into a single string
        line_str = '\t'.join(line)
        if re.search(niphal_pattern, line_str):
            Niphal.append(line_str)
        elif re.search(qal_passive_pattern, line_str):
            Qal_passive.append(line_str)
        elif re.search(hophal_pattern, line_str):
            Hophal.append(line_str)
        elif re.search(pual_pattern, line_str):
            Pual.append(line_str)
        else:
            Other.append(line_str)

    with open(f'{directory_path}/report.md', 'a', encoding='utf-8') as report_file:
        report_file.write(f'\n## Passives in English from {book_name} that are not Niphal, Qal passive, Hophal, or Pual\n')
        report_file.write('References\tGlosses\tLexeme\tMorphology\n')
        for line in Other:
            report_file.write(f'{line}\n')
    
    print('Data processed and written to report.md')

generate_report(modified_verse_data, book_name)

# Standard link and note
standard_link = 'rc://*/ta/man/translate/figs-activepassive'
standard_note_template = 'If your language does not use this passive form, you could express the idea in active form or in another way that is natural in your language. Alternate translation: “alternate_translation”'

# Debugging: Print before writing transformed data
print("Transforming data for transformed_passives.tsv")

# Write to the output file only if rows exist after filtering
if modified_verse_data:
    with open(f'{directory_path}/transformed_passives.tsv', 'w', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        # Write the headers
        writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet'])
        
        for row in modified_verse_data:
            if len(row) == 4:
                reference = row[0]
                snippet = row[1]
                lexeme = row[2]

                # Extract chapter and verse from the reference
                chapter_verse = reference.rsplit(' ', 1)[1]

                # Create the new row
                transformed_row = [
                    chapter_verse,  # Reference without the book name
                    '',    # ID: random, unique four-letter and number combination
                    '',             # Tags: blank
                    standard_link,  # SupportReference: standard link
                    lexeme,         # Quote: lexeme
                    '1',            # Occurrence: the number 1
                    standard_note_template,
                    snippet  # Note: standard note with {gloss}
                ]

                # Write the transformed row to the output file
                writer.writerow(transformed_row)

    print(f"Transformed data has been written to transformed_passives.tsv")
