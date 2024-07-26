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
            "I need to write notes about the following family relationships, providing the required information:\n"
            "Term: Required Information\n"
            "brother: younger or older, half or full\n"
            "sister: younger or older, half or full\n"
            "cousin: gender, side of the family, younger or older\n"
            "uncle: side of the family, older or younger than parent\n"
            "aunt: side of the family, older or younger than parent\n"
            "niece: side of the family\n"
            "nephew: side of the family\n"
            "grandfather: side of the family\n"
            "grandmother: side of the family\n"
            "-in-law: side of the family, specific relationship\n\n"
            "You have been given a chapter from the Bible. Identify all terms for the above relationships in the chapter, if any. Only identify the relationships listed above. Do not include any other family relationships, such as terms like 'queen', 'wife', 'servant', 'son', 'daughter', or 'father'. If there are no terms, return 'None.'\n"
            "Ignore any figurative uses of terms for these relationships, and focus only on literal family relationships.\n"
            "When you find a term for one of the above relationships, you must append a row of data to a TSV table. If there are multiple terms in one verse, append a separate row for each one.\n"
            "Each row must contain exactly three tab-separated values:\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the term is found. Ensure that the term is found exactly in the verse you identify."
            "\n(2) The second tab-separated value will provide the term from the verse. Quote exactly from the verse."
            "\n(3) The third tab-separated value will give the required information for the term, using all information you have available. If you do not know some of the required information, include that in your answer. The required information must be in this exact form:\n"
            "'Here the term **[family relationship term]** specifically refers to [exact family relationship]. [Any further explanation required, such as if information is not known.] If your language has a specific word for [exact family relationship], it would be appropriate to use it here'. Replace the words in brackets with the appropriate information. If you quote directly from the verse, use double asterisks instead of quote marks, as the template illustrates.\n"
            "If the term is not one of the specified family relationship terms listed above, do not include it in your response.\n"
            "Ensure that the table is in TSV form."
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
