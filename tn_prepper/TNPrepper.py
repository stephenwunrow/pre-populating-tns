import os
import csv
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from pprint import pprint
import time
import openai
from dotenv import load_dotenv
from openai import OpenAI
client = OpenAI()


class TNPrepper():
    def __init__(self, model='gpt-4o-mini'):
        self.output_base_dir = 'output'
        self.model = model

    # Function to get the content of the file
    def _get_file_content(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return ''

    # Scrapes ult or ust and reads it, returning "soup"
    def _scrape_and_read_data(self, book_name, version):
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

        # Get the acronym from the acronym mapping
        if book_name in acronym_mapping:
            acronym = acronym_mapping[book_name]
        else:
            print("Invalid book name. Please enter a valid book name.")
            exit()

        # URL of the file to download
        url = f"https://git.door43.org/unfoldingWord/en_{version}/raw/branch/master/{acronym}.usfm"

        # Get the file content
        file_content = self._get_file_content(url)

        # Process the file content
        soup = BeautifulSoup(file_content, 'html.parser')
        return soup

    # NOTE: there may be too much variation among the functions to use this for all of them
    # Searches "identification_pattern" and returns "verse_data"
        # "identification_pattern" should have two match groups, 
        # the first for morphology (x-morph) and the second for the Hebrew word (x-content),
        # and it should end with \\w .+?\|
    def _create_verse_data(self, soup, book_name, identification_pattern):
        # Initialize variables
        chapter = None
        verse = None
        verse_data = []

        # Combine all lines into a single string
        combined_text = soup.get_text(separator='\n')

        # Split the combined text by "\\zaln-s"
        chunks = combined_text.split('\\zaln-s')

        with tqdm(total=len(chunks), desc="Processing Chunks") as pbar:
            for chunk in chunks:
                pbar.update(1)  # Update progress bar

                # Find all matches of the desired pattern
                matches = re.findall(identification_pattern, chunk, re.DOTALL)
                if matches:  # Only proceed if there are matches
                    for match in matches:
                        lexeme = match[1]
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

        return verse_data

    # NOTE: there may be too much variation among the functions to use this for all of them
    # Takes "verse_data" and transforms it into TN form
        # Provide the appropriate "SupportReference" and "note_template" for the type of note
    def _transform_data(self, verse_data, support_reference, note_template):
        if verse_data:

            transformed_data = list()
            for row in verse_data:

                if len(row) == 4:
                    reference = row[0]
                    snippet = row[1]
                    lexeme = row[2]

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',  # ID: random, unique four-letter and number combination
                        '',  # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,  # Quote: lexeme
                        '1',  # Occurrence: the number 1
                        note_template,  # Note: standard note with {gloss}
                        snippet
                    ]

                    transformed_data.append(transformed_row)

            return transformed_data

    def __setup_output(self, book_name, file_name):
        # Construct the output path
        output_path = f'output/{book_name}'

        # Ensure the directory exists
        os.makedirs(output_path, exist_ok=True)

        if '.tsv' not in file_name:
            file_name += '.tsv'

        # Path to the file you want to write
        return f'{output_path}/{file_name}'

    def _get_book_name(self):
        if os.getenv('BOOK_NAME'):
            book_name = os.getenv('BOOK_NAME')
        else:
            # Prompt the user for book name
            book_name = input("Enter the book name (e.g., 2 Chronicles): ")
        return book_name

    def _parse_verse_ref(self, verse_ref):
        # Function to split verse_ref into chapter and verse and return as tuple for sorting
        chapter, verse = verse_ref.split(':')
        return int(chapter), int(verse)

    def _read_tsv(self, file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            return list(reader)

    def _write_output(self, book_name, file, headers, data, fieldnames=None):

        output_file = self.__setup_output(book_name, file)

        # Write results to a TSV file
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            if fieldnames:
                writer = csv.DictWriter(file, delimiter='\t', fieldnames=fieldnames)
                writer.writeheader()
            else:
                writer = csv.writer(file, delimiter='\t')
                writer.writerow(headers)  # Column headers
            for line in data:
                writer.writerow(line)

        print(f"Data has been written to {output_file}")

    def _write_tsv(self, book_name, file_name, headers, data):

        output_file = self.__setup_output(book_name, file_name)

        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            file.write('\t'.join(headers) + '\n')  # Write headers

            for line in data:
                file.write(line + '\n')  # Write each line of data
        print(f'data written to {output_file}')

    def _write_fieldnames_to_tsv(self, book_name, file_name, data, headers):

        output_file = self.__setup_output(book_name, file_name)

        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, delimiter='\t', fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print(f'data written to {output_file}')

    def _write_report(self, data, message, book_name):
        with open(f'output/{book_name}/report.md', 'a', encoding='utf-8') as report_file:
            report_file.write(f'{message}')
            for line in data:
                report_file.write(f'{line}\n')





    # SupportReference specific functions
    ## figs_go
    def _figs_go(self, verse_data):
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
            all_text = re.sub(r'(.+\b(go|goes|gone|going|went|come|comes|coming|came|take|takes|taken|taking|took|bring|brings|bringing|brought)\b)', r'~\1', all_text)
            all_text = re.sub(r'\n[^~].+', r'', all_text)
            all_text = re.sub(r'^[^~].+', r'', all_text)
            all_text = re.sub(r'^\n', r'', all_text)
            all_text = re.sub(r'~', r'', all_text)
            # Split the modified string back into lines
            modified_verse_data = [line.split('\t') for line in all_text.split('\n')]

        return modified_verse_data

    def _transform_figs_go(self, modified_verse_data, support_reference):
        word_mapping = {
            "goes": "comes",
            "gone": "come",
            "going": "coming",
            "go": "come",
            "went": "came",
            "has come": "has gone",
            "have come": "have gone",
            "had come": "had gone",
            "has…come": "has…gone",
            "have…come": "have…gone",
            "had…come": "had…gone",
            "comes": "goes",
            "coming": "going",
            "came": "went",
            "come": "go",
            "takes": "brings",
            "taken": "brought",
            "taking": "bringing",
            "took": "brought",
            "take": "bring",
            "has brought": "has taken",
            "have brought": "have taken",
            "had brought": "had taken",
            "has…brought": "has…taken",
            "have…brought": "have…taken",
            "had…brought": "had…taken",
            "brings": "takes",
            "bringing": "taking",
            "bring": "take",
            "brought": "took"
        }

        if modified_verse_data:
            transformed_data = []
            for row in modified_verse_data:
                if len(row) == 4:
                    reference = row[0]
                    snippet = row[1]
                    lexeme = row[2]

                    key = ""
                    text = ""

                    for word in word_mapping:
                        if word in snippet:
                            key = word
                            key = re.sub(r'(has|have|had)(…| )', r'', key)
                            text = word_mapping[key]
                            text = re.sub(r'(has|have|had)(…| )', r'', text)
                            break  # Stop searching once a match is found

                    AT = re.sub(rf'(.*){key}(.*)', rf'\1{text}\2', snippet)

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    note_template = f"In a context such as this, your language might say “{text}” instead of **{key}**. Alternate translation: “{AT}”"

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',    # ID: random, unique four-letter and number combination
                        '',             # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,         # Quote: lexeme
                        '1',            # Occurrence: the number 1
                        note_template.format(key=key, text=text, AT=AT),  # Note: standard note with {gloss}
                        snippet
                    ]
                    transformed_data.append(transformed_row)

            return transformed_data

    ## figs-activepassive
    def _figs_passive(self, verse_data):
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

        return modified_verse_data

    def _passive_report(self, modified_verse_data):
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

        return Other

    def _transform_passives(self, modified_verse_data, support_reference):
        if modified_verse_data:
            transformed_data = []
            for row in modified_verse_data:
                if len(row) == 4:
                    reference = row['Reference']
                    snippet = row['Glosses']
                    lexeme = row['Lexeme']

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    if '&' in lexeme:
                        note_template = 'If your language does not use these passive forms, you could express the ideas in active form or in another way that is natural in your language. Alternate translation: “alternate_translation”'
                    else:
                        note_template = 'If your language does not use this passive form, you could express the idea in active form or in another way that is natural in your language. Alternate translation: “alternate_translation”'

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',    # ID: random, unique four-letter and number combination
                        '',             # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,         # Quote: lexeme
                        '1',            # Occurrence: the number 1
                        note_template,
                        snippet  # Note: standard note with {gloss}
                    ]

                    # Write the transformed row to the output file
                    transformed_data.append(transformed_row)
            return transformed_data


    ## translate_names
    def _translate_names(self, verse_data):
        url = 'https://git.door43.org/unfoldingWord/en_tw/src/branch/master/bible/names'
        custom_words_to_remove = ["and", "but", "then", "in", "now", "Yahweh", "Israel"]
        # Function to fetch words from a URL
        def __extract_words_from_url(url):
            response = requests.get(url)
            if response.status_code == 200:
                html_content = response.text
                return __extract_words_from_html(html_content)
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
                return []

        # Function to extract words from HTML content
        def __extract_words_from_html(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            a_tags = soup.find_all('a', href=True, title=lambda x: x and x.endswith('.md'))
            words = [a_tag['title'].split('.md')[0] for a_tag in a_tags]
            return words

        scraped_names = __extract_words_from_url(url)

        all_names_to_remove = [name.lower() for name in scraped_names + custom_words_to_remove]

        if verse_data:
            name_count = {}
            for row in verse_data:
                gloss = row[1]
                mod_gloss = re.sub(r'\b(And|But|Then|Now|In|The|At|For)\b ', r'', gloss)
                names_search = re.findall(r'(\b[A-Z]\w+?\b)', mod_gloss)
                if names_search:
                    name = ' '.join(names_search)
                    mod_name = re.sub(' ', '', name)
                    if mod_name.lower() not in all_names_to_remove:
                        if name in name_count:
                            name_count[name] += 1
                        else:
                            name_count[name] = 1
                    row.append(name)

            sorted_name_count = sorted(name_count.items(), key=lambda x: x[1], reverse=True)

            joined_name_count = []
            for name, count in sorted_name_count:
                joined_name_count.append([name, str(count)])

            def __filter_rows(verse_data, all_names_to_remove):
                filtered_rows = []
                for row in verse_data:
                    if len(row) > 4:
                        if row[4].lower() not in all_names_to_remove:
                            filtered_rows.append(row)
                return filtered_rows

            modified_verse_data = __filter_rows(verse_data, all_names_to_remove)

        return joined_name_count, modified_verse_data

    def _transform_names(self, modified_verse_data, support_reference):

        if modified_verse_data:
            name_occurrence = {}
            transformed_data = []
            for row in modified_verse_data:
                if len(row) == 5:
                    reference = row[0]
                    name = row[4]
                    lexeme = row[2]
                    snippet = row[1]
                    note_template = f'The word **{name}** is the name of a ______.'

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',    # ID: random, unique four-letter and number combination
                        '',             # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,         # Quote: lexeme
                        '1',            # Occurrence: the number 1
                        note_template,  # Note: standard note with {name}
                        snippet
                    ]
                    if name not in name_occurrence:
                        # Write the transformed row to the output file
                        transformed_data.append(transformed_row)
                        name_occurrence[name] = True
                    elif name in name_occurrence:
                        continue

        return transformed_data

    # figs-abstractnouns
    def _figs_abstractnouns(self, verse_data, ab_nouns):
        def __combine_glosses(verse_data):
            # Define the search and replace pattern
            search_pattern = r'([^\n]*\d+:\d+)\t([^\n]+?)\t([^\n]+?)\t(.+?)\n(\1\t)([^\n]+?)(\t\3[^\n]+)'
            replace_with = r'\1\t\2…\6\t\3\t\4'

            combined_data = []
            for verse in verse_data:
                # Join elements in each inner list into a single string
                combined_verse = '\t'.join(verse)
                combined_data.append(combined_verse)
            combined_data = '\n'.join(combined_data)

            # Apply search and replace until no changes are detected
            while True:
                new_text = re.sub(search_pattern, replace_with, combined_data, flags=re.DOTALL)
                if new_text == combined_data:
                    break
                combined_data = new_text

            combined_data = combined_data.split('\n')

            return combined_data

        def __find_abnouns(combined_data, ab_nouns):
            found_instances = []
            patterns = {}
            for ab_noun in ab_nouns:
                if ' ' in ab_noun:
                    ab_noun1, ab_noun2 = ab_noun.split(' ', 1)
                    patterns[ab_noun] = re.compile(rf'.+?\t.*?\b{ab_noun1}\b.*?\b{ab_noun2}\b.*?\t.+', re.IGNORECASE)
                else:
                    patterns[ab_noun] = re.compile(rf'.+?\t.*?\b{ab_noun}\b.*?\t.+', re.IGNORECASE)

            for line in combined_data:
                for ab_noun, pattern in patterns.items():
                    matches = pattern.findall(line)
                    if matches:
                        for match in matches:
                            # Append to verse_data with lexeme, verse reference, and ab_noun
                            found_instances.append(f'{match}\t{ab_noun}\n')
            return found_instances

        def __delete_repeats(found_instances):

            # Apply regex replacements repeatedly
            def apply_replacements(text, patterns):
                while True:
                    new_text = text
                    for pattern, replacement in patterns:
                        new_text = re.sub(pattern, replacement, new_text)
                    if new_text == text:
                        break
                    text = new_text
                return text

            # Define the patterns and replacements
            replacements = [
                (r'([^\n]+?\d)(\t)([^\n\t]+)(\t)([^\n\t]+\t[^\n\t]+)(\t)([^\n\t]+)\n(\1\2\3\4\5\t[^\n\t]+)', r'\8')
            ]

            # Join the verse_data list into a single string
            verse_data_str = ''.join(found_instances)

            # Apply the replacements
            verse_data_str = apply_replacements(verse_data_str, replacements)

            # Split back into a list
            modified_verse_data = verse_data_str.split('\n')

            return modified_verse_data

        def __count_nouns(modified_verse_data):
            # Count occurrences of each abstract noun
            abstract_noun_counts = {}
            for line in modified_verse_data:
                if line:
                    parts = line.split('\t')
                    if len(parts) == 5:
                        ab_noun = parts[4]
                        if ab_noun in abstract_noun_counts:
                            abstract_noun_counts[ab_noun] += 1
                        else:
                            abstract_noun_counts[ab_noun] = 1

            # Sort abstract nouns by count in descending order
            sorted_counts = sorted(abstract_noun_counts.items(), key=lambda x: x[1], reverse=True)

            return sorted_counts

        combined_data = __combine_glosses(verse_data)

        found_instances = __find_abnouns(combined_data, ab_nouns)

        modified_verse_data = __delete_repeats(found_instances)

        sorted_counts = __count_nouns(modified_verse_data)

        return modified_verse_data, sorted_counts

    def _transform_abstractnouns(self, modified_verse_data, support_reference):
        if modified_verse_data:
            transformed_data = []
            for row in modified_verse_data:
                if len(row) == 5:
                    reference = row['Reference']
                    snippet = row['Glosses']
                    lexeme = row['Lexeme']
                    ab_noun = row['Name']
                    if ',' not in ab_noun:
                        note_template = f'If your language does not use an abstract noun for the idea of **{ab_noun}**, you could express the same idea in another way. Alternate translation: “alternate_translation”'
                    elif ab_noun.count(',') == 1:
                        abnoun_1, abnoun_2 = ab_noun.rsplit(',')
                        note_template = f'If your language does not use abstract nouns for the ideas of **{abnoun_1.strip()}** and **{abnoun_2.strip()}**, you could express the same ideas in another way. Alternate translation: “alternate_translation”'
                    elif ab_noun.count(',') > 1:
                        phrase, abnoun_2 = ab_noun.rsplit(',', 1)
                        mod_phrase = re.sub(', ', '**, **', phrase)
                        note_template = f'If your language does not use abstract nouns for the ideas of **{mod_phrase.strip()}**, and **{abnoun_2.strip()}**, you could express the same ideas in another way. Alternate translation: “alternate_translation”'

                    # Extract chapter and verse from the reference
                    chapter_verse = reference.rsplit(' ', 1)[1]

                    # Create the new row
                    transformed_row = [
                        chapter_verse,  # Reference without the book name
                        '',    # ID: random, unique four-letter and number combination
                        '',             # Tags: blank
                        support_reference,  # SupportReference: standard link
                        lexeme,         # Quote: lexeme
                        '1',            # Occurrence: the number 1
                        note_template.format(ab_noun=ab_noun),  # Note: standard note with {ab_noun}
                        snippet
                    ]
                    transformed_data.append(transformed_row)
            return transformed_data

    # LLM query stuff

    # Function to wait between queries
    def __wait_between_queries(self, seconds):
        print(f"Waiting for {seconds} seconds...")
        time.sleep(seconds)

    # Function to query the LLM
    def _query_llm(self, context, prompt):
        combined_prompt = f"Chapter:\n{context}\n\nPrompt:\n{prompt}"
        response = None

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "I want to write translation notes for translation issues in the Bible."
                        "These translation notes will include chapter and verse, an explanation of the translation issue, an alternate way to translate the idea without using the figure of speech, and the words from the Bible translation that need to be replaced to include the alternate translation."
                        "In order to accomplish this goal, I want you to provide me with the precise data I request. You should not provide explanations and interpretation unless you are specifically asked to do so."
                    },
                    {
                        "role": "user",
                        "content": combined_prompt,
                    }
                ],
                model=self.groq_model,
                temperature = 0.4

            )
            response = chat_completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"Request failed: {e}")
            print(f"Failed to get response for prompt: {prompt}")

        finally:
            print(combined_prompt)
            print(f'Response: {response}')
            print('---')

            # Waiting, to stay below our request limit (30 reqs/minute)
            self.__wait_between_queries(2)

            return response

    def _query_openai(self, context, prompt):
        combined_prompt = f"Chapter:\n{context}\n\nPrompt:\n{prompt}"
        response = None

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "I want to write translation notes for translation issues in the Bible. These translation notes will include chapter and verse, "
                    "an explanation of the translation issue, an alternate way to translate the idea without using the figure of speech, and the words from the Bible translation "
                    "that need to be replaced to include the alternate translation. In order to accomplish this goal, I want you to provide me with the precise data I request. "
                    "You should not provide explanations and interpretation unless you are specifically asked to do so."},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.4
            )

            response_content = completion.choices[0].message.content
            response = response_content

        except openai.error.OpenAIError as e:
            print(f"Failed to get response for prompt: {prompt}")
            print(f"Exception: {e}")

        finally:
            print(combined_prompt)
            print(f'Response: {response}')
            print('---')

            return response

    ## Combine name notes together (use at the end of ATs_snippets.py)
    def _combine_names(self, ai_notes):
        # Join all lines into a single string
        combined_lines = '\n'.join(['\t'.join(item.values()) for item in ai_notes])

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe word)([^\n]+?)(is the name of a )(\w+)([^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe word([^\n]+) is the name of a \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 & \11\4\tThe words\6and\12 are the names of \8s\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe words)([^\n]+?)(are the names of )(\w+)(s[^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe word([^\n]+) is the name of a \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 \& \11\4\5\6and\12 \7\8\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe words)([^\n]+?)(are the names of )(\w+)([^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe words([^\n]+) are the names of \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 \& \11\4\5\6and\12 \7\8\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        combined_lines = re.sub(r' mans', r' men', combined_lines)
        combined_lines = re.sub(r' womans', r' women', combined_lines)
        combined_lines = re.sub(r'(The words \*\*\w+\*\*)( and)( \*\*\w+\*\*)( and \*\*\w+\*\*)', r'\1,\3,\4', combined_lines)

        search_pattern = r'(\*\*\w+\*\*, \*\*\w+\*\*, )(and )(\*\*\w+\*\*)( and \*\*\w+\*\*)'
        replace_with = r'\1\3,\4'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        # At the end, split the combined_lines back into a list of dictionaries
        result_lines = []
        for line in combined_lines.strip().split('\n'):
            # Split each line by tabs and create a dictionary for each
            values = line.split('\t')
            result_lines.append({key: value for key, value in zip(ai_notes[0].keys(), values)})

        return result_lines