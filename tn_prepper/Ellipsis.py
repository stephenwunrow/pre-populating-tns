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
        prompt1 = (
            "You have been given a chapter from the Bible. Identify the subject and main verb in each independent and dependent clause in this chapter. If the subject and/or verb are omitted, identify the clause as 'ellipsis'.\n"
            "There are two exceptions to this rule: (1) imperative verbs are grammatically complete without a subject, so mark them as imperatives instead of ellipses, and (2) compound predicates have one subject with several verbs, so they count as a single clause.\n"
            "Be sure that you separate each sentence into its independent and dependent clauses before you provide your answer.\n"
            "In your answer, make sure to include the clause, the subject, the verb, and whether there is ellipsis or not. Provide the data in this form:\n"
            "**Book_Name Chapter:Verse**\n"
            "**Clause**: clause_text\n"
            "**Subject**: subject_text\n"
            "**Verb**: verb_text\n"
            "**Ellipsis**: either 'Yes' or 'No'\n\n"
            "Include the above set of data for every clause in the chapter. Make sure that you include the correct reference at the beginning of each and every entry.\n"
        )

        response1 = self._query_openai(chapter_content, prompt1)

        if response1:
            ellipses = []
            ellipsis_search = re.compile(fr'\*\*{book_name} (\d+:\d+)\*\*[^\n]*\n\*\*Clause\*\*: ([^\n]+)\n\*\*Subject\*\*: ([^\n]+)\n\*\*Verb\*\*: ([^\n]+)\n\*\*Ellipsis\*\*: Yes')
            matches = ellipsis_search.findall(response1)
            for match in matches:
                ellipses.append({
                    "Reference": match[0],
                    "Clause": match[1],
                    "Subject": match[2],
                    "Verb": match[3],
                })

        prompt2 = (
            f"In your previous response, you gave a set of possible ellipsis in the chapter: {ellipses}.\n"
            "If the set is empty, return the answer 'None'\n."
            "If the set contains at least one entry, for each ellipsis, analyze the data and the chapter. Make sure that each possible ellipsis is a true case of ellipsis. If it is not a true case of ellipsis, delete the row.\n"
            "Then, for each true case of ellipsis, provide a TSV table with four tab-separated columns:"
            "\n(1) The first column will provide the chapter and verse where the ellipsis occurs. Do not include the book name."
            "\n(2) The second column will name the person who wrote or spoke the verse in the chapter context."
            "\n(3) The third column will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to make the omitted words explicit."
            "\n(4) The fourth column will provide a way to express the exact quote from the fourth value with the omitted words made explicit. You should infer the omitted words from the previous clause(s). Ensure that the rephrased text fits naturally in the context and exactly replaces the quote.\n"
            "Ensure that your answer contains exactly these four columns in TSV format. Also, do not rephrase any figurative language."
        )

        return self._query_openai(chapter_content, prompt2)
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference'].strip('\'".,;!?“”’‘')
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘()')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘()')
                alt_translation = re.sub(r'\*', '', alt_translation)
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
