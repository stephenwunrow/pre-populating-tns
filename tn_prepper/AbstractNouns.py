from .TNPrepper import TNPrepper
import requests
import re


class AbstractNouns(TNPrepper):
    def __init__(self):
        super().__init__()

    # Function to fetch data from a given URL
    def fetch_data(self, url):
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text

    # Function to process data and extract relevant information based on a regex pattern
    def process_data(self, data, pattern, book_name):
        result = []
        rows = data.splitlines()
        for row in rows:
            match = re.search(pattern, row)
            if match:
                reference, words = match.groups()
                # Include the book name in the reference
                full_reference = f"{book_name} {reference}"
                # Split words by word joiner (U+2060), Hebrew punctuation Maqaf (U+05BE), and any whitespace
                words_list = re.split(r'[\u05BE\s]+', words)
                for word in words_list:
                    if '&' in word:
                        break
                    elif word:  # Ensure no empty strings are added
                        result.append([full_reference, word])
        return result

    def run(self):

        # Base URL with placeholder for the acronym
        base_url = "https://git.door43.org/unfoldingWord/en_tn/raw/branch/master/tn_{}.tsv"

        # Regex pattern to match the desired format
        pattern = re.compile(r'(\d+:\d+)\t.+?\t.*?\trc://\*/ta/man/translate/figs-abstractnouns\t(.+?)\t')

        # Main script
        all_results = []

        # List of three-letter acronyms to replace "JON" in the URL
        acronyms = ["EXO", "EZR", "JOB", "JON", "NEH", "RUT"]  # Add more acronyms as needed

        for acronym in acronyms:
            url = base_url.format(acronym)
            try:
                data = self.fetch_data(url)
                results = self.process_data(data, pattern, acronym)
                all_results.extend(results)
            except requests.HTTPError as e:
                print(f"Failed to fetch data from {url}: {e}")

            # Write results to a TSV file
            headers = ["Reference", "Word"]
            self._write_output(book_name=acronym, file='abstract_nouns', headers=headers, data=all_results)
