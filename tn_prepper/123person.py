from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Person(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "Sometimes, when they are talking, people use the third person when the second or first person would be more natural. There are several reasons why someone might do this, but respect toward a superior is a common one.\n"
            "You have been given a chapter from the Bible. Please identify each time a speaker uses the third person when the first or second person would have been more natural. Be sure that what you identify is in a quote and uses the third person in a place that would normally use the first or second person.\n"
            "Return a list with the reference, the relevant phrase, and whether the speaker is using the third person instead of the second person or instead of the first person. If there are several occurrences in one verse, include them all in one line. If there are no relevant phrases, return 'None'."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of places where people might be using the third person when the second or first person would be more natural:\n{response1}\n\n"
            "Please examine this list in context to see if it is correct. If you find any lines that do not include a person referring to themselves or their conversation partner in the third person, remove them. If you find any lines that contain text that is not from a quotation, remove them.\n"
            "Return the revised list only. If the list is empty, return 'None'."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of places where people refer to themselves or to the people with whom they are speaking in the third person:\n{response2}\n\n"
            "For each instance, append a row of exactly four tab-separated values to a TSV table. If there are multiple instances in a verse of the same type, address all of them with one row. Here is what you should include in each row:"
            "\n(1) The first tab-separated value will provide the chapter and verse where the identified instance is found. Do not include the book name."
            "\n(2) The second tab-separated value will indicate whether it would be more natural to use the first or the second person here. Use the word 'first' the word 'second' as your answer."
            "\n(3) The third tab-separated value will provide an explanation of the issue. If it would be more natural to use the first person, use this template: '[Speaker] is speaking about himself in the third person. If this would not be natural in your language, you could use the first person form'."
            "If it would be more natural to use the second person, use this template: 'Here [Speaker] addresses [Recipient] in the third person to [function]. If this would not be natural in your language, you could use the second-person form and indicate the [function] in another way'. Replace the bracketed phrases with the appropriate information from the verse (without brackets)."
            "\n(4) The fourth tab-separated value will provide an exact quote from the verse. This quote will include the section of the verse that will need to be rephrased in order to model how to express the idea in first or second person instead of third person."
            "\n(5) The fifth tab-separated value will rephrase the exact quote from the third tab-separated value. The rephrased text will model how to express the idea in first or second person instead of third person. Ensure that the rephrased text is as close as possible to the exact quote and can exactly replace the quote."
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
                support_reference = 'rc://*/ta/man/translate/figs-123person'
                note_template = f'{explanation}. Alternate translation: “{alt_translation}”'
                
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
                        'Speaker': columns[1],
                        'Explanation': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4],
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Speaker', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_123person.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_123person.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    person_instance = Person(book_name)
    person_instance.run()
