from TNPrepper import TNPrepper
from groq import Groq
import re
import os
import csv
from dotenv import load_dotenv

class Personification(TNPrepper):
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
    "You have been given a chapter from the Bible. Please identify every occurrence of personification in this chapter, if any. Be sure that what you identify is not better classified as a different figure of speech, such as metaphor or simile.\n"
    "Personification is a figure of speech where a non-human thing is described as having human attributes, actions, or emotions. It involves giving human-like qualities to animals, objects, or abstract concepts.\n"
    "Do not confuse personification with metaphor, which directly compares two unlike things, or simile, which compares two unlike things using 'like' or 'as'.\n"
    "Before identifying personification, ask yourself if the entity being described can logically possess human traits, actions, or emotions. If it cannot, then it is likely personification.\n"
    "Do not consider groups of people (e.g., 'thieves', 'nations') or anthropomorphism (gods or animals given human traits) as personification.\n"
    "Provide a table with exactly six tab-separated values as your answer. Do not provide any explanation or introduction. You should answer with the table only.\n"
    "The first column should provide the chapter and verse for the found instance of personification. Do not include the book name.\n"
    "The second column should provide the clause that has the personification. Do not include any explanation or introduction.\n"
    "The third column should provide a one-sentence explanation of the identified personification. The sentence should have this form: 'Here, the speaker speaks of [thing personified] as if it/they were a person/people who could [the thing that it does].' Replace the information in square brackets with the appropriate information.\n"
    "The fourth column should provide a way to express the words from the second column without using personification. Only include the alternate phrase. Do not include any introduction or explanation.\n"
    "The fifth column should include an exact quote from the verse. This quote should be semantically equivalent to the alternate expression you provided in the fourth column. Be sure that the quote you provide is precisely from the relevant verse.\n"
    "The sixth column should indicate who speaks or writes the personification.\n"
    "Here is an example of what a line would look like:\n\n"
    "2:10\tmountain was lonely\tHere, the speaker speaks of a mountain as if it were a person who could be lonely.\tthere were no other mountains nearby that mountain\tthat mountain was lonely\tthe poet\n"
    "Be sure that each row contains exactly six values.\n"
    "Before you answer with the table, check whether the thing that you identified as personified in context might refer to a person (such as 'thieves' or 'savior'). If it might refer to a person, remove that row.\n"
    "Additionally, ensure that the personification does not involve anthropomorphism, where gods or animals are given human traits, as these are not considered personification in this context.\n"
    "If you are unsure whether a clause is personification, do not include it in the table."
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
                        'Personification': columns[1],
                        'Explanation': columns[2],
                        'Alternate Translation': columns[3],
                        'Snippet': columns[4],
                        'Speaker': columns[5]
                    }
                    mod_ai_data.append(row_dict)

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
        self._write_output(book_name, file='transformed_ai_personification.tsv', headers=headers_transformed, data=transformed_data)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    personification_instance = Personification(book_name)
    personification_instance.run()
