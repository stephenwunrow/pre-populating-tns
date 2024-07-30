from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Generic_Nouns(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "A generic noun seems to refer to a specific person or thing, but in the context it refers to people or things in general."
            "You have been given a chapter from the Bible. Please identify all generic nouns and noun phrases in the chapter. If there are none, return 'None'.\n"
            "Provide the reference and the complete noun phrase for each one you find, if any. If there are multiple generic nouns in a verse, list all of them. Each generic noun should have its own line in the list.\n"
            "Important: generic nouns are always singular.\n"
            "Here is an example: 'People curse the man who refuses to sell grain.' In this sentence, the word 'man' is used as a generic noun. Although 'man' refers to a specific individual in the sentence, it represents a general category of people. The context implies that 'man' could be any person who refuses to sell grain, rather than referring to a particular individual. The term 'man' in this context is used generically to represent any person who fits the described behavior."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"A generic noun seems to refer to a specific person or thing, but in the context it refers to people or things in general. You have been given a chapter from the Bible. Here is a list of possible generic nouns in this chapter:\n{response1}\n\n"
            "Examine the list in context. If the line does not contain a noun, remove it. Also, remove any line that in context does refer to a specific person or thing. If you remove all the lines, return 'None'. Otherwise, return the revised list only."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"Here is a list of generic nouns in this chapter:\n{response2}\n\n"
            "For each generic noun, append a row of data to a TSV table. If the list is empty, return 'None' instead of a table.\n"
            "Each row in the TSV table must contain exactly four tab-separated values:\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the generic noun is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide an explanation of the generic noun. The explanation must follow this template: 'The word **generic_noun** represents [things] in general, not one particular [thing]'. Replace the bracketed words with information from the verse and context. The word or words in double asterisks must be exact quotes from the verse."
            "\n(3) The third tab-separated value will contain an exact quote from the verse. This quote will provide the words that would need to be rephrased to express the idea without using a generic noun."
            "\n(4) The fourth tab-separated value will model how to rephrase the exact quote from the third value so that it refers to people or things in general. One of the best ways to do this is to make the noun or noun phrase plural. Make sure that the rephrased text can exactly replace the quote in the verse."
            "\nMake sure that the values in each row are consistent in how they identify, understand, and explain the collective noun.\n"
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
                note_template = f'{explanation}. If it would be helpful in your language, you could use a more natural expression. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-genericnoun'
                
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
        file_name = 'ai_genericnouns.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_genericnouns.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    generic_noun_instance = Generic_Nouns(book_name)
    generic_noun_instance.run()
