from TNPrepper import TNPrepper
from groq import Groq
import re
import os
import csv
from dotenv import load_dotenv

class LogicalRelationships(TNPrepper):
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
            "You have been given a chapter from the Bible. Please identify transition words that you find in the chapter. Only identify transition words that are significant for the logical structure of the chapter.\n"
            "As your answer, you will provide a table with exactly five tab-separated values. Do not include any introduction or explanation with the table. For example, do not include a phrase such as 'Here is the table...'\n"
            "\n(1) The first column will provide the chapter and verse where the transition word is found. Do not include the book name."
            "\n(2) The second column will provide the transition word. "
            "\n(3) The third column will provide a one sentence explanation of the function of the transition word in context. The sentence should begin with this phrase: 'The word **word** here'. "
            "\n(4) The fourth column will provide a way to express the idea without using the transition word that is in the verse. "
            "\n(5) The fifth column will indicate the precise function of the transition word in context. Here are your options: contrast, result, purpose, contrary to fact condition, factual condition, hypothetical condition, exception.\n\n"
            "Be sure that the items in each row are consistent in how they understand the transition word.\n"
            "Here is an example of what your response might look like:\n\n"
            "1:4\tbut\tThe word **but** here introduces a contrast with what Jonah said in the previous verse.\tin contrast\tcontrast\n"
            "3:5\tAnd\tThe word **And** here connects the response of the men of Nineveh to Jonah's proclamation.\tSo\tresult"
        )
        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                snippet = row['Transition'].strip('\'".,;!?“”’‘')
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                function = row['Function'].strip('\'".,;!?“”’‘')
                if function.lower() == 'contrast':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-contrast'
                    note_template = f'{explanation}. In your translation, indicate this strong contrast in a way that is natural in your language. Alternate translation: “{alt_translation}”'
                if function.lower() == 'goal':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-goal'
                    note_template = f'{explanation}. Use a connector in your language that makes it clear that this is the purpose. Alternate translation: “{alt_translation}”'
                if function.lower() == 'result':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-result'
                    note_template = f'{explanation}. Use a connector in your language that makes it clear that what follows is a result of what came before. Alternate translation: “{alt_translation}”'
                if function.lower() == 'contrary to fact condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-contrary'
                    note_template = f'{explanation}. Use a natural form in your language for introducing a condition that the speaker believes is not true. Alternate translation: “{alt_translation}”'
                if function.lower() == 'factual condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-fact'
                    note_template = f'{explanation}. If your language does not state something as a condition if it is certain or true, and if your readers might think that what the speaker is saying is uncertain, then you could translate his words as an affirmative statement. Alternate translation: “{alt_translation}”'
                if function.lower() == 'hypothetical condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-hypothetical'
                    note_template = f'{explanation}. Use a natural form in your language for introducing a situation that could happen. Alternate translation: “{alt_translation}”'
                if function.lower() == 'exception':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-exceptions'
                    note_template = f'{explanation}. If, in your language, it would appear that the speaker were making a statement here and then contradicting it, you could reword this to avoid using an exception clause. Alternate translation: “{alt_translation}”'
                
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
                        'Transition': columns[1],
                        'Explanation': columns[2],
                        'Alternate Translation': columns[3],
                        'Function': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Transition', 'Explanation', 'Alternate Translation', 'Snippet', 'Function']
        file_name = 'ai_relationships.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_relationships.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    relationships_instance = LogicalRelationships(book_name)
    relationships_instance.run()
