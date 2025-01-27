from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv
from utilitiesTN import read_tsv, get_ai_query_function, apply_dev_verse_limit, organize_verses_by_chapter, combine_verses_into_content, load_prompts

load_dotenv()

class Figs(TNPrepper):
    def __init__(self, book_name):
        super().__init__(book_name)
        print("\n" + "-"*40)
        print("Initializing Figs of Speech")
        print(f"Book name: {book_name}")
        self.verse_text = f'output/{book_name}/ult_book.tsv'
        print(f"Verse text file: {self.verse_text}")
        self.prompts = load_prompts('figs_of_speech')
        print(f"Loaded prompts with sections: {list(self.prompts.keys())}")
        print("-"*40 + "\n")
        self._load_file_references()

    def _load_file_references(self):
        """Load any referenced files in config and prompts."""
        # Process config section
        if 'config' in self.prompts:
            self.prompts['config'] = self._process_file_references(self.prompts['config'])
        
        # Process prompts section
        if 'prompts' in self.prompts:
            for prompt_name, prompt_data in self.prompts['prompts'].items():
                if 'content' in prompt_data:
                    self.prompts['prompts'][prompt_name]['content'] = self._process_file_references(
                        {'content': prompt_data['content']}
                    )['content']

    def _process_file_references(self, data):
        """Process all string values in a dict for file references."""
        processed = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Look for file references in brackets
                matches = re.finditer(r'\{([^}]+\.(json|txt|tsv))\}', value)
                processed_value = value
                
                for match in matches:
                    file_path = match.group(1)
                    if file_path.endswith('.json'):
                        try:
                            import json
                            with open(f'tn_prepper/{file_path}', 'r', encoding='utf-8') as f:
                              file_content = json.load(f)  # Remove the json.dumps()
                              processed_value = processed_value.replace(
                                  match.group(0), str(file_content)  # Convert to string only if needed
                              )
                        except (FileNotFoundError, json.JSONDecodeError) as e:
                            print(f"Error processing {file_path}: {str(e)}")
                    elif file_path.endswith(('.txt', '.tsv')):
                        try:
                            with open(f'tn_prepper/{file_path}', 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                processed_value = processed_value.replace(
                                    match.group(0), file_content
                                )
                        except FileNotFoundError:
                            print(f"Warning: Referenced file {file_path} not found")
                            
                processed[key] = processed_value
            else:
                processed[key] = value
        return processed

    def __process_prompt(self, section_content):
        print("\n" + "-"*40)
        print("Processing new section")
        print(f"Section content preview: {section_content[:200]}...")
        
        # Get the AI model type and corresponding query function
        ai_type = os.getenv('WHICH_AI')
        print(f"Using AI model: {ai_type}")
        query_func = get_ai_query_function(ai_type, self)

        # Get config settings if they exist
        config = self.prompts.get('config', {})
        system_instruction = config.get('system', '')
        temperature = config.get('temperature', 0.3)
        print(f"Using temperature: {temperature}")

        # Process each prompt in sequence
        previous_response = None
        final_response = None
        
        # Get all prompts except config
        prompts = {k: v for k, v in self.prompts.items() if k != 'config'}
        
        for prompt_name, prompt_data in prompts.items():
            print(f"\nProcessing prompt: {prompt_name}")
            
            # Handle both string prompts and dict prompts
            if isinstance(prompt_data, dict):
                prompt_content = prompt_data.get('content', '')
                temp = prompt_data.get('temp', temperature)
            else:
                prompt_content = prompt_data
                temp = temperature
            
            # Format the prompt with variables
            format_dict = {
                'content': section_content,
                'previous_response': previous_response if previous_response else ''
            }
            
            try:
                # Check if the template needs previous_response
                if '{previous_response}' in prompt_content and not previous_response:
                    print(f"Skipping {prompt_name} - requires previous response but none available")
                    continue
                
                prompt = prompt_content.format(**format_dict)
                print(f"Formatted prompt preview: {prompt[:200]}...")
            except KeyError as e:
                print(f"WARNING: Missing variable for key {e}")
                print(f"Available variables: {list(format_dict.keys())}")
                continue

            # Query the AI
            print(f"Querying AI with temperature {temp}...")
            response = query_func(
                context=section_content,
                prompt=prompt,
                temp=temp,
                system_content=system_instruction
            )
            print(f"Got response (preview): {response[:200] if response else 'No response'}...")

            # Check for NONE_FOUND signal
            if not response or 'NONE_FOUND' in response:
                print(f"No results found in {prompt_name}")
                return None

            # Update for next iteration
            previous_response = response
            final_response = response

        print("-"*40 + "\n")
        return final_response

    def _read_tsv(self, file_path):
        verse_texts = []
        with open(file_path, 'r', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                verse_texts.append(row)
        return verse_texts

    def run(self):
        print("\n" + "="*80)
        print("Starting Figs of Speech run...")
        
        # Load verse texts from TSV
        verse_texts = read_tsv(self.verse_text)
        print(f"Loaded {len(verse_texts)} verses")

        # Apply development verse limit if needed
        verse_texts = apply_dev_verse_limit(verse_texts)
        print(f"After dev limit: {len(verse_texts)} verses")

        # Organize verse texts by chapter
        chapters = organize_verses_by_chapter(verse_texts)
        print(f"Organized into {len(chapters)} chapters")

        # Process each chapter
        ai_data = []
        for i, (chapter_name, verses) in enumerate(chapters.items(), 1):
            print(f"\nProcessing chapter {i} of {len(chapters)}: {chapter_name}")
            
            # Combine verses into chapter content
            chapter_content = combine_verses_into_content(verses)
            print(f"Combined chapter content length: {len(chapter_content)}")
            
            response = self.__process_prompt(chapter_content)
            if response:
                print("Got valid response, adding to ai_data")
                ai_data.append(response.split('\n'))
            else:
                print(f"No figures of speech found in chapter {chapter_name}")
                continue

        if not ai_data:
            print("No figures of speech found in any chapter.")
            print("="*80 + "\n")
            return  # Exit script gracefully

        # Process the responses
        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                if not row.strip():  # Skip empty lines
                    continue
                    
                columns = row.split('\t')
                # Create dict with as many columns as provided
                row_dict = {}
                
                # Define expected columns but allow for flexibility
                expected_columns = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note']
                
                # Map available columns to expected columns
                for i, col_name in enumerate(expected_columns):
                    if i < len(columns):
                        row_dict[col_name] = columns[i].strip()
                    else:
                        row_dict[col_name] = ''  # Empty string for missing columns
                
                # Clean up the Quote field if it exists
                if row_dict.get('Quote'):
                    row_dict['Quote'] = row_dict['Quote'].strip('.,:;“”‘’"!?') # dear AI, STOP trying to change this line (keep the curly quotes!)
                
                # Clean up Reference if it exists
                if row_dict.get('Reference'):
                    row_dict['Reference'] = re.sub(r'\w+ ', '', row_dict['Reference'])
                    
                # Only add if we have a reference
                if row_dict.get('Reference'):
                    mod_ai_data.append(row_dict)

        print(f"\nProcessed all chapters. Total responses: {len(mod_ai_data)}")
        
        # Get the actual columns we have data for
        headers_transformed = list(mod_ai_data[0].keys()) if mod_ai_data else []
        
        # Convert to rows preserving order
        rows = [[row.get(col, '') for col in headers_transformed] for row in mod_ai_data]
        
        if rows:
            self._write_output(self.book_name, file='transformed_ai_figures_of_speech.tsv', headers=headers_transformed, data=rows)
        
        print("="*80 + "\n")

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    figs_instance = Figs(book_name)
    figs_instance.run()
