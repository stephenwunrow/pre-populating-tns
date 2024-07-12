from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
from dotenv import load_dotenv

class Doublets(TNPrepper):
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
            "A doublet is two or more words or very short phrases that mean the same thing and that are used in the same phrase. In the chapter of the Bible provided above, identify each doublet. Be sure that what you identify is not better labeled as a different figure of speech, such as parallelism.\n"
            "When you find a doublet, you will append a row of data to a table. Each row should contain exactly four tab-separated values, no more or less. Do not include any introduction or explanation with the table. For example, do not include a phrase such as 'Here is the table...'\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the doublet is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide an explanation of the doublet. The explanation must be in this form: 'The terms **[word/phrase 1]** and **[word/phrase 2]** mean similar things. [Speaker/Writer] is using the two terms together for emphasis.' Use these exact sentences, including the asterisks, except you should replace the bracketed words with the appropriate data from the verse."
            "\n(3) The third tab-separated value will provide a way to express the clause from the verse that contains the doublet without using a doublet."
            "\n(4) For the fourth tab-separated value, ask yourself this question: 'Which exact words from the verse are the words you provided in the third tab-separated value semantically equivalent to?' Be sure that your answer is an exact quote from the verse."
            "Be sure that the items in each row are consistent in how they understand the doublet.\n"
            "Here are two examples of what the rows of values might look like:\n\n"
            "34:22\tThe terms **darkness** and **deep darkness** mean similar things. Elihu is using the two terms together for emphasis.\tThere is no darkness at all\tThere is no darkness and there is no deep darkness\n"
            "34:28\tThe terms **Observe** and **see** mean similar things. Elihu is using the two terms together for emphasis.\tCarefully observe the heavens\tObserve the heavens and see\n"
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
                note_template = f'{explanation}. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-doublet'
                
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
                if len(columns) == 4:
                    row_dict = {
                        'Reference': columns[0],
                        'Explanation': columns[1],
                        'Alternate Translation': columns[2],
                        'Snippet': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Explanation', 'Alternate Translation', 'Snippet']
        file_name = 'test_doublets.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_test_doublets.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    doublets_instance = Doublets(book_name)
    doublets_instance.run()