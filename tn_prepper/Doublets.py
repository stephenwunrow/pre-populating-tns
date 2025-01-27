from TNPrepper import TNPrepper
import os
import csv
import re
from dotenv import load_dotenv
from utilitiesTN import read_tsv, get_ai_query_function, apply_dev_verse_limit, organize_verses_by_section, combine_verses_into_content, load_prompts

load_dotenv()

class Doublets(TNPrepper):
    def __init__(self, book_name):
        super().__init__(book_name)
        print("\n" + "-"*40)
        print("Initializing Doublets")
        print(f"Book name: {book_name}")
        self.verse_text = f'output/{book_name}/ult_book.tsv'
        print(f"Verse text file: {self.verse_text}")
        self.prompts = load_prompts('doublets')
        print(f"Loaded prompts with sections: {list(self.prompts.keys())}")
        print("-"*40 + "\n")

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

    def run(self):
        print("\n" + "="*80)
        print("Starting Doublets run...")
        
        # Load verse texts from TSV
        verse_texts = read_tsv(self.verse_text)
        print(f"Loaded {len(verse_texts)} verses")

        # Apply development verse limit if needed
        verse_texts = apply_dev_verse_limit(verse_texts)
        print(f"After dev limit: {len(verse_texts)} verses")

        # Organize verse texts by sections
        sections = organize_verses_by_section(verse_texts)
        print(f"Organized into {len(sections)} sections")

        # Process each section for doublets
        ai_data = []
        for i, section in enumerate(sections, 1):
            print(f"\nProcessing section {i} of {len(sections)}")
            # Combine verses into section context
            section_content = combine_verses_into_content(section)
            print(f"Combined section content length: {len(section_content)}")
            
            response = self.__process_prompt(section_content)
            if response:
                print("Got valid response, adding to ai_data")
                ai_data.append(response.split('\n'))
            else:
                print(f"No doublets found in section starting with verse {section[0]['Reference']}")
                continue

        if not ai_data:
            print("No doublets found in any section.")
            print("="*80 + "\n")
            return  # Exit script gracefully

        # Process the responses - now more flexible with column handling
        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                if not row.strip():  # Skip empty lines
                    continue
                    
                columns = row.split('\t')
                # Create dict with as many columns as provided
                row_dict = {}
                
                # Define expected columns but allow for flexibility
                expected_columns = ['Reference', 'Explanation', 'Snippet', 'Alternate Translation']
                
                # Map available columns to expected columns
                for i, col_name in enumerate(expected_columns):
                    if i < len(columns):
                        row_dict[col_name] = columns[i].strip()
                    else:
                        row_dict[col_name] = ''  # Empty string for missing columns
                
                if row_dict['Reference']:  # Only add if we at least have a reference
                    mod_ai_data.append(row_dict)

        print(f"\nProcessed all sections. Total responses: {len(mod_ai_data)}")
        
        # Get the actual columns we have data for
        headers_transformed = list(mod_ai_data[0].keys()) if mod_ai_data else []
        
        # Convert to rows preserving order
        rows = [[row.get(col, '') for col in headers_transformed] for row in mod_ai_data]
        
        if rows:
            self._write_output(self.book_name, file='transformed_ai_doublets.tsv', headers=headers_transformed, data=rows)
        
        print("="*80 + "\n")

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    doublets_instance = Doublets(book_name)
    doublets_instance.run()