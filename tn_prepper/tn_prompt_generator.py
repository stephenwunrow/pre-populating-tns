import os
import csv
from TNPrepper import TNPrepper
from utilitiesTN import read_tsv, get_ai_query_function, load_prompts, load_issue_descriptions
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

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
    
    def _group_by_issue(self, data):
        """Group entries by issue type and add line numbers as IDs."""
        groups = {}
        for i, entry in enumerate(data, 1):
            # Get issue type from SupportReference
            if 'SupportReference' in entry:
                issue_type = entry['SupportReference'].split('/')[-1]
                if issue_type not in groups:
                    groups[issue_type] = []
                    
                # Add line number as ID if not already present
                if 'ID' not in entry:
                    entry['ID'] = f"{entry['Reference']}_{i}"
                entry['original_line'] = i  # Track original position
                groups[issue_type].append(entry)
                
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

        # Filter entries that need AI processing (don't have $ or § in explanation)
        ai_needed_entries = []
        prewritten_notes = {}
        
        for entry in entries:
            entry_id = f"{entry['Reference']}_{len(prewritten_notes)}"
            explanation = entry.get('Explanation', '') or ''  # Convert None to empty string
            at_field = entry.get('AT', '') or ''  # Convert None to empty string
            
            if explanation and (explanation.startswith('$') or explanation.startswith('§')):
                # Store prewritten note
                is_literal = explanation.startswith('§')
                note = explanation[1:].strip()  # Remove the $ or § and any whitespace
                at = ''
                
                # Check if there's an alternate translation in the explanation
                if 'Alternate translation' in explanation:
                    parts = explanation.split('Alternate translation:', 1)
                    note = parts[0][1:].strip()  # Remove symbol and whitespace
                    at = parts[1].strip()
                elif at_field and (at_field.startswith('$') or at_field.startswith('§')):
                    # Use pre-written AT if it exists
                    at = at_field[1:].strip()
                
                # For literal notes (§), preserve exactly as written
                if is_literal:
                    # Don't modify the note content at all
                    pass
                else:
                    # For $ notes, still allow formatting cleanup
                    note = self._clean_response_formatting(note)
                    if at:
                        at = self._clean_response_formatting(at)
                
                prewritten_notes[entry_id] = {
                    'Reference': entry['Reference'],
                    'ID': entry_id,
                    'Tags': '',
                    'SupportReference': support_ref,
                    'GLQuote': entry.get('GLQuote', ''),
                    'Occurrence': '1',
                    'Note': note,
                    'OccurrenceNote': at
                }
            else:
                # Add to entries needing AI processing
                entry['ID'] = entry_id
                ai_needed_entries.append(entry)

        # If no entries need AI processing, return early
        if not ai_needed_entries:
            return "", prewritten_notes

        prompt = f"""You are a Bible translation expert. Given the following translation issue type and examples, generate translation notes.

Issue Type: {issue_type}
Support Reference: {support_ref}

Issue Description and Examples:
{description}

Translation Academy Content:
{ta_content}

Entries to process:
"""
        for entry in ai_needed_entries:
            ref = entry['Reference']
            verse_text = self.verse_data.get(f"{self.book_name} {ref}", "")
            prompt += f"\nID: {entry['ID']}"
            prompt += f"\nReference: {ref}"
            prompt += f"\nVerse: {verse_text}"
            prompt += f"\nQuoted Text: {entry['GLQuote']}"
            if 'Explanation' in entry and entry['Explanation']:
                prompt += f"\nContext: {entry['Explanation']}"
            if 'AT' in entry and entry['AT'] and not entry['AT'].startswith('$'):
                prompt += f"\nProvided Alternate Translation: {entry['AT']}"
            prompt += "\n"
            
        prompt += f"""\nGenerate translation notes for {issue_type} in this format:
ID\tReference\tNote\tAlternate Translation (if applicable)

Important formatting and content rules:
1. Do not include "Reference:" or "Note:" prefixes in your response
2. When quoting directly from the verse text, use markdown bold (**like this**)
3. For any other quotation marks, use curly/smart quotes ("like this")
4. Separate fields with tabs, one entry per line
5. Include the ID exactly as provided in the input
6. If a "Provided Alternate Translation" is given in the input:
   - Use that exact text as the Alternate Translation in your response
   - Use it as a guide to understand how the translation issue was resolved
   - Write your note to explain the conceptual path from the original text to this alternate translation
7. Your note should explain:
   - Why the original text might be difficult to understand
   - What the text means in its context
   - How the alternate translation helps readers understand the meaning\n"""
        
        return prompt, prewritten_notes
    
    def _clean_response_formatting(self, text):
        """Clean up response formatting to ensure consistent output."""
        if not text:
            return ""
            
        # First, fix any malformed markdown bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
        
        # Remove any "Reference:" or "Note:" prefixes
        text = text.replace("Reference:", "").replace("Note:", "")
        
        # Handle .replace('""', and ).replace('""', artifacts
        text = re.sub(r'\.replace\([\'"]""\', ?([^)]+)\)', r'\1', text)
        
        # Fix curly quotes, but not inside markdown bold
        parts = text.split('**')
        for i in range(0, len(parts), 2):  # Only process parts outside of bold
            # Replace straight quotes with curly quotes
            part = parts[i]
            # Handle opening quotes at start of string or after space/punctuation
            part = re.sub(r'(^|\s|[.!?])"', r'\1"', part)
            # Handle closing quotes before space/punctuation or end of string
            part = re.sub(r'"(\s|[.!?,]|$)', r'"\1', part)
            parts[i] = part
            
        text = '**'.join(parts)
        
        # Clean up any remaining straight quotes outside markdown
        text = re.sub(r'(?<!\*)"(?!\*)', '"', text)
        
        # Remove any double spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _generate_notes(self, issue_type, entries, ta_content):
        print(f"\nGenerating notes for {issue_type}")
        prompt, prewritten_notes = self._create_prompt(issue_type, entries, ta_content)
        print(f"Got {len(prewritten_notes)} prewritten notes")
        
        # Start with prewritten notes
        notes = list(prewritten_notes.values())
        print(f"Starting with {len(notes)} prewritten notes")
        
        if prompt:
            ai_query = get_ai_query_function(os.getenv('WHICH_AI', 'openai'), self)
            
            try:
                print(f"\nSending prompt to AI for {issue_type}:")
                response = ai_query(context="", prompt=prompt, temp=0.3)
                print("Got AI response:")
                print(response)
                print("-" * 80)
                
                # Parse the response into structured notes
                ai_generated_notes = []
                try:
                    for line in response.strip().split('\n'):
                        # Skip header line and empty lines
                        if not line.strip() or 'ID\tReference\tNote' in line:
                            continue
                            
                        # Split by tabs and clean up each part
                        parts = [part.strip() for part in line.split('\t')]
                        print(f"Processing line with {len(parts)} parts: {parts}")
                        
                        if len(parts) >= 3:  # We need at least ID, Reference, and Note
                            entry_id = parts[0]
                            ref = parts[1]
                            note = parts[2]
                            at = parts[3] if len(parts) > 3 else ''
                            
                            # Find the original entry to get GLQuote
                            original_entry = next((e for e in entries if e.get('ID') == entry_id), None)
                            if not original_entry:
                                original_entry = next((e for e in entries if e.get('Reference') == ref), None)
                            
                            gl_quote = original_entry.get('GLQuote', '') if original_entry else ''
                            
                            # Clean up formatting for note and AT
                            note = self._clean_response_formatting(note)
                            if at:
                                at = self._clean_response_formatting(at)
                            
                            note_dict = {
                                'Reference': ref,
                                'ID': entry_id,
                                'Tags': '',
                                'SupportReference': self.support_refs.get(self._map_issue_type(issue_type), ""),
                                'GLQuote': gl_quote,
                                'Occurrence': '1',
                                'Note': note,
                                'OccurrenceNote': at
                            }
                            print(f"Created note: {note_dict}")
                            ai_generated_notes.append(note_dict)
                except Exception as e:
                    print(f"Error processing response line: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                
                print(f"Generated {len(ai_generated_notes)} new notes from AI")
                notes.extend(ai_generated_notes)
                print(f"Total notes after adding AI-generated: {len(notes)}")
                
            except Exception as e:
                print(f"Error generating notes for {issue_type}: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        print(f"Returning {len(notes)} total notes for {issue_type}")
        return notes
    
    def process_file(self, input_file, output_file, batch_size=10):
        """Process the input file and generate notes."""
        # Read input data
        input_data = read_tsv(input_file)
        print(f"Read {len(input_data)} rows from input file")
        
        # Group entries by issue type
        issue_groups = self._group_by_issue(input_data)
        print(f"Grouped into {len(issue_groups)} issue types: {list(issue_groups.keys())}")
        
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
                print(f"Generated {len(notes)} notes for this batch")
                
                # Transfer original line numbers to generated notes
                for note in notes:
                    # Find matching original entry
                    original_entry = next((e for e in batch if e.get('ID') == note['ID']), None)
                    if original_entry:
                        note['original_line'] = original_entry.get('original_line', 0)
                    else:
                        print(f"Warning: Could not find original entry for note with ID {note['ID']}")
                
                all_notes.extend(notes)
                print(f"Total notes accumulated so far: {len(all_notes)}")
                
        print(f"\nFinal note count before sorting: {len(all_notes)}")
        
        # Sort notes by original line number
        all_notes.sort(key=lambda x: x.get('original_line', 0))
        print("Notes sorted by original line order")
        
        # Define the fieldnames in the correct order
        fieldnames = ['Reference', 'ID', 'Tags', 'SupportReference', 'GLQuote', 
                     'Occurrence', 'Note', 'OccurrenceNote']
        
        # Add timestamp and AI model to output filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        ai_model = os.getenv('WHICH_AI', 'unknown')
        base_name, ext = os.path.splitext(output_file)
        timestamped_output = f"{base_name}_{ai_model}_{timestamp}{ext}"
        
        # Write to output file
        with open(timestamped_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            # Remove original_line before writing
            for note in all_notes:
                note.pop('original_line', None)
            writer.writerows(all_notes)
            
        print(f"\nProcessed {len(all_notes)} notes total")
        print(f"Output written to: {timestamped_output}")

if __name__ == "__main__":
    generator = TNPromptGenerator("Obadiah")
    generator.process_file(
        # "output/Obadiah/OBA sample TN prompt.tsv",
        # "output/Obadiah/OBA_generated_notes.tsv",
        "output/1 Samuel/1SA sample TN prompt.tsv",
        "output/1 Samuel/1SA_generated_notes.tsv",
        batch_size=20
    ) 