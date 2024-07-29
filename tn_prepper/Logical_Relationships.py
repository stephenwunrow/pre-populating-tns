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

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "You have been given a chapter from the Bible. Identify every conjunction and transition word that introduces a condition, a contrast, a purpose, a reason, a result, or an exception.\n"
            "List each one you identify. Each entry should contain the reference, the conjunction or transition word, and the function.\n"
            "For the function, you must use one of these exact terms: contrast, result, purpose, contrary to fact condition, factual condition, hypothetical condition, exception, addition.\n"
            "Important: be sure that the word or phrase you identify is actually a transition word or conjunction, not some other part of speech."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of possible transition words or phrases from this chapter:\n{response1}\n\n"
            "First, check this list to make sure that the identified words are actually transition words or conjunctions. If they are not, remove them from the list.\n"
            "Second, consider the identified function in context. If the identified function is incorrect, replace the label with one of these exact labels: contrast, result, purpose, contrary to fact condition, factual condition, hypothetical condition, exception, addition.\n"
            "Return the list with any false positives removed and any false identifications corrected. Only return the revised list."
        )

        response3 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of significant conjunctions and transition words in this chapter:\n{response3}\n\n"
            "Analyze these conjunctions and transition words in context. As your answer, you will provide a table with exactly five tab-separated values for each word or phrase in the provided list."
            "\n(1) The first column will provide the chapter and verse where the conjunction or transition word is found. Do not include the book name."
            "\n(2) The second column will indicate the precise function of the transition word or conjunction in context. You must identify one of the following functions: contrast, result, purpose, contrary to fact condition, factual condition, hypothetical condition, exception, addition."
            "\n(3) The third column will provide a one sentence explanation of the function of the transition word or conjunction in context. The sentence should begin with this phrase: 'The word **word** here'."
            "\n(4) The fourth column will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to express the idea with a different transition word or phrase."
            "\n(5) The fifth column will provide a way to express the exact quote from the fourth value with a different transition word or phrase."
            "Be sure that the values in each row are consistent in how they understand the transition word or conjunction.\n"
            "Here is an example of what your response might look like:\n\n"
            "1:4\tcontrast\tThe word **but** here introduces a contrast with what Jonah said in the previous verse.\tbut\tin contrast\n"
            "3:5\tresult\tThe word **And** here connects the response of the men of Nineveh to Jonah's proclamation.\tAnd he\tSo he"
        )
        return self._query_openai(chapter_content, prompt3)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                snippet = row['Snippet'].strip('\'".,;!?“”’‘ ')
                explanation = row['Explanation'].strip('\'".,;!?“”’‘ ')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘ ')
                alt_translation = re.sub(r'\*', '', alt_translation)
                function = row['Function'].strip('\'".,;!?“”’‘ ')
                if function.lower() == 'contrast':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-contrast'
                    note_template = f'{explanation}. In your translation, indicate this strong contrast in a way that is natural in your language. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'goal':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-goal'
                    note_template = f'{explanation}. Use a connector in your language that makes it clear that this is the purpose. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'result':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-result'
                    note_template = f'{explanation}. Use a connector in your language that makes it clear that what follows is a result of what came before. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'reason':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-logic-result'
                    note_template = f'{explanation}. Use a connector in your language that makes it clear that what follows is a reason. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'contrary to fact condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-contrary'
                    note_template = f'{explanation}. Use a natural form in your language for introducing a condition that the speaker believes is not true. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'factual condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-fact'
                    note_template = f'{explanation}. If your language does not state something as a condition if it is certain or true, and if your readers might think that what the speaker is saying is uncertain, then you could translate his words as an affirmative statement. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'hypothetical condition':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-condition-hypothetical'
                    note_template = f'{explanation}. Use a natural form in your language for introducing a situation that could happen. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'exception':
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-exceptions'
                    note_template = f'{explanation}. If, in your language, it would appear that the speaker were making a statement here and then contradicting it, you could reword this to avoid using an exception clause. Alternate translation: “{alt_translation}”'
                elif function.lower() == 'addition':
                    continue
                else:
                    support_reference = 'rc://*/ta/man/translate/grammar-connect-words-phrases'
                    note_template = f'{explanation}. Use a natural form in your language for connecting this statement to the previous one. Alternate translation: “{alt_translation}”'
                
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
                        'Function': columns[1],
                        'Explanation': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Function', 'Explanation', 'Snippet', 'Alternate Translation']
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
