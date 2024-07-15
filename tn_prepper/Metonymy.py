from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Metonymy(TNPrepper):
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
            "Metonymy always requires the substition of a related word or phrase for a normal word or phrase. For example, 'throne' substitutes for 'reign.' You have been given a chapter from the Bible. Please identify all metonymy in the chapter, if any. Be sure that what you identify as metonymy is not better classified as another figure of speech, such as metaphor or idiom.\n"
            "When you find a metonymy, you will append a row of data to a table. Each row must contain exactly five tab-separated values. Do not include any introduction or explanation with the table.\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the metonymy is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide the words from the verse that contain the metonymy. Quote exactly from the verse."
            "\n(3) The third tab-separated value will provide a one-sentence explanation of the meaning of the metonymy. You must begin your sentence with the phrase 'Here, **[word]** represents'. Replace [word] with the appropriate data from the verse, and keep the double asterisks."
            "\n(4) The fourth tab-separated value will provide a way to express the idea without using metonymy. The alternate expression you provide must be able to replace the phrase or clause from the verse that contains the metonymy."
            "\n(5) The fifth tab-separated value will include the exact words from the verse that the alternate expression can replace. Make sure that the words you provide are quoted precisely from the verse."
            "\nMake sure that the values in each row are consistent in how they identify, understand, and explain the metaphor.\n"
            "Also, make sure that each row contains these exact five values."
        )
        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                note_template = f'{explanation}. If it would be helpful in your language, you could state the meaning plainly. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-metonymy'
                
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
                if len(columns) == 5:
                    row_dict = {
                        'Reference': columns[0],
                        'Metonymy': columns[1],
                        'Explanation': columns[2],
                        'Alternate Translation': columns[3],
                        'Snippet': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Metonymy', 'Explanation', 'Alternate Translation', 'Snippet']
        file_name = 'ai_metonymy.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_metonymy.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    metonymy_instance = Metonymy(book_name)
    metonymy_instance.run()
