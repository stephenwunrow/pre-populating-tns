import os
import csv
from TNPrepper import TNPrepper
from utilitiesTN import read_tsv, get_ai_query_function, load_prompts, load_issue_descriptions
from collections import defaultdict
import requests
from bs4 import BeautifulSoup

class TNPromptGenerator(TNPrepper):
    def __init__(self, book_name=None):
        super().__init__(book_name)
        self.support_refs = self._load_support_references()
        self.issue_descriptions = load_issue_descriptions()
        # Load verse data
        self.verse_data = self._load_verse_data()
        
    def _load_verse_data(self):
        """Load the verse data from the ULT TSV file."""
        verse_data = {}
        try:
            verses = read_tsv(f'output/{self.book_name}/ult_book.tsv')
            for verse in verses:
                if verse['Reference'] != '-':
                    verse_data[verse['Reference']] = verse['Verse']
            return verse_data
        except Exception as e:
            print(f"Error loading verse data: {str(e)}")
            return {}
    
    def _load_support_references(self):
        refs = {}
        with open('tn_prepper/data/support_references.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    key = line.split('/')[-1]  # Extract the last part of the path
                    refs[key] = line
        return refs
    
    def _map_issue_type(self, issue_type):
        """Map issue types to their corresponding TA article paths."""
        # Load the issue map from the CSV file
        issue_map = {}
        with open('tn_prepper/data/ta articles short to long.csv', 'r', encoding='utf-8') as f:
            for line in f:
                key, value = line.strip().split(':')
                issue_map[key.strip().strip("'")] = value.strip().strip("'")

        return issue_map.get(issue_type, issue_type)

    def _get_ta_content(self, issue_type):
        # Map the issue type to its TA path
        ta_path = self._map_issue_type(issue_type)
        base_url = "https://git.door43.org/unfoldingWord/en_ta/raw/branch/master/translate/"
        url = f"{base_url}{ta_path}/01.md"
            
        print(f"Fetching TA content from: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        print(f"Failed to fetch TA content: {response.status_code}")
        return ""
    
    def _group_by_issue(self, input_data):
        groups = defaultdict(list)
        for entry in input_data:
            if 'SupportReference' in entry:
                ref = entry['SupportReference'].split('/')[-1]
                groups[ref].append(entry)
        return groups
    
    def _create_prompt(self, issue_type, entries, ta_content):
        # Get the mapped issue type for looking up support reference
        ta_path = self._map_issue_type(issue_type)
        support_ref = self.support_refs.get(ta_path, "")
        
        # Get the full description with examples for this issue type
        description = self.issue_descriptions.get(ta_path, "")
        if not description:
            print(f"Warning: No description found for issue type {issue_type} (mapped to {ta_path})")
            description = "No description available"

        prompt = f"""You are a Bible translation expert. Given the following translation issue type and examples, generate translation notes.

Issue Type: {issue_type}
Support Reference: {support_ref}

Issue Description and Examples:
{description}

Translation Academy Content:
{ta_content}

Entries to process:
"""
        for entry in entries:
            ref = entry['Reference']
            verse_text = self.verse_data.get(f"{self.book_name} {ref}", "")
            prompt += f"\nReference: {ref}"
            prompt += f"\nVerse: {verse_text}"
            prompt += f"\nQuoted Text: {entry['GLQuote']}"
            if 'Explanation' in entry:
                prompt += f"\nContext: {entry['Explanation']}"
            prompt += "\n"
            
        prompt += f"\nGenerate translation notes for {issue_type} in this format:\n"
        prompt += "Reference\tIssue Type\tNote\tAlternate Translation (if applicable)\n"
        
        return prompt
    
    def _generate_notes(self, issue_type, entries, ta_content):
        prompt = self._create_prompt(issue_type, entries, ta_content)
        
        # Get the appropriate AI query function from utilitiesTN
        ai_query = get_ai_query_function(os.getenv('WHICH_AI', 'openai'), self)
        
        try:
            print(f"\nSending prompt to AI for {issue_type}:")
            # Pass an empty context since we're including all necessary context in the prompt
            response = ai_query(context="", prompt=prompt, temp=0.3)
            print(response)
            print("-" * 80)
            
            # Parse the response into structured notes
            notes = []
            for line in response.strip().split('\n'):
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 3:  # Ensure we have at least reference, issue type, and note
                        ref, issue, note = parts[:3]
                        at = parts[3] if len(parts) > 3 else ''  # Get AT if available
                        notes.append({
                            'Reference': ref.strip(),
                            'Tags': '',  # Add empty Tags field
                            'SupportReference': self.support_refs.get(self._map_issue_type(issue_type), ""),
                            'GLQuote': '',  # Add empty GLQuote field
                            'Occurrence': '1',  # Add default Occurrence
                            'Note': note.strip(),
                            'OccurrenceNote': at.strip() if at else ''  # Use OccurrenceNote for alternate translations
                        })
            return notes
        except Exception as e:
            print(f"Error generating notes for {issue_type}: {str(e)}")
            return []
    
    def process_file(self, input_file, output_file, batch_size=10):
        """Process the input file and generate notes."""
        # Read input data
        input_data = read_tsv(input_file)
        
        # Group entries by issue type
        issue_groups = self._group_by_issue(input_data)
        
        all_notes = []
        for issue_type, entries in issue_groups.items():
            print(f"\nProcessing issue type: {issue_type}")
            print(f"Found {len(entries)} entries")
            
            # Get TA content for this issue type
            ta_content = self._get_ta_content(issue_type)
            
            # Process in batches
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i + batch_size]
                print(f"\nProcessing batch {i//batch_size + 1} ({len(batch)} entries)")
                
                notes = self._generate_notes(issue_type, batch, ta_content)
                all_notes.extend(notes)
                
        # Define the fieldnames in the correct order
        fieldnames = ['Reference', 'ID', 'Tags', 'SupportReference', 'GLQuote', 
                     'Occurrence', 'Note', 'OccurrenceNote']
        
        # Write to output file
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(all_notes)
            
        print(f"\nProcessed {len(all_notes)} notes total")
        print(f"Output written to: {output_file}")

if __name__ == "__main__":
    generator = TNPromptGenerator("Obadiah")
    generator.process_file(
        "output/Obadiah/OBA sample TN prompt.tsv",
        "output/Obadiah/OBA_generated_notes.tsv",
        batch_size=20
    ) 