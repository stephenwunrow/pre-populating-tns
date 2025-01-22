from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Pronouns(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        # Get the AI model type and corresponding query function
        which_ai = os.getenv('WHICH_AI')
        if which_ai == 'openai':
            query_func = self._query_openai
        elif which_ai == 'gemini':
            query_func = self._query_gemini
        elif which_ai == 'claude':
            query_func = self._query_claude
        else:
            raise ValueError(f"Invalid AI model specified: {which_ai}")        

        prompt1 = (
            "<instructions>You have been given a chapter from the Bible. For each pronoun, determine whether its referent is clear from the context of the text. Check possessive pronouns and demonstratives. A pronoun is considered unclear if a reader would have difficulty identifying what or whom the pronoun refers to without additional context. Sometimes this happens when there is a person number mismatch (you for happens in Hebrew at times or vice-versa). Confusion can also hapeen in regards to who is included, sometimes a prophet might say your, but he could be included in the group of people he is talking about. \n"
            "List only those pronouns where the referent is ambiguous or not immediately apparent. For each unclear pronoun, provide its possible referent(s).\n"
            "Be sure to include all pronouns that do not have an explicit referent earlier in the chapter, including indefinite or impersonal 'they'."
            "If none of the pronouns have unclear referents, do not provide any list. Instead, return 'NONE_FOUND'."
            "</instructions>\n"
        )
        
        response1 = query_func(chapter_content, prompt=prompt1, temp=0.8)
        print(f"\nResponse 1: {response1}")
        self.write_to_log()

        # Only proceed if we got a valid response and it's not NONE_FOUND
        if not response1 or 'NONE_FOUND' in response1:
            print("No unclear pronouns found in first pass")
            self.write_to_log()
            return None

        prompt2 = (
            "<instructions>You have been given a chapter from the Bible. I will now provide you with a list of pronouns whose referents may not be clear from the context of the text. A pronoun is considered unclear if a reader would have difficulty identifying what or whom the pronoun refers to without additional context.\n\n"
            f"List:\n<data>{response1}</data>\n\n"
            "Analyze the list and considering their context in the chapter, return only those pronouns that have unclear referents, including indefinite or impersonal 'they'. If none of the pronouns have unclear referents, do not provide any list. Instead, return 'NONE_FOUND'."
            "</instructions>\n"
        )

        response2 = query_func(chapter_content, prompt2, temp= 0.8)
        print(f"\nResponse 2: {response2}")
        self.write_to_log()

        # Only proceed if we got a valid response and it's not NONE_FOUND
        if not response2 or 'NONE_FOUND' in response2:
            print("No unclear pronouns found in second pass")
            self.write_to_log()
            return None

        prompt3 = (
            f"<instructions>You have been given a chapter from the Bible. Here is a list of pronouns whose referent is unclear:\n<data>{response2}</data>\n\n"
            "If the list is empty or 'NONE_FOUND', respond with 'NONE_FOUND'. Otherwise, create a TSV table of exactly four columns of data based on the list and the chapter."
            "\n(1) The first column will contain the reference for the verse where the pronoun is found. Do not include the book name."
            "\n(2) The second column will contain the pronoun whose referent is unclear."
            "\n(3) The third column will provide an explanation. You must follow this template: <formatting>The pronoun **[pronoun]** refers to [the referent]. If this is not clear for your readers, you could refer to [the referent] directly.</formatting>"
            "\n(4) The fourth column will provide an exact quote from the verse. This quote will contain the word or words from the verse that would need to be rephrased to make the reference clear."
            "\n(5) The fifth column will model how the quote from the fourth column could be rephrased so the referent is clear. Be sure that the word or words you provide exactly replace the quote from the fourth column."
            "Make sure that you are consistent in how you understand and interpret the pronoun across the columns, and use TSV format.</instructions>\n"
        )

        response3 = query_func(chapter_content, prompt3)
        print(f"\nResponse 3: {response3}")
        self.write_to_log()
        
        if not response3 or 'NONE_FOUND' in response3:
            print("No unclear pronouns found in final pass")
            self.write_to_log()
            return None
            
        return response3
        
    def _transform_response(self, mod_ai_data):
        transformed_data = []
        if mod_ai_data:            
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?""''')
                snippet = row['Snippet'].strip('\'".,;!""''')
                alt_translation = row['Alternate Translation'].strip('\'",;!?""''')
                alt_translation = re.sub(r'\*', '', alt_translation)
                note_template = f'{explanation}. Alternate translation: [{alt_translation}]'
                support_reference = 'rc://*/ta/man/translate/writing-pronouns'

                
                transformed_row = [
                ref,  # Reference
                'uw43',   # ID: random, unique four-letter and number combination
                '',   # Tags: blank
                support_reference,  # SupportReference: standard link
                snippet,  # Quote: lexeme
                '1',  # Occurrence: the number 1
                note_template  # Note: standard note with {gloss}
                
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

        # Check stage first
        if os.getenv('STAGE') == 'dev':
            # Then check for verse limit in dev mode
            dev_verse_limit = os.getenv('DEV_NUMBER_OF_VERSES')
            if dev_verse_limit:
                try:
                    dev_verse_limit = int(dev_verse_limit)
                    verse_texts = verse_texts[:dev_verse_limit]
                    print(f"Dev mode: Processing first {dev_verse_limit} verses")
                except ValueError:
                    print("Warning: Invalid 'DEV_NUMBER_OF_VERSES' value, processing all verses")
            else:
                print("Dev mode: No verse limit specified, processing all verses")
        
        print(f"Processing {len(verse_texts)} verses")
        self.write_to_log()

        # Organize verse texts by chapter
        chapters = {}
        for verse in verse_texts:
            reference = verse['Reference']
            # Skip section markers and handle malformed references
            if reference == '-' or ' ' not in reference:
                continue
            try:
                book_name, chapter_and_verse = reference.rsplit(' ', 1)
                chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
                if chapter not in chapters:
                    chapters[chapter] = []
                chapters[chapter].append(verse)
            except ValueError as e:
                print(f"Error processing reference '{reference}': {e}")
                self.write_to_log()
                continue

        # Process each chapter for personification
        ai_data = []
        for chapter_key, verses in chapters.items():
            # Combine verses into chapter context
            chapter_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
            print(f"\nProcessing chapter: {chapter_key}")
            self.write_to_log()
            
            response = self.__process_prompt(chapter_content)
            if response:
                ai_data.append(response.split('\n'))
                print(f"Found pronouns in {chapter_key}")
                self.write_to_log()
        
        # Flatten the list of lists into a single list of dictionaries
        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                columns = row.split('\t')
                if len(columns) == 5:
                    row_dict = {
                        'Reference': columns[0],
                        'Pronoun': columns[1],
                        'Explanation': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        print(f"\nFound {len(mod_ai_data)} pronouns to process")
        self.write_to_log()

        # Write the results to a new TSV file
        headers = ['Reference', 'Pronoun', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_pronouns.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)
        print(f"Wrote raw data to {file_name}")
        self.write_to_log()

        transformed_data = self._transform_response(mod_ai_data)
        if transformed_data:
            headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
            self._write_output(book_name, file='transformed_ai_pronouns.tsv', headers=headers_transformed, data=transformed_data)
            print(f"Wrote transformed data to transformed_ai_pronouns.tsv")
        else:
            print("No data to transform")
        self.write_to_log()


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    pronouns_instance = Pronouns(book_name)
    pronouns_instance.run()
