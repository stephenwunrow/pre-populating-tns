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

    def __process_prompt1(self, chapter_content):
        prompt = (
            "Ellipsis occurs when an author repeats the structure of a preceding clause but omits some of the key grammatical elements, usually the subject and/or main verb. Authors do this because readers can infer the omitted elements from the preceding clause.\n"
            "You have been given a chapter from the Bible. Identify the subject and main verb in each independent and dependent clause in this chapter. If the subject and/or verb are omitted, identify the clause as ellipsis.\n"
            "In your answer, make sure to include the clause, the subject, the verb, and whether there is ellipsis or not. Provide the data in this form:\n"
            "**Book_Name Chapter:Verse**\n"
            "**Clause**: clause_text\n"
            "**Subject**: subject_text\n"
            "**Verb**: verb_text\n"
            "**Ellipsis**: either 'Yes' or 'No'\n\n"
        )

        return self._query_openai(chapter_content, prompt)
    
    def __process_prompt2(self, chapter_content, ellipses):
        prompt = (
            f"Here is a set of possible ellipses in this chapter: {ellipses}.\n"
            "For each ellipsis, analyze the data and the chapter. Make sure that each possible ellipsis is a true case of ellipsis.\n"
            "Then, for each true case of ellipsis, provide a TSV table with four tab-separated columns:"
            "\n(1) The first column will provide the chapter and verse where the ellipsis occurs. Do not include the book name."
            "\n(2) The second column will name the person who wrote or spoke the verse in the chapter context."
            "\n(3) The third column will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to make the omitted words explicit."
            "\n(4) The fourth column will provide a way to express the exact quote from the fourth value with the omitted words made explicit. The rephrased text should be as similar to the quote as possible, adding as few words as possible to make the omitted words explicit."
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

        for chapter_key, verses in chapters.items():
            ellipses = []
            # Combine verses into chapter context
            chapter_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
            response1 = self.__process_prompt1(chapter_content)
            if response1:
                ellipsis_search = re.compile(fr'\*\*{book_name} (\d+:\d+)\*\*[^\n]*\n\*\*Clause\*\*: ([^\n]+)\n\*\*Subject\*\*: ([^\n]+)\n\*\*Verb\*\*: ([^\n]+)\n\*\*Ellipsis\*\*: Yes')
                matches = ellipsis_search.findall(response1)
                for match in matches:
                    print(match)
                    ellipses.append({
                        "Reference": match[0],
                        "Clause": match[1],
                        "Subject": match[2],
                        "Verb": match[3],
                    })
            print(ellipses)


        # Process each chapter for personification
        ai_data = []
        for chapter_key, verses in chapters.items():
            # Combine verses into chapter context
            chapter_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
            response2 = self.__process_prompt2(chapter_content, ellipses)
            if response2:
                ai_data.append(response2.split('\n'))
        
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
