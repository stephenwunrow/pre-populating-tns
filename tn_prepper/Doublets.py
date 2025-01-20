from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv

class Doublets(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        load_dotenv()

        self.verse_text = f'output/{book_name}/ult_book.tsv'
    def __process_prompt(self, chapter_content):
        prompt1 = (
            "A doublet is two words or very short phrases that have the same meaning (or almost the same meaning) and that are joined directly by 'and'. This type of repetition emphasizes the meaning. Be sure that the words or phrases you identify are not full clauses.\n"
            "In the section of the Bible provided above, identify each doublet. Check the section again to make sure you didn't miss any doublets. If there are no doublets, return 'NONE_FOUND'.\n"
            "Only return the chapter:verse and the doublet text, no other text."
        )

        which_ai = os.getenv('WHICH_AI')
        
        if which_ai == 'openai':
            response1 = self._query_openai(chapter_content, prompt1)
        elif which_ai == 'gemini':
            response1 = self._query_gemini(chapter_content, prompt1) 
        elif which_ai == 'claude':
            response1 = self._query_claude(chapter_content, prompt1)
        else:
            raise ValueError(f"Invalid AI model specified: {which_ai}")

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of potential doublets in this chapter:\n{response1}\n\n"
            "Examine this list in context. If the two words or phrases do not have the same meaning (or almost the same meaning), remove the line from the list. If the two words or phrases are not joined directly by 'and', remove the line from the list. If the two words or phrases could be better considered parallelisms or a merism, remove the line from the list.  If one of the words or phrases could be used to modify the other (hendiadys) remove the item from the list. Return the revised list. If the revised list is empty, return 'NONE_FOUND'."
        )
        if 'NONE_FOUND' not in response1:
            if which_ai == 'openai':
                response2 = self._query_openai(chapter_content, prompt2)
            elif which_ai == 'gemini':
                response2 = self._query_gemini(chapter_content, prompt2)
            elif which_ai == 'claude':
                response2 = self._query_claude(chapter_content, prompt2)
        else:
            return None  # Returning null as instructed

        prompt3 = (
            f"You have been given a section from the Bible. Here is a list of doublets from that section:\n{response2}\n\n"
            "If the list is empty, return 'None'. Otherwise, for each doublet, you will append a row of data to a TSV table. Each row should contain exactly four tab-separated values:"
            "\n(1) The first tab-separated value will provide the chapter and verse where the doublet is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide an explanation of the doublet. The explanation must be in this form: 'The terms **[word/phrase 1]** and **[word/phrase 2]** mean similar things. [Speaker/Writer] is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.' Use these exact sentences, including the asterisks, except you should replace the bracketed words with the appropriate data from the verse."
            "\n(3) The third tab-separated value will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to express the idea without the doublet."
            "\n(4) The fourth tab-separated value will provide a way to express the quote from the third value without using both words or phrases. This alternate expression should be able to replace the quote in the verse context without losing any meaning."
            "\nBe sure that the items in each row are consistent in how they understand the doublet.\n"
        )
        if 'NONE_FOUND' not in response2:
            if which_ai == 'openai':
                return self._query_openai(chapter_content, prompt3)
            elif which_ai == 'gemini':
                return self._query_gemini(chapter_content, prompt3)
            elif which_ai == 'claude':
                return self._query_claude(chapter_content, prompt3)
            # print("test prompt3")
            # response3 = "test"
            # return response3
        else:
            return None  # Returning null as instructed
    
    
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?""''')
                snippet = row['Snippet'].strip('\'".,;!?""''')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?""''')
                alt_translation = re.sub(r'\*', '', alt_translation)
                note_template = f'{explanation}. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: [{alt_translation}]'
                support_reference = 'rc://*/ta/man/translate/figs-doublet'
                
                transformed_row = [
                    ref,  # Reference
                    '',   # ID: random, unique four-letter and number combination
                    '',   # Tags: blank
                    support_reference,  # SupportReference: standard link
                    snippet,  # Quote
                    '1',  # Occurrence: the number 1
                    note_template  # Note: standard note with {gloss}
                ]
                transformed_data.append(transformed_row)
        else:
            return None
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

        # Organize verse texts by chapter & section
        chapters = {}
        current_section = []
        sections_count = 0
        dev_mode = os.getenv('STAGE') == 'dev'
        dev_section_limit = 5  # Define limit in one place for easier modification
        
        # First pass: organize verses into sections
        for verse in verse_texts:
            reference = verse['Reference']
            if reference == '-':
                # End current section if not empty
                if current_section and current_section[0]['Reference'] != '-':
                    book_name, chapter_and_verse = current_section[0]['Reference'].rsplit(' ', 1)
                    chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
                    if chapter not in chapters:
                        chapters[chapter] = []
                    chapters[chapter].append(current_section)
                    sections_count += 1
                    if dev_mode and sections_count >= dev_section_limit:
                        break
                current_section = []
            else:
                current_section.append(verse)
                
        # Add final section if not empty and we haven't hit section limit
        if current_section and (not dev_mode or sections_count < dev_section_limit):
            book_name, chapter_and_verse = current_section[0]['Reference'].rsplit(' ', 1) 
            chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(current_section)

        # Process each chapter's sections for doublets
        ai_data = []
        for chapter_key, sections in chapters.items():
            # Process each section within the chapter
            for i, section in enumerate(sections, 1):
                section_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in section])
                print(f"Processing section {i} of {len(sections)} in {chapter_key}")
                response = self.__process_prompt(section_content)
                if response:
                    ai_data.append(response.split('\n'))

        # Check if any AI data was generated before proceeding
        if not ai_data:
            print("No doublets were identified. Exiting...")
            return

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
        file_name = 'ai_doublets.tsv'
        self._write_fieldnames_to_tsv(book_name, file_name, mod_ai_data, headers)

        self.process_transformed_data(book_name)

    def process_transformed_data(self, book_name):
        """
        Process and write transformed data to a TSV file.
        
        Args:
            book_name: Name of the book being processed
        """
        # Read the AI doublets file
        input_file = f'output/{book_name}/ai_doublets.tsv'
        mod_ai_data = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            # Skip header line
            next(f)
            for line in f:
                columns = line.strip().split('\t')
                if len(columns) == 4:
                    row_dict = {
                        'Reference': columns[0],
                        'Explanation': columns[1], 
                        'Snippet': columns[2],
                        'Alternate Translation': columns[3]
                    }
                    mod_ai_data.append(row_dict)

        transformed_data = self._transform_response(mod_ai_data)
        if transformed_data:
            headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note']
            self._write_output(book_name, file='transformed_ai_doublets.tsv', headers=headers_transformed, data=transformed_data)
        else:
            print("No data to transform. Skipping transformed output file.")


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    doublets_instance = Doublets(book_name)
    # Run full process
    # doublets_instance.run()
    
    # Or just transform existing AI doublets file
    doublets_instance.process_transformed_data(book_name)