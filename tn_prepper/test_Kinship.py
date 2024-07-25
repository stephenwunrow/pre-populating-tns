from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class RQuestion(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt = (
            "Various languages use more or less precise terms for family relationships. Because of this, I need to provide information about specific family relationship terms so that translators know what relationship is being described.\n"
            "You have been given a chapter from the Bible. Please identify every family relationship terms.\n"
            "Particularly focus on brothers, sisters, cousins, in-laws, and grandparents. Do not infer relationships from context unless explicitly stated within the given text.\n"
            "For every family relationship term, you must append a row of data to a TSV table. If there are multiple family relationship terms in a verse, append a separate row for each one.\n"
            "Each row must contain exactly three tab-separated values:\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the family relationship term is found. Ensure that the family relationship terms is found exactly in the verse you identify."
            "\n(2) The second tab-separated value will provide the family relationship term from the verse. Quote exactly from the verse."
            "\n(3) The third tab-separated value will provide an explanation of the family relationship term, using information you already know and any information you can gain from the context. The explanation must be in this exact form:\n"
            "'Here the term **[family relationship term]** specifically refers to [exact family relationship]. If your language has a specific word for [exact family relationship], it would be appropriate to use it here'. Replace the words in brackets with the appropriate information. If you quote directly from the verse, use double asterisks instead of quote marks, as the template illustrates.\n"
            "If the relationship is brother or sister, be sure to indicate from what you know who is the older sibling. If the relationship is grandparents, be sure to indicate from what you know which side of the family the grandparents are on."
            "\nMake sure that the values in each row are consistent in how they identify, understand, and explain the family relationship term.\n"
            "Also, make sure that each row contains exactly these three tab-separated values."
            "### Examples:\n"
            "1 Kings 1:6\this father\tHere the term **his father** specifically refers to David, who is the father of Adonijah. If your language has a specific word for this father-son relationship, it would be appropriate to use it here.\n"
            "1 Kings 1:10\this brother Solomon\tHere the term **his brother Solomon** specifically refers to Solomon, who is the younger brother of Adonijah. If your language has a specific word for this younger brother relationship, it would be appropriate to use it here."
        )
        return self._query_openai(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                snippet = row['Term'].strip('\'".,;!“”’‘*')
                explanation = row['Explanation'].strip('\'".,;!“”’‘ ')
                note_template = f'{explanation}.'
                support_reference = 'rc://*/ta/man/translate/translate-kinship'
                
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
            book_name, chapter_and_verse = reference.rsplit(' ', 1)
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
                if len(columns) == 3:
                    row_dict = {
                        'Reference': columns[0],
                        'Term': columns[1],
                        'Explanation': columns[2],
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Term', 'Explanation']
        file_name = 'ai_kinship.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_kinship.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    rquestion_instance = RQuestion(book_name)
    rquestion_instance.run()
