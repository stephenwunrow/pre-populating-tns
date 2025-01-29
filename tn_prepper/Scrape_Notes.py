from TNPrepper import TNPrepper
from Final_Snippets import Final_Snippets
import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

class Scrape_Notes(TNPrepper):
    def __init__(self, book_name):
        super().__init__()
        self.book_name = book_name
        print(f"\nInitializing Scrape_Notes for {book_name}")
        
        # Get version from environment
        self.version = os.getenv("VERSION")
        if not self.version:
            raise ValueError("VERSION not set in environment")
        
        # Mapping of book names to their 3-letter codes with numbers
        self.book_codes = {
            "Genesis": "01-GEN", "Exodus": "02-EXO", "Leviticus": "03-LEV",
            "Numbers": "04-NUM", "Deuteronomy": "05-DEU", "Joshua": "06-JOS",
            "Judges": "07-JDG", "Ruth": "08-RUT", "1 Samuel": "09-1SA",
            "2 Samuel": "10-2SA", "1 Kings": "11-1KI", "2 Kings": "12-2KI",
            "1 Chronicles": "13-1CH", "2 Chronicles": "14-2CH", "Ezra": "15-EZR",
            "Nehemiah": "16-NEH", "Esther": "17-EST", "Job": "18-JOB",
            "Psalms": "19-PSA", "Proverbs": "20-PRO", "Ecclesiastes": "21-ECC",
            "Song of Solomon": "22-SNG", "Isaiah": "23-ISA", "Jeremiah": "24-JER",
            "Lamentations": "25-LAM", "Ezekiel": "26-EZK", "Daniel": "27-DAN",
            "Hosea": "28-HOS", "Joel": "29-JOL", "Amos": "30-AMO",
            "Obadiah": "31-OBA", "Jonah": "32-JON", "Micah": "33-MIC",
            "Nahum": "34-NAM", "Habakkuk": "35-HAB", "Zephaniah": "36-ZEP",
            "Haggai": "37-HAG", "Zechariah": "38-ZEC", "Malachi": "39-MAL"
        }
        
        self.book_code = self.book_codes.get(book_name)
        if not self.book_code:
            raise ValueError(f"Unknown book name: {book_name}")
            
        # Initialize Final_Snippets for alignment data
        # Create a dummy input file path that Final_Snippets expects
        input_file = f'output/{book_name}/ai_notes.tsv'
        self.snippets = Final_Snippets(book_name, self.version, self.book_code, input_file)
            
    def _get_alignment_data(self):
        """Get Hebrew-English alignment data using Final_Snippets methods"""
        # Step 1: Get Hebrew text
        print("\nStep 1: Getting Hebrew text...")
        combined_text = self.snippets._get_hbo(self.book_name, self.book_code)
        print(f"Combined text length: {len(combined_text) if combined_text else 0}")
        if combined_text:
            print("First 200 chars:", combined_text[:200])
        else:
            print("WARNING: No Hebrew text found!")
            
        # Step 2: Find unique numbers
        print("\nStep 2: Finding unique numbers...")
        unique_numbers = self.snippets._find_unique_numbers(combined_text)
        print(f"Found {len(unique_numbers)} unique numbers")
        if unique_numbers:
            print("First 3 entries:")
            for num in unique_numbers[:3]:
                print(f"  Reference: {num[0]}, Hebrew: {num[1]}, Number: {num[2]}, Occurrence: {num[3]}")
        else:
            print("WARNING: No unique numbers found!")
            
        # Step 3: Get ULT dictionary
        print("\nStep 3: Getting ULT dictionary...")
        ult_dict = self.snippets._construct_ult_dict(self.version, self.book_code, unique_numbers)
        print(f"ULT dictionary has {len(ult_dict)} entries")
        if ult_dict:
            print("First 3 entries:")
            for entry in ult_dict[:3]:
                print(f"  Verse: {entry[0]}, Hebrew: {entry[1]}, Number: {entry[2]}, English: {entry[3]}, Chunk: {entry[4]}")
        else:
            print("WARNING: ULT dictionary is empty!")
            
        return ult_dict
            
    def _fetch_tn_data(self):
        """Fetch translation notes data from Door43"""
        # Use the book code without numbers for the URL
        url = f"https://git.door43.org/unfoldingWord/en_tn/raw/branch/master/tn_{self.book_code[3:]}.tsv"
        print(f"Fetching data from: {url}")
        
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code}")
            
        return response.text
        
    def _parse_tn_data(self, content, ult_dict):
        """Parse the TSV content and extract required fields, using ult_dict for alignments"""
        parsed_data = []
        
        # Read TSV content
        reader = csv.reader(content.splitlines(), delimiter='\t')
        next_row = next(reader)  # Skip header row
        
        # First, organize ULT dict by verse and chunk for easier lookup
        verse_dict = {}
        for entry in ult_dict:
            verse_ref = entry[0]
            hebrew = entry[1]
            english = entry[3]
            chunk = entry[4]
            
            if verse_ref not in verse_dict:
                verse_dict[verse_ref] = {}
            if chunk not in verse_dict[verse_ref]:
                verse_dict[verse_ref][chunk] = {}
            if hebrew not in verse_dict[verse_ref][chunk]:
                verse_dict[verse_ref][chunk][hebrew] = set()  # Use set to avoid duplicates
            verse_dict[verse_ref][chunk][hebrew].add(english)
        
        for row in reader:
            if len(row) < 7:  # Skip rows that don't have all required columns
                continue
                
            reference = row[0]
            support_ref = row[3]
            quote = row[4]  # This is Hebrew text
            occurrence = row[5]
            note = row[6]  # Get the note which contains the English translation
            
            # Only process rows with occurrence = 1
            if occurrence != "1":
                continue
                
            if reference != '1:1': # ADDED: Skip rows that are not 1:1
                continue
                
            # Extract issue type from support reference - everything after translate/
            issue_match = re.search(r'translate/([^/\]]+)', support_ref)
            if not issue_match:
                continue
                
            issue_type = issue_match.group(1)
            
            # Clean up reference (remove book name if present)
            if ' ' in reference:
                reference = reference.split(' ')[-1]
            
            # Try to extract English translation from the note
            english_quote = quote  # Default to Hebrew if no English found
            
            # Look for text between double asterisks in the note
            quoted_text = re.findall(r'\*\*([^*]+)\*\*', note)
            if quoted_text:
                # Remove duplicates while maintaining order
                seen = set()
                unique_quotes = []
                for q in quoted_text:
                    q = q.strip()
                    if q.lower() not in seen:
                        seen.add(q.lower())
                        unique_quotes.append(q)
                english_quote = ' '.join(unique_quotes)
                print(f"Found English quote in note: {english_quote}")
            
            # If we didn't find English in the note, try the ULT alignments
            if english_quote == quote and reference in verse_dict:
                print(f"\nTrying ULT alignments for {quote}...")
                hebrew_words = quote.split()
                chunk_parts = {}  # Store English parts by chunk number
                
                # Try to find each Hebrew word in each chunk
                for hebrew_word in hebrew_words:
                    found = False
                    for chunk_num in sorted(verse_dict[reference].keys()):
                        chunk_dict = verse_dict[reference][chunk_num]
                        if hebrew_word in chunk_dict:
                            # Get all English parts for this Hebrew word in this chunk
                            english_parts = verse_dict[reference][chunk_num][hebrew_word]
                            if chunk_num not in chunk_parts:
                                chunk_parts[chunk_num] = []
                            chunk_parts[chunk_num].extend(english_parts)
                            found = True
                            break
                
                # Combine English parts in chunk order
                english_parts = []
                for chunk_num in sorted(chunk_parts.keys()):
                    chunk_english = ' '.join(sorted(set(chunk_parts[chunk_num])))  # Remove duplicates within chunk
                    english_parts.append(chunk_english)
                
                if english_parts:
                    english_quote = ' '.join(english_parts)
                    print(f"Built English quote: {english_quote}")
            
            parsed_data.append([reference, issue_type, english_quote])
            
        return parsed_data
        
    def run(self):
        print("\n" + "="*80)
        print(f"Starting Scrape_Notes for {self.book_name}")
        
        # Get alignment data
        print("Getting alignment data...")
        ult_dict = self._get_alignment_data()
        
        # Fetch translation notes
        print("Fetching translation notes...")
        content = self._fetch_tn_data()
        
        # Parse data with alignments
        parsed_data = self._parse_tn_data(content, ult_dict)
        
        # Write output
        headers = ['Reference', 'Issue Type', 'Quote']
        output_file = f'scraped_notes.tsv'
        self._write_output(self.book_name, output_file, headers, parsed_data)
        
        print(f"Processed {len(parsed_data)} notes")
        print("="*80 + "\n")

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    scraper = Scrape_Notes(book_name)
    scraper.run() 