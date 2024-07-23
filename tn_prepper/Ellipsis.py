from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Ellipsis(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt = (
            "A clause must contain a subject and a main verb. Ellipsis occurs when the subject or main verb in a clause is omitted but can be inferred from the context. You have been given a chapter from the Bible. Identify all places where there is ellipsis, if any.\n"
            "As your answer, you will provide a TSV table with exactly four tab-separated values. If there are multiple places in a verse where ellipsis occurs, include a separate row in the able for each one.\n"
            "\n(1) The first column will provide the chapter and verse where the ellipsis occurs. Do not include the book name."
            "\n(2) The second column will name who writes or speaks the ellipsis."
            "\n(3) The third column will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to make the omitted words explicit."
            "\n(4) The fourth column will provide a way to express the exact quote from the fourth value with the omitted words made explicit. The rephrased text should be as similar to the quote as possible, adding as few words as possible to make the omitted words explicit."
            "\nBe sure that the items in each row are consistent in how they understand the ellipsis."
            "\n# Important:"
            "\n\t• Focus on identifying ellipsis where the subject or main verb is omitted."
            "\n\t• Do not include conjunctions or repetitive structures unless they omit the subject or main verb."
            "\n\t• Ensure that the rephrased quote maintains the original meaning by only adding the necessary omitted words."
            "\n\t• Be completely sure that there is an ellipsis. It is better to have no data than to have false data."
            "\n# Example:"
            "\n\t• Original verse: 'so his life abhors bread, and his soul food of desire'"
            "\n\t• Identified instance of ellipsis: 'his soul food of desire'"
            "\n\t• Rephrased instance: 'his sould abhors food of desire'"
        )

        return self._query_openai(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference'].strip('\'".,;!?“”’‘')
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                note_template = f'{explanation} is leaving out some of the words that in many languages a sentence would need in order to be complete. You could supply these words from earlier in the sentence if it would be clearer in your language. Alternate translation: “{alt_translation}”'
                support_reference = 'rc://*/ta/man/translate/figs-ellipsis'
                
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
                        'Snippet': columns[2],
                        'Alternate Translation': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_ellipsis.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_ellipsis.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    ellipsis_instance = Ellipsis(book_name)
    ellipsis_instance.run()