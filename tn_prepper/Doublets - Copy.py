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
            "A doublet is two words or very short phrases that have the same meaning and that are joined directly by 'and'. This type of repetition emphasizes the meaning. Be sure that the words or phrases you identify are not full clauses.\n"
            "In the chapter of the Bible provided above, identify each doublet. If there are no doublets, return 'None'."
        )

        # response1 = self._query_openai(chapter_content, prompt1)
        # response1 = self._query_gemini(chapter_content, prompt1)
        response1 = self._query_claude(chapter_content, prompt1)

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of potential doublets in this chapter:\n{response1}\n\n"
            "Examine this list in context. If the two words or phrases do not have the same meaning, remove the line from the list. If the two words or phrases are not joined directly by 'and', remove the line from the list. Return the revised list. If the revised list is empty, return 'None'."
        )
        if response1 and len(response1) > 0:
            # response2 = self._query_openai(chapter_content, prompt2)
            # response2 = self._query_gemini(chapter_content, prompt2)
            response2 = self._query_claude(chapter_content, prompt2)
        else:
            return None  # Returning null as instructed

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of doublets from that chapter:\n{response2}\n\n"
            "If the list is empty, return 'None'. Otherwise, for each doublet, you will append a row of data to a TSV table. Each row should contain exactly four tab-separated values:"
            "\n(1) The first tab-separated value will provide the chapter and verse where the doublet is found. Do not include the book name."
            "\n(2) The second tab-separated value will provide an explanation of the doublet. The explanation must be in this form: 'The terms **[word/phrase 1]** and **[word/phrase 2]** mean similar things. [Speaker/Writer] is using the two terms together for emphasis.' Use these exact sentences, including the asterisks, except you should replace the bracketed words with the appropriate data from the verse."
            "\n(3) The third tab-separated value will provide an exact quote from the verse. This quote will be the section of the verse that would need to be rephrased to express the idea without the doublet."
            "\n(4) The fourth tab-separated value will provide a way to express the quote from the third value without using both words or phrases. This alternate expression should be able to replace the quote in the verse context without losing any meaning."
            "\nBe sure that the items in each row are consistent in how they understand the doublet.\n"
        )
        if response2 and len(response2) > 0:
            # return self._query_openai(chapter_content, prompt3)
            # return self._query_gemini(chapter_content, prompt3)
            return self._query_claude(chapter_content, prompt3)
        else:
            return None  # Returning null as instructed
        
    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                ref = re.sub(r'.+ (\d+:\d+)', r'\1', ref)
                explanation = row['Explanation'].strip('\'".,;!?“”’‘')
                snippet = row['Snippet'].strip('\'".,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘')
                alt_translation = re.sub(r'\*', '', alt_translation)
                note_template = f'{explanation}. If it would be clearer for your readers, you could express the emphasis with a single phrase. Alternate translation: [{alt_translation}]'
                support_reference = 'rc://*/ta/man/translate/figs-doublet'
                
                transformed_row = [
                ref,  # Reference
                'uw43',   # ID: random, unique four-letter and number combination - uw43 for now, Rich's script will change this
                '',   # Tags: blank
                support_reference,  # SupportReference: standard link
                snippet,  # Quote: lexeme. We can put English here, Rich's script will change this
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

    def _organize_verses_by_section(self, verse_texts):
        sections = []
        current_section = []
        
        # Handle first verse
        if verse_texts and verse_texts[0]['Verse'] != '-':
            current_section.append(verse_texts[0])
        
        # Process remaining verses
        for verse in verse_texts[1:]:
            if verse['Verse'] == '-':
                if current_section:  # Only append if section has verses
                    sections.append(current_section)
                current_section = []
            else:
                current_section.append(verse)
        
        # Add the last section if it exists
        if current_section:
            sections.append(current_section)
            
        return sections

    def run(self):
        # Load verse texts from TSV
        verse_texts = self._read_tsv(self.verse_text)

        # Check the stage and limit verse_texts if in development stage
        if os.getenv('STAGE') == 'dev':
            verse_texts = verse_texts[:5]

        # Organize verse texts by sections
        sections = self._organize_verses_by_section(verse_texts)

        # Process each section for doublets
        ai_data = []
        for section in sections:
            # Combine verses into section context
            section_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in section])
            response = self.__process_prompt(section_content)
            if response:
                ai_data.append(response.split('\n'))
            else:
                print(f"No doublets found in section starting with verse {section[0]['Reference']}")
                continue  # Continue to next section instead of exiting
        
        if not ai_data:
            print("No doublets found in any section.")
            return  # Exit script gracefully

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
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note']
        self._write_output(book_name, file='transformed_ai_doublets.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    doublets_instance = Doublets(book_name)
    doublets_instance.run()
