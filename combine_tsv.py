import csv
from collections import defaultdict

# Function to read and parse TSV files
def read_tsv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        headers = next(reader)  # Assuming the first row is headers
        for row in reader:
            data.append(row)
    return data

# Function to extract note_word from Notes column
def extract_note_word(note):
    if '**' in note:
        start_index = note.index('**') + 2
        
        # Find the first occurrence of either '…' or '**'
        end_index_ellipsis = note.find('…', start_index)
        end_index_asterisks = note.find('**', start_index)
        
        if end_index_ellipsis == -1:
            end_index = end_index_asterisks
        elif end_index_asterisks == -1:
            end_index = end_index_ellipsis
        else:
            end_index = min(end_index_ellipsis, end_index_asterisks)

        # If no ending found, return the remaining string
        if end_index == -1:
            return note[start_index:].strip()
        
        return note[start_index:end_index].strip()
    return ''

# Function to read verse texts from output.tsv
def read_verse_texts(file_path):
    verse_texts = {}
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')
        headers = next(reader)  # Assuming the first row is headers
        for row in reader:
            reference = row[0]  # Assuming first column is Reference (e.g., Esther 1:14)
            verse_text = row[-1]  # Assuming last column is Verse Text
            # Split the reference to remove the book name prefix
            book_name, chapter_verse = reference.split(' ', 1)
            verse_texts[chapter_verse] = verse_text
    return verse_texts

# Function to sort rows by chapter and verse, and then by sequence of note_word in verse text
def sort_rows(tsv_data, verse_texts):
    # Dictionary to store positions of note_words in verse_texts
    note_word_positions = defaultdict(dict)

    # Populate note_word_positions
    for row in tsv_data:
        chapter_verse = row[0]  # Assuming first column is Reference (e.g., "1:14")
        note_word = extract_note_word(row[6])  # Assuming seventh column is Notes
        verse_text = verse_texts.get(chapter_verse, "")
        if verse_text and note_word:
            positions = []
            start = 0
            while True:
                start = verse_text.find(note_word, start)
                if start == -1:
                    break
                positions.append(start)
                start += len(note_word)
            note_word_positions[chapter_verse][note_word] = positions

    # Sort function
    def sort_key(row):
        chapter_verse = row[0]  # Assuming first column is Reference (e.g., "1:14")
        note_word = extract_note_word(row[6])  # Assuming seventh column is Notes

        # Split chapter_verse into chapter and verse components
        chapter, verse = map(int, chapter_verse.split(':'))

        # Get positions of note_word in the verse_text for this chapter_verse
        positions = note_word_positions.get(chapter_verse, {}).get(note_word, [])

        # Return tuple for sorting: (chapter, verse, first position of note_word or large number, note_word)
        return (chapter, verse, positions[0] if positions else float('inf'), note_word)

    # Sort rows
    sorted_data = sorted(tsv_data, key=sort_key)
    return sorted_data

# Function to combine and write sorted data to output.tsv
def combine_and_write(sorted_data, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
        writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note'])

        for row in sorted_data:
            writer.writerow(row)

# Main function to process multiple input files
def combine_multiple_tsv(files, output_file, verse_text_file):
    # Read verse texts from output.tsv
    verse_texts = read_verse_texts(verse_text_file)

    combined_data = []
    for file_path in files:
        data = read_tsv(file_path)
        combined_data.extend(data)

    # Sort combined data
    sorted_data = sort_rows(combined_data, verse_texts)

    # Write sorted data to output file
    combine_and_write(sorted_data, output_file)
    print(f"Combined and sorted data has been written to {output_file}")

# Example usage:
if __name__ == "__main__":
    # List of input files to combine
    input_files = ['transformed_ab_nouns.tsv', 'transformed_names.tsv', 'transformed_passives.tsv', 'transformed_ordinals.tsv']

    # Output file name
    output_file = 'combined_notes.tsv'

    # File containing verse texts
    verse_text_file = 'output.tsv'

    # Combine and sort
    combine_multiple_tsv(input_files, output_file, verse_text_file)
