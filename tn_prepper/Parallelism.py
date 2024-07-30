from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Parallelism(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "In parallelism, two clauses that have similar grammatical structures and similar meanings are used together for poetic effect.\n"
            "In the chapter from the Bible above, identify any parallelisms. If there are no parallelisms, return 'None'."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of potential parallelisms in this chapter:\n{response1}\n\n"
            "Examine this list in context. If the two clauses do not have similar meaning, remove the line from the list. If the two clauses do not have similar grammatical structures, remove the line from the list. Return the revised list. If the revised list is empty, return 'None'."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of parallelisms from that chapter:\n{response2}\n\n"
            "If the list is empty, return 'None'. Otherwise, for each parallelism, you will append a row of data to a TSV table. Each row should contain exactly four tab-separated values:"
            "(1) The first tab-separated value will be the chapter and verse where the parallelism is found. Do not include the book name.\n"
            "(2) The second tab-separated value will be an exact quote from the verse. This quote must contain the two clauses that make up the parallelism.\n"
            "(3) The third tab-separated value will be a way to express the two parallel clauses you quoted as a single, simple clause. Be sure that this simple clause combines the ideas of the two clauses you quoted.\n"
            "(4) The fourth tab-separated value will identify who writes or speaks the parallelism.\n\n"
            "\nBe sure that the items in each row are consistent in how they understand the parallelism.\n"
        )
        return self._query_openai(chapter_content, prompt3)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                snippet = row['Phrases'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                alt_translation = re.sub(r'\*', '', alt_translation)
                speaker = row['Speaker'].strip('\'".,;!?“”’‘')
                note_template = f'These two phrases mean similar things. {speaker} is using repetition to emphasize the idea that the phrases express. If it would be helpful to your readers, you could indicate that by using a word other than “and” in your translation, or you could combine the phrases. Alternate translation: “{alt_translation}”'
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
