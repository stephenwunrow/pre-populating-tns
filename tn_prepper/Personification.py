from TNPrepper import TNPrepper
from groq import Groq
import re
import os
import csv
from dotenv import load_dotenv

class Personification(TNPrepper):
    def __init__(self):
        super().__init__()

        load_dotenv()

        api_key = os.getenv('API_KEY')
        self.verse_text = os.getenv('VERSE_TEXT')

        # Initialize the Groq client with your API key
        self.groq_client = Groq(api_key=api_key)
        self.groq_model = 'llama3-70b-8192'

    def __process_personification(self, chapter_content):
        prompt = (
            "You have been given a chapter from the Bible. Please identify every occurrence of the figure of speech 'personification' in this chapter. Be sure that the personification you identify is not better classified as a different figure of speech. "
            "You should provide a table with tab-separated values as your answer. Do not provide any explanation or introduction. You should answer with the table only. "
            "The first column should provide the chapter and verse for the found instance of personification. Do not include the book name."
            "The second column should provide the clause that has the personification. Do not include any explanation or introduction. "
            "The third column should provide a one sentence explanation of the identified personification. The sentence have this form: 'Here, the speaker speaks of [thing personified] as if it were a person who could [the thing that it does].' Replace the information in square brackets with the appropriate information. "
            "The fourth column should provide a way to express the words from the second column without using personification. Only include the alternate phrase. Do not include any introduction or explanation. "
            "The fifth column should give the exact words from the verse that are semantically equivalent to the phrase you provided in the fourth column. "
            "The sixth column should indicate who speaks or writes the personification. Here is an example of what a line would look like: "
            "2:10\tmountain was lonely\tHere, the speaker speaks of a mountain as if it were a person who could be lonely.\tthere were no other mountains nearby that mountain\tthat mountain was lonely\tthe poet"
        )
        return self._query_llm(chapter_content, prompt)

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
            response = self.__process_personification(chapter_content)
            if response:
                ai_data.append(response.split('\n'))
        
        # Flatten the list of lists into a single list of dictionaries
        mod_ai_data = []
        for row_list in ai_data:
            print(row_list)
            for row in row_list:
                columns = row.split('\t')
                if len(columns) == 6:
                    row_dict = {
                        'Reference': columns[0],
                        'Personification': columns[1],
                        'Explanation': columns[2],
                        'Alternate Translation': columns[3],
                        'Snippet': columns[4],
                        'Speaker': columns[5]
                    }
                    mod_ai_data.append(row_dict)
                    print(mod_ai_data)

        # Write the results to a new TSV file
        headers = ['Reference', 'Personification', 'Explanation', 'Alternate Translation', 'Snippet', 'Speaker']
        file_name = 'ai_personification.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        # Prepare transformed data and write to another TSV file
        transformed_data = []
        for row in mod_ai_data:
            ref = row['Reference']
            explanation = row['Explanation'].strip('\'".,;!?“”’‘')
            alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
            snippet = row['Snippet'].strip('\'".,;!?“”’‘')
            speaker = row['Speaker'].strip('\'".,;!?“”’‘')

            mod_explanation = re.sub(rf'(Here, )(the speaker)', rf'\1{speaker}', explanation)
            support_reference = 'rc://*/ta/man/translate/figs-personification'
            note_template = f'{mod_explanation}. If it would be helpful in your language, you could express the meaning plainly. Alternate translation: “{alt_translation}”'

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

        # Write transformed data to another TSV file
        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name='Obadiah', file='transformed_ai_personification.tsv', headers=headers_transformed, data=transformed_data)

if __name__ == "__main__":
    personification_instance = Personification()
    personification_instance.run()
