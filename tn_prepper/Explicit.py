from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class Explicit(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt = (
            "Authors sometimes omit information that they believe their readers already know. This information can be inferred from the context or is generally known in their culture.\n"
            "However, for readers who are unfamiliar with that culture or who do not infer the information from the context, the meaning can be unclear.\n"
            "You have been given a chapter from the Bible. Identify every instance where an author omits information that he or she assumed his or her readers would already know.\n"
            "The issues of metaphor, metonymy, and other figures of speech, as well as the issue unusual words, will be dealt with in other notes. So, do not include those issues here. Instead, focus on issues related to whole clauses and sentences."
            "As your answer, you will provide a TSV table with exactly four tab-separated values. If there are multiple places in a verse where significant information is omitted, include a separate row in the TSV table for each one.\n"
            "\n(1) The first column will provide the chapter and verse where the information is omittex. Do not include the book name."
            "\n(2) The second column will provide an explanation of the omitted information. The explanation must begin in this exact way: 'The implication is that'."
            "\n(3) The third column will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to express the omitted information explicitly."
            "\n(4) The fourth column will provide a way to express the exact quote from the fourth value with the omitted information made explicit. Do not remove or modify any figures of speech, and do not shorten the quote. Match the style of the verse as closely as possible."
            "\nBe sure that the items in each row are consistent in how they understand the implied information.\n"
        )

        return self._query_openai(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference'].strip('\'".,;!?“”’‘')
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                note_template = f'{explanation}. You could include this information if that would be helpful to your readers. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-explicit'
                
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
                if len(columns) == 4:
                    row_dict = {
                        'Reference': columns[0],
                        'Explanation': columns[1],
                        'Snippet': columns[2],
                        'Alternate Translation': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_explicit.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_explicit.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    explicit_instance = Explicit(book_name)
    explicit_instance.run()
