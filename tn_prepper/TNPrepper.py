import os
import csv

class TNPrepper():
    def __init__(self):
        self.output_base_dir = 'output'
        pass

    def __setup_output(self, book_name, file):
        # Construct the output path
        output_path = f'output/{book_name}'

        # Ensure the directory exists
        os.makedirs(output_path, exist_ok=True)

        # Path to the file you want to write
        return f'{output_path}/{file}.tsv'


    def _write_output(self, book_name, file, headers, data):
        output_file = self.__setup_output(book_name, file)

        # Write results to a TSV file
        #output_file = self.output_base_dir + '/' + book + "/abstract_nouns.tsv"

        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(headers)  # Column headers
            writer.writerows(data)

        print(f"Data has been written to {output_file}")