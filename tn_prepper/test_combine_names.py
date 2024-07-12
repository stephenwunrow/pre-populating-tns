from TNPrepper import TNPrepper

import re
import os
from dotenv import load_dotenv

load_dotenv()

class Combine_Names(TNPrepper):

    def __init__(self, book_name):
        super().__init__()

        self.book_name = book_name

    def __join_and_search(self, ai_notes):
        # Join all lines into a single string
        combined_lines = '\n'.join(['\t'.join(item.values()) for item in ai_notes])

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe word)([^\n]+?)(is the name of a )(\w+)([^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe word([^\n]+) is the name of a \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 & \11\4\tThe words\6and\12 are the names of \8s\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe words)([^\n]+?)(are the names of )(\w+)(s[^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe word([^\n]+) is the name of a \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 \& \11\4\5\6and\12 \7\8\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        search_pattern = r'(?s)(\d+:\d+)([^\n]+?names\t)([^\n]+)(\t\d)(\tThe words)([^\n]+?)(are the names of )(\w+)([^\n]+)(.*?)\n\1\t[^\n]+names\t([^\n]+)\t\d\tThe words([^\n]+) are the names of \8\.\t([^\n]+)'
        replace_with = r'\1\2\3 \& \11\4\5\6and\12 \7\8\9…\13\10'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        combined_lines = re.sub(r' mans', r' men', combined_lines)
        combined_lines = re.sub(r' womans', r' women', combined_lines)
        combined_lines = re.sub(r'(The words \*\*\w+\*\*)( and)( \*\*\w+\*\*)( and \*\*\w+\*\*)', r'\1,\3,\4', combined_lines)

        search_pattern = r'(\*\*\w+\*\*, \*\*\w+\*\*, )(and )(\*\*\w+\*\*)( and \*\*\w+\*\*)'
        replace_with = r'\1\3,\4'

        while True:
            new_text = re.sub(search_pattern, replace_with, combined_lines)
            if new_text == combined_lines:
                break
            combined_lines = new_text

        return combined_lines
    
    def _write_tsv(self, file_path, data):
        with open(file_path, 'w') as file:
            file.write(data)
        print(f'Data written to {file_path}')

    def run(self):

        file_path = f'output/{book_name}/ai_notes.tsv'
        ai_notes = self._read_tsv(file_path)

        combined_lines = self.__join_and_search(ai_notes)
        
        output_file_path = f'output/{book_name}/combined_names.tsv'
        self._write_tsv(output_file_path, combined_lines)

# Example usage:
if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    # Ensure the directory exists
    os.makedirs(f'output/{book_name}', exist_ok=True)

    combine_instance = Combine_Names(book_name)
    combine_instance.run()