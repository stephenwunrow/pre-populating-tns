from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Pronouns(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "You have been given a chapter from the Bible. For each pronoun, determine whether its referent is clear from the context of the text. A pronoun is considered unclear if a reader would have difficulty identifying what or whom the pronoun refers to without additional context.\n"
            "List only those pronouns where the referent is ambiguous or not immediately apparent. For each unclear pronoun, provide its possible referent(s).\n"
            "Be sure to include all pronouns that do not have an explicit referent earlier in the chapter, including indefinite or impersonal 'they'."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            "You have been given a chapter from the Bible. I will now provide you with a list of pronouns whose referents may not be clear from the context of the text. A pronoun is considered unclear if a reader would have difficulty identifying what or whom the pronoun refers to without additional context.\n\n"
            f"List:\n{response1}\n\n"
            "Analyze the list and return only those pronouns that have unclear referents, including indefinite or impersonal 'they'. If none of the pronouns have unclear referents, do not provide any list. Instead, return 'None'."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of pronouns whose referent is unclear:\n{response2}\n\n"
            "If the list is empty or 'None', respond with 'None'. Otherwise, create a TSV table of exactly four columns of data based on the list and the chapter."
            "\n(1) The first column will contain the reference for the verse where the pronoun is found. Do not include the book name."
            "\n(2) The second column will contain the pronoun whose referent is unclear."
            "\n(3) The third column will provide an explanation. You must follow this template: 'The pronoun **[pronoun]** refers to [the referent]. If this is not clear for your readers, you could refer to [the referent] directly.'"
            "\n(4) The fourth column will provide an exact quote from the verse. This quote will contain the word or words from the verse that would need to be rephrased to make the referenc clear."
            "\n(5) The fifth column will model how the quote from the fourth column could be rephrased so the referent is clear. Be sure that the word or words you provide exactly replace the quote from the fourth column."
            "Make sure that you are consistent in how you understand and interpret the pronoun across the columns, and use TSV format."
        )

        return self._query_openai(chapter_content, prompt3)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'",;!?“”’‘')
                alt_translation = re.sub(r'\*', '', alt_translation)
                note_template = f'{explanation}. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/writing-pronouns'

                
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
                if len(columns) == 5:
                    row_dict = {
                        'Reference': columns[0],
                        'Pronoun': columns[1],
                        'Explanation': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Pronoun', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_pronouns.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_pronouns.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    pronouns_instance = Pronouns(book_name)
    pronouns_instance.run()
