from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
from dotenv import load_dotenv

class Parallelism(TNPrepper):
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
            "In parallelism, two clauses that have equivalent meanings are used together for poetic effect. In the chapter from the Bible above, identify each parallelism. Be sure that the clauses identified as parallel are within one verse and have equivalent meanings.\n\n"
            "Provide your answer in table form without any introduction or explanation. Each row should contain exactly four tab-separated values:\n\n"
            "1. The first value must be the chapter and verse where the parallelism is found (without the book name).\n"
            "2. The second value must be the two clauses that make up the parallelism. You should quote exactly from the chapter.\n"
            "3. The third value must be a way to express the two parallel clauses you quoted as only one clause. Be sure that this clause can completely replace the two clauses you quoted.\n"
            "4. The fourth value must identify who writes or speaks the parallelism.\n\n"
            "Ensure consistency in how you understand and present the parallelism.\n\n"
            "Example response:\n\n"
            "30:23\tto death and to the house of appointment to all the living\tto death, yes, to the house of appointment to all the living\tJob\n"
            "30:26\tThe deep says, ‘It is not in me,’ and the sea says, ‘It is not with me.’\tThe deep, wide ocean says, ‘It is not in me’\tJob\n\n"
            "Be sure that there are only four values in each row, as in the above example."

        )
        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                snippet = row['Phrases'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                speaker = row['Speaker'].strip('\'".,;!?“”’‘')
                note_template = f'These two phrases mean similar things. {speaker} is using repetition to emphasize the idea that the phrases express. If it would be helpful to your readers, you could indicate that by using a word other than “and” in your translation. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-parallelism'
                
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
                        'Phrases': columns[1],
                        'Alternate Translation': columns[2],
                        'Speaker': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Phrases', 'Alternate Translation', 'Speaker']
        file_name = 'ai_parallelism.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_parallelism.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    parallelism_instance = Parallelism(book_name)
    parallelism_instance.run()