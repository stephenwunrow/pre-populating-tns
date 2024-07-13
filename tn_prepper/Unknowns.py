from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import requests
import re
import spacy
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class Unknowns(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        api_key = os.getenv('API_KEY')
        self.verse_text = f'output/{book_name}/ult_book.tsv'

        # Initialize the Groq client with your API key
        self.groq_client = Groq(api_key=api_key)
        self.groq_model = 'llama3-70b-8192'

    def __process_prompt(self, chapter_content):
        prompt = (
            "You have been given a chapter from the Bible. Identify any individual words that refer to objects or things that would be unfamiliar to people in other cultures. Do not include proper names.\n" 
            "As your answer, you will provide a table with exactly four tab-separated values. Do not include any introduction or explanation with the table. For example, do not include a phrase such as 'Here is the table...'\n"
            "\n(1) The first column will provide the chapter and verse where the unknown word is found. Do not include the book name."
            "\n(2) The second column will provide an explanation of the unknown word. The explanation should be in this exact form: 'The word or phrase **[unknown word]** refers to [explanation]. If your readers would not be familiar with [unknown word], you could refer to a similar [class of unknown word] in your culture, or you could use a general expression.' Replace the words in brackets with the appropriate information from the verse and context."
            "\n(3) The third column will provide a way to express the idea in a more general way, without using the unknown word. "
            "\n(4) The fourth column will contain the exact words from the verse that are semantically equivalent to the words that you provided in the third column. "
            "Be sure that the items in each row are consistent in how they understand the unknown word.\n"
            "Here is an example of what a row in your response might look like:\n\n"
            "22:34\tA **rooster** is a bird that calls out loudly around the time the sun comes up. If your readers would not be familiar with this bird, you could use the name of a bird in your area that calls out or sings just before dawn, or you could use a general expression.\tbefore the birds begin to sing in the morning, you will deny three times that you know me\tthe rooster will not crow today before you deny three times that you know me\n\n"
            "Make sure that each row contains exactly four tab-separated values."
        )

        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference'].strip('\'".,;!?“”’‘')
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                note_template = f'{explanation}. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/translate_unknown'
                
                transformed_row = [
                ref,  # Reference
                '',   # ID: random, unique four-letter and number combination
                '',   # Tags: blank
                support_reference,  # SupportReference: standard link
                'hebrew_placeholder',  # Quote: lexeme
                '1',  # Occurrence: the number 1
                note_template,  # Note: standard note with {gloss}
                snippet
            ]
                transformed_data.append(transformed_row)

        return transformed_data

    def _remove_words(self, mod_ai_data):
        filtered_data = []
        url_1 = 'https://git.door43.org/unfoldingWord/en_tw/src/branch/master/bible/kt'
        url_2 = 'https://git.door43.org/unfoldingWord/en_tw/src/branch/master/bible/other'

        def __extract_words_from_html(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            a_tags = soup.find_all('a', href=True, title=lambda x: x and x.endswith('.md'))
            words = [a_tag['title'].split('.md')[0] for a_tag in a_tags]
            return words

        # Function to fetch words from a URL
        def __extract_words_from_url(url):
            response = requests.get(url)
            if response.status_code == 200:
                html_content = response.text
                return __extract_words_from_html(html_content)
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
                return []

        scraped_names_1 = __extract_words_from_url(url_1)
        scraped_names_2 = __extract_words_from_url(url_2)

        all_names_to_remove = [name.split('-')[0].lower() for name in scraped_names_1 + scraped_names_2]

        nlp = spacy.load("en_core_web_sm")
        def get_lemma(word):
            doc = nlp(word)
            return doc[0].lemma_

        for row in mod_ai_data:
            text = row.get('Explanation', '')
            names = re.findall(r'\*\*(.+?)\*\*', text)
            for name in names:
                if ' ' in name:
                    mod_name = re.sub(r' ', r'', name)
                else:
                    mod_name = get_lemma(name)
                if mod_name.lower() not in all_names_to_remove:
                    filtered_data.append(row)

        return filtered_data

    def _read_tsv(self, file_path):
        verse_texts = []
        with open(file_path, 'r', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                verse_texts.append(row)
        return verse_texts

    def run(self):
        # Load verse texts from TSV
        verse_texts = self._read_tsv(self.verse_text)

        # Check the stage and limit verse_texts if in development stage
        if os.getenv('STAGE') == 'dev':
            verse_texts = verse_texts[:5]

        # Organize verse texts by chapter
        chapters = {}
        for verse in verse_texts:
            reference = verse['Reference']
            book_name, chapter_and_verse = reference.split()
            chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(verse)

        # Process each chapter for personification
        ai_data = []
        for chapter_key, verses in chapters.items():
            # Combine verses into chapter context
            chapter_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
            response = self.__process_prompt(chapter_content)
            if response:
                ai_data.append(response.split('\n'))
        
        # Flatten the list of lists into a single list of dictionaries
        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                columns = row.split('\t')
                if len(columns) == 4:
                    row_dict = {
                        'Reference': columns[0],
                        'Explanation': columns[1],
                        'Alternate Translation': columns[2],
                        'Snippet': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Explanation', 'Alternate Translation', 'Snippet']
        file_name = 'ai_unknowns.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        filtered_data = self._remove_words(mod_ai_data)

        transformed_data = self._transform_response(filtered_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_unknowns.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    unknowns_instance = Unknowns(book_name)
    unknowns_instance.run()
