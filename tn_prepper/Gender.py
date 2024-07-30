from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Gender(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "In the Bible, sometimes words that are masculine in gender are used in context to refer to both male and female people. You have been given a chapter from the Bible. Please identify all masculine words that in their context refer to both male and female people. If there are none, return 'None'.\n"
            "Provide the reference and quote the masculine word for each instance you find, if any. If there are several instances in one verse, list each one separately.\n"
            "Examples: 'men' for a group of men and women; 'sons' for chidren or descendants of both genders; 'brothers' for relatives of both genders.\n"
            "Most important: be sure that the masculine word you quote is exactly from the cited verse."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"Sometimes masculine words refer to both male and female people. You have been given a chapter from the Bible. Here is a list from that chapter:\n{response1}\n\n"
            "This list is supposed to provide words that are masculine but that refer to both male and female people. Examine the list in context. Then, remove each line that does not contain a masculine word that refers to both male and female people. If you remove all the lines, return 'None'. Otherwise, return the revised list only.\n"
            "Be sure that you remove all lines that do not have a masculine word."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"Here is a list of masculine in this chapter that refer to both male and female people:\n{response2}\n\n"
            "For each masculine word, append a row of data to a TSV table. If the list is empty, return 'None' instead of a table.\n"
            "Each row in the TSV table must contain exactly four tab-separated values:\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the masculine word is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide an explanation of the masculine word. The explanation must follow this template: 'Although the term **[masculine word]** is masculine, [the writer] is using the word in a generic sense that includes both men and women'. Replace the bracketed words with information from the verse and context. The word or words in double asterisks must be exact quotes from the verse."
            "\n(3) The third tab-separated value will contain an exact quote from the verse. This quote will provide the words that would need to be rephrased to refer directly to both male and female people. Make your answer as short as possible."
            "\n(4) The fourth tab-separated value will model how to rephrase the exact quote from the third value so that it refers directly to both male and female people. Make sure that the rephrased text can exactly replace the quote in the verse."
            "\nMake sure that the values in each row are consistent in how they identify, understand, and explain the masculine word.\n"
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
                note_template = f'{explanation}. If it would be helpful in your language, you could use a phrase that makes this clear. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-gendernotations'
                
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
        file_name = 'ai_gender.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_gender.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    gender_instance = Gender(book_name)
    gender_instance.run()
