from TNPrepper import TNPrepper
from dotenv import load_dotenv
import os
import re
from itertools import permutations, combinations
from collections import defaultdict

load_dotenv()

class Passives(TNPrepper):
    def __init__(self, book_name, version):
        super().__init__()
        
        self.book_name = book_name
        self.version = version

    def __parse_combined_verse_data(self, data_list):
        combined_verse_data = []
        for row in data_list:
            if row:  # Check if line is not empty
                reference = row[0]
                glosses = row[1]
                lexeme = row[2]
                morphology = row[3]

                combined_verse_data.append({
                    'Reference': reference,
                    'Glosses': glosses,
                    'Lexeme': lexeme,
                    'Morphology': morphology,
                })

        return combined_verse_data

    def __combine_rows(self, modified_verse_data, verse_text_data):
        verse_dict = {row['Reference']: row['Verse'] for row in verse_text_data}
        combined_data_dict = defaultdict(list)

        # Parse the modified verse data
        combined_verse_data = self.__parse_combined_verse_data(modified_verse_data)

        for row in combined_verse_data:
            reference = row['Reference']
            combined_data_dict[reference].append(row)

        combined_data = []
        processed_references = set()

        for reference, rows in combined_data_dict.items():
            if reference in processed_references:
                continue  # Skip this reference if already processed

            verse = verse_dict.get(reference, "")
            if not verse:
                continue

            glosses = [row['Glosses'] for row in rows]
            glosses_set = set(glosses)  # For efficient lookup

            gloss_to_pattern = {re.escape(gloss): gloss for gloss in glosses}
            found_glosses = set()
            found_valid_sequence = False

            for r in range(len(glosses), 1, -1):
                for comb in combinations(glosses, r):
                    for perm in permutations(comb):
                        # Skip if any gloss in the permutation has already been used
                        if any(gloss in found_glosses for gloss in perm):
                            continue

                        # Create a regex pattern and track glosses used
                        pattern_parts = []
                        glosses_used = []

                        for i in range(len(perm) - 1):
                            gloss = re.escape(perm[i])
                            mod_gloss = re.sub('…', '.+?', gloss)
                            pattern_parts.append(mod_gloss)
                            pattern_parts.append(r'[^;.?:!]+?')  # Match any characters except sentence delimiters
                            glosses_used.append(gloss)
                        pattern_parts.append(re.escape(perm[-1]))
                        glosses_used.append(re.escape(perm[-1]))

                        names_joined_pattern = ''.join(pattern_parts)

                        # Search for matches in the verse
                        for match in re.finditer(names_joined_pattern, verse, re.IGNORECASE):
                            start, end = match.span()
                            matched_text = verse[start:end]

                            # Map back to original glosses
                            reconstructed_glosses = []
                            for part in pattern_parts:
                                if part in gloss_to_pattern:
                                    reconstructed_glosses.append(gloss_to_pattern[part])

                            # Filter rows based on the reconstructed glosses
                            matched_rows = [row for row in rows if row['Glosses'] in reconstructed_glosses]
                            found_glosses.update(reconstructed_glosses)

                            if matched_rows:
                                # Join matched rows
                                glosses_combined = '…'.join(row['Glosses'] for row in matched_rows)
                                lexeme_combined = ' & '.join(row['Lexeme'] for row in matched_rows)
                                morphology_combined = '; '.join(row['Morphology'] for row in matched_rows)

                                combined_data.append({
                                    'Reference': reference,
                                    'Glosses': glosses_combined,
                                    'Lexeme': lexeme_combined,
                                    'Morphology': morphology_combined,
                                })

                                found_valid_sequence = True
                                break  # Stop searching if a valid sequence is found

                            if found_valid_sequence:
                                break
                        if found_valid_sequence:
                            break
                    if found_valid_sequence:
                        break

            # Handle non-found glosses
            non_found_glosses = set(glosses) - found_glosses
            if non_found_glosses:
                non_found_rows = [row for row in rows if row['Glosses'] in non_found_glosses]
                combined_data.extend(non_found_rows)

            processed_references.add(reference)  # Mark this reference as processed

        return combined_data


    def run(self):
        
        # Scrape data from proposed book
        soup = self._scrape_and_read_data(self.book_name, self.version)

        # Define the identification pattern
        identification_pattern = r'x-morph="([^"]*?V[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

        # Create verse data
        verse_data = self._create_verse_data(soup, self.book_name, identification_pattern)

        modified_verse_data = self._figs_passive(verse_data)

        headers = ['Reference', 'Glosses', 'Lexeme', 'Morphology']
        file_name = 'passives.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=modified_verse_data)


        Other = self._passive_report(modified_verse_data)

        message = f'\n## Passives in English from {book_name} that are not Niphal, Qal passive, Hophal, or Pual\nReferences\tGlosses\tLexeme\tMorphology\n'
        data = Other
        report = self._write_report(data, message, book_name)

        verse_text_data_path = f'output/{book_name}/ult_book.tsv'
        verse_text_data = self._read_tsv(verse_text_data_path)
        joined_verse_data = self.__combine_rows(modified_verse_data, verse_text_data)

        # Standard link and note
        support_reference = 'rc://*/ta/man/translate/figs-activepassive'

        transformed_data = self._transform_passives(joined_verse_data, support_reference)

        # Write results to a TSV file
        headers = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        file_name = 'transformed_passives.tsv'
        self._write_output(book_name=self.book_name, file=file_name, headers=headers, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    version = os.getenv("VERSION")

    passives_instance = Passives(book_name, version)
    passives_instance.run()