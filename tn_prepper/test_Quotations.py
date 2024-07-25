from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Quotations(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt = (
            "In the Bible, quotations can be either direct, indirect, or within another quote. For whichever type of quotation appears in a sentence, I want to provide the other option in my notes. You have been given a chapter from the Bible. Please identify all direct, indirect, and quote-in-quote quotations that are contained within a verse.\n"
            "When you find a direct, indirect, or quote-in quote quotation, you will append a row of data to a TSV table. If there are multiple quotations in a verse, include a separate row for each one.\n"
            "Each row must contain exactly five tab-separated values:\n"
            "\n(1) The first tab-separated value will provide the chapter and verse where the quotation is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide the words from the verse that contain the direct or indirect quotation, as well as the words that indicate who is speaking the quote. Quote exactly from the verse."
            "\n(3) The third tab-separated value will identify whether the quote is 'direct', 'indirect', or 'quote-in-quote'."
            "\n(4) The fourth tab-separated value will provide an exact quote from the verse. This quote will include the section of the verse that will need to be rephrased in order to express a direct quote indirectly, an indirect quote directly, or a quote-in-quote indirectly. It will also include the words that indicate who is speaking the quote."
            "\n(5) The fifth tab-separated value will rephrase the exact quote from the fourth tab-separated value. The rephrased text will model how to rephrase a direct quote as an indirect quote, an indirect quote as a direct quote, or a quote-in-quote as an indirect quote. Ensure that the rephrased text is as close as possible to the exact quote and can exactly replace the quote."
            "\nMake sure that the values in each row are consistent in how they identify, understand, and explain the quotation.\n"
        )
        return self._query_openai(chapter_content, prompt)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                function = row['Type'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'",;!?“”’‘')
                if 'indirect' in function.lower():
                    note_template = f'It may be more natural in your language to have a direct quotation here. Alternate translation: “{alt_translation}”'
                    support_reference = 'rc://*/ta/man/translate/figs-quotations'
                elif 'direct' in function.lower():
                    note_template = f'It may be more natural in your language to have an indirect quotation here. Alternate translation: “{alt_translation}”'
                    support_reference = 'rc://*/ta/man/translate/figs-quotations'
                elif 'quote-in-quote' in function.lower():
                    note_template = f'If it would be clearer in your language, you could translate this so that there is not a quotation within a quotation. Alternate translation: “{alt_translation}”'
                    support_reference = 'rc://*/ta/man/translate/figs-quotesinquotes'
                else:
                    note_template = f'It may be more natural in your language to use a different form to express the quotation here. Alternate translation: “{alt_translation}”'
                
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
                        'Quotation': columns[1],
                        'Type': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Quotation', 'Type', 'Snippet', 'Alternate Translation']
        file_name = 'ai_quotations.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_quotations.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    quotations_instance = Quotations(book_name)
    quotations_instance.run()
