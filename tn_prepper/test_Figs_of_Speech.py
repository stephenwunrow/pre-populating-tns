from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv


class Figs(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
        prompt1 = (
            "You have been given a chapter from the Bible. I want you to look for each of the following specific figures of speech in the chapter: metaphor, simile, idiom, personification, metonymy, synecdoche, apostrophe, euphemism, hendiadys, litotes, merism, hyperbole. This list is roughly in order from most common to least common."
            "\n\nAs you are looking for each figure of speech, make sure that you carefully consider the definition of that figure of speech. Ensure that what you find for each figure of speech is not better classified as a different figure of speech."
            "\n\nFor each figure of speech you find, provide the following information in a tab-separated format:"
            "\n(1) The verse reference (e.g., 1 Kings 1:1)."
            "\n(2) The type of figure of speech."
            "\n(3) An exact quote from the verse that contains the figure of speech."
            "\n\nIf there are several figures of speech in one verse, include a separate set of data for each one."
        )

        response1 = self._query_openai(chapter_content, prompt1)

        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of some figures of speech from this chapter:\n{response1}\n\n"
            "I want you to double-check for each of the following specific figures of speech in the chapter: metaphor, simile, idiom, personification, metonymy, synecdoche, apostrophe, euphemism, hendiadys, litotes, merism, hyperbole.\n"
            "If you find more figures of speech, add them to the list.\n"
            "Also double-check the label provided for the figure of speech. Consider whether it is the best label for the text. Change it to another label if it is not the best label.\n"
            "As your answer, provide the new list."
        )

        response2 = self._query_openai(chapter_content, prompt2)

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of figures of speech in this chapter: {response2}\n\n"
            "\nFor each of these listed figures of speech, append a row of data to a TSV table. Each row must contain exactly eight tab-separated values. Here is what a row should be like:"
            "chapter:verse\t\t\trc://*/ta/man/translate/figs-[figure_of_speech]\thebrew_placeholder\t1\tExplanation of the figure of speech along with an alternate translation that does not use the figure of speech\tquote from the verse that the alternate translation can replace\n\n"
            "Here are two examples:\n"
            "1:2			rc://*/ta/man/translate/figs-metaphor	 hebrew_placeholder	1	Here the servants speak of how the young woman will always serve the king as if she would **stand to the face of the king**. If it would be helpful in your language, you could use a comparable figure of speech or state the meaning plainly. Alternate translation: “and she will always be ready to serve”\tand she will always stand to the face of the king\n"
            "1:37			rc://*/ta/man/translate/figs-metonymy   hebrew_placeholder  1	Here, **throne** represents the rule or reign of the person who sits on the **throne**. If it would be helpful in your language, you could use an equivalent expression from your language or state the meaning plainly. Alternate translation: “and may he make his reign greater than the reign of my lord the king David” or “and may he make him a greater ruler than my lord the king David”\tand may he make his throne greater than the throne of my lord the king David\n"
            "Note - whenever you quote directly from the verse, you should enclose the quoted word or words in double asterisks, as in the above examples."
        )

        return self._query_openai(chapter_content, prompt3)

    def _transform_response(self, mod_ai_data):
        if mod_ai_data:
            transformed_data = []
            for row in mod_ai_data:
                ref = row['Reference']
                if book_name in ref:
                    ref = re.sub(rf'{book_name} (.+)', r'\1', ref)
                function = row['Function']
                explanation = row['Explanation']
                mod_explanation = re.sub(r'.*(Here, this.+?\.).*', r'\1', explanation)
                snippet = row['Snippet'].strip('\'"*.,;!?“”’‘')
                alt_translation = row['Alternate Translation'].strip('\'".,;!?“”’‘*')

                if 'metaphor' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-metaphor'
                    mod_explanation = re.sub('Here, this figure of speech', 'This metaphor', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could state the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'simile' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-simile'
                    mod_explanation = re.sub('Here, this figure of speech', 'This simile', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could make this point explicitly. Alternate translation: “{alt_translation}”'

                if 'personification' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-personification'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could express the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'idiom' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-idiom'
                    mod_explanation = re.sub('Here, this figure of speech', 'This is an idiom. It', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If this phrase does not have that meaning in your language, you could use an idiom from your language that does have that meaning or state the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'metonymy' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-metonymy'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could state the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'synecdoche' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-synecdoche'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could use an equivalent expression from your culture or state the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'apostrophe' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-apostrophe'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you use the third person or express the idea in another way. Alternate translation: “{alt_translation}”'

                if 'euphemism' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-euphemism'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could use a polite way of referring to this in your language, or you could state this plainly. Alternate translation: “{alt_translation}”'

                if 'hyperbole' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-hyperbole'
                    mod_explanation = re.sub('Here, this figure of speech', 'Here, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could use a different way to express the emphasis. Alternate translation: “{alt_translation}”'

                if 'hendiadys' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-hendiadys'
                    mod_explanation = re.sub('Here, this figure of speech', 'In this figure of speech, the speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be more natural in your language, you could express this idea in a different way. Alternate translation: “{alt_translation}”'

                if 'merism' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-merism'
                    mod_explanation = re.sub('Here, this figure of speech', 'The speaker or writer', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could state the meaning plainly. Alternate translation: “{alt_translation}”'

                if 'litotes' in function.lower():
                    support_reference = 'rc://*/ta/man/translate/figs-litotes'
                    mod_explanation = re.sub('Here, this figure of speech', 'The speaker or writer is using a figure of speech here that', mod_explanation)
                    note_template = f'{mod_explanation.strip('\'".,;!?“”’‘')}. If it would be helpful in your language, you could express the positive meaning. Alternate translation: “{alt_translation}”'

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
                        'Function': columns[1],
                        'Explanation': columns[2],
                        'Snippet': columns[3],
                        'Alternate Translation': columns[4]
                    }
                    mod_ai_data.append(row_dict)

        # Write the results to a new TSV file
        headers = ['Reference', 'Function', 'Explanation', 'Snippet', 'Alternate Translation']
        file_name = 'ai_figures_of_speech.tsv'
        data = mod_ai_data
        self._write_fieldnames_to_tsv(book_name, file_name, data, headers)

        transformed_data = self._transform_response(mod_ai_data)

        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_figures_of_speech.tsv', headers=headers_transformed, data=transformed_data)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    figs_instance = Figs(book_name)
    figs_instance.run()
