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
            "You have been given a chapter from the Bible. Please identify any doublets in the chapter. A doublet is made up of two words or very short phrases that have the same meaning and that are joined by the word 'and'. The structure must be like this: '[word\phrase 1] and [word\phrase 2]'.\n"
            "When you find a doublet, you will append a row of data to a table. Each row should contain exactly six tab-separated values. Do not include any introduction or explanation with the table.\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the doublet is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide the first word or short phrase in the doublet. Quote exactly from the verse. "
            "\n(3) The third tab-separated value will provide the second word or short phrase in the doublet. Quote exactly from the verse. "
            "\n(4) The fourth tab-separated value will provide a way to express the clause without using two words with the same meaning. Be sure that you rephrase the entire section of the verse that includes the doublet. "
            "\n(5) The fifth tab-separated value will include an exact quote from the verse. This quote should be semantically equivalent to the alternate expression you provided in the fourth value. Be sure that the quote you provide is precisely from the relevant verse."
            "\n(6) The sixth tab-separated value will identify who writes or speaks the doublet. "
            "Be sure that the items in each row are consistent in how they understand the doublet.\n"
            "Here are two examples of what the rows of values might look like:\n\n"
            "34:22\tdarkness\tdeep darkness\tThere is no darkness at all\tThere is no darkness and there is no deep darkness\tElihu\n"
            "34:28\tObserve\tsee\tCarefully observe the heavens\tObserve the heavens and see\tElihu\n"
        )
        return self._query_llm(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                word_1 = row['Word 1']
                word_2 = row['Word 2']
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                speaker = row['Speaker'].strip('\'".,;!?“”’‘')
                note_template = f'The terms **{word_1}** and **{word_2}** mean similar things. {speaker} is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: “{alt_translation}”'
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
                if len(columns) == 6:
                    row_dict = {
                        'Reference': columns[0],
                        'Word 1': columns[1],
                        'Word 2': columns[2],
                        'Alternate Translation': columns[3],
                        'Snippet': columns[4],
                        'Speaker': columns[5]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Word 1', 'Word 2', 'Alternate Translation', 'Snippet', 'Speaker']
        file_name = 'ai_doublets.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_doublets.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    doublets_instance = Doublets(book_name)
    doublets_instance.run()
