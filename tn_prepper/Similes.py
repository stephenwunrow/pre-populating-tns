from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
from dotenv import load_dotenv

class Similes(TNPrepper):
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
            "A simile is a comparison that must use the words 'like' or 'as'. You have been given a chapter from the Bible. Please identify similes in the chapter, if any.\n"
            "As your answer, you will provide a table with exactly four tab-separated values. Do not include any introduction or explanation with the table. For example, do not include a phrase such as 'Here is the table...'\n"
            "\n(1) The first column will provide the chapter and verse where the simile is found. Do not include the book name."
            "\n(2) The second column will provide a one-sentence explanation of the simile. The explanation sentence should begin this way: 'The point of this comparison is that'. Direct references to key words from the verse should be inside double asterisks (like this: **word**). "
            "\n(3) The third column will provide a way to express the idea in a way that explicitly explains the simile. "
            "\n(4) The fourth column will include an exact quote from the verse. This quote should be precisely semantically equivalent to the alternate expression you provided in the third column. Be sure that the quote you provide is precisely from the relevant verse.\n"
            "\nBe sure that the items in each row are consistent in how they understand the simile.\n"
            "Here is an example of what your response might look like:\n\n"
            "38:14\tThe point of this comparison is that just as plain **clay** takes on distinct features when it is pressed **under a seal**, so the features of the earth become distinct in the light of day.\tIts features change from indistinct to distinct, just as clay takes on distinct features when it is pressed under a seal\tIt is changed like clay under a seal\n"
            "38:30\tThe point of this comparison is that just as it is not possible to see through **stone**, it is typically not possible to see through the ice that forms on top of **the waters** in the winter.\tAs under stone through which one cannot see\tAs under stone\n\n"
            "Before you return the table, check each row to make sure that the identified simile does use 'like' or 'as'. If the row does not, remove it from the table."
        )

        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference'].strip('\'".,;!?“”’‘')
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                note_template = f'{explanation}. If it would be helpful in your language, you could make this point explicitly. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-simile'
                
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
        file_name = 'ai_similes.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_similes.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    similes_instance = Similes(book_name)
    similes_instance.run()
