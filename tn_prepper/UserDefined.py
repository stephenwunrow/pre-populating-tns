from TNPrepper import TNPrepper
import os
from dotenv import load_dotenv
from utilitiesTN import (
    read_tsv, get_ai_query_function, apply_dev_verse_limit, 
    organize_verses_by_section, combine_verses_into_content, 
    load_prompts, process_prompt_references
)
import re
import yaml

load_dotenv()

class UserDefined(TNPrepper):
    def __init__(self, book_name):
        super().__init__(book_name)
        print("\n" + "-"*40)
        print("Initializing UserDefined")
        print(f"Book name: {book_name}")
        self.verse_text = f'output/{book_name}/ult_book.tsv'
        print(f"Verse text file: {self.verse_text}")
        self.prompts = load_prompts('user_defined')
        print(f"Loaded prompts with sections: {list(self.prompts.keys())}")
        self.prompts = process_prompt_references(self.prompts)
        print("-"*40 + "\n")

    def __process_prompt(self, section_content):
        print("\n" + "-"*40)
        print("Processing new section")
        print(f"Section content preview: {section_content[:200]}...")
        
        # Get the AI model type and corresponding query function
        ai_type = os.getenv('WHICH_AI')
        print(f"Using AI model: {ai_type}")
        query_func = get_ai_query_function(ai_type, self)

        # Get config settings
        system_instruction = self.prompts.get('config', {}).get('system', '')
        temperature = self.prompts.get('config', {}).get('temperature', 0.4)
        print(f"Using temperature: {temperature}")

        # Process each prompt in sequence
        previous_response = None
        for prompt_name, prompt_data in self.prompts.get('prompts', {}).items():
            if prompt_name == 'config':
                continue

            print(f"\nProcessing prompt: {prompt_name}")
            prompt_content = prompt_data.get('content', '')
            print(f"Previous response exists: {previous_response is not None}")
            if previous_response:
                print(f"Previous response preview: {previous_response[:200]}...")
            
            # Format the prompt with variables
            format_dict = {
                'content': section_content,
                'previous_response': previous_response if previous_response else ''
            }
            print(f"Format dict keys: {list(format_dict.keys())}")
            print(f"Format dict values preview:")
            for k, v in format_dict.items():
                print(f"  {k}: {str(v)[:100] if v else 'empty'}...")
            
            try:
                # Check if the template actually needs previous_response
                if '{previous_response}' in prompt_content and not previous_response:
                    print("WARNING: Template requires previous_response but none available")
                    if prompt_name != 'initial_analysis':  # Skip non-initial prompts if no previous response
                        print(f"Skipping {prompt_name} due to missing previous response")
                        continue
                
                prompt = prompt_content.format(**format_dict)
                print(f"Formatted prompt preview: {prompt[:200]}...")
            except KeyError as e:
                print(f"WARNING: Missing variable for key {e}")
                print(f"Available variables: {list(format_dict.keys())}")
                pattern = r'\{([^}]+)\}'
                refs = re.findall(pattern, prompt_content)
                print(f"Template contains references: {refs}")
                if str(e) == "'previous_response'" and not previous_response:
                    print(f"Skipping {prompt_name} due to missing previous response")
                    continue
                prompt = prompt_content

            # Query the AI
            print("Querying AI...")
            response = query_func(
                context=section_content,
                prompt=prompt,
                temp=temperature,
                system_content=system_instruction
            )
            print(f"Got response (preview): {response[:200] if response else 'No response'}...")

            # Check for NONE_FOUND signal
            if response and 'NONE_FOUND' in response:
                print("NONE_FOUND in response, returning None")
                print("-"*40 + "\n")
                return None

            # Update previous response for next iteration
            previous_response = response
            print(f"Updated previous_response for next iteration (preview): {previous_response[:100] if previous_response else 'None'}...")

        print("-"*40 + "\n")
        return previous_response

    def run(self):
        print("\n" + "="*80)
        print("Starting UserDefined run...")
        
        # Load verse texts from TSV
        verse_texts = read_tsv(self.verse_text)
        print(f"Loaded {len(verse_texts)} verses")

        # Apply development verse limit if needed
        verse_texts = apply_dev_verse_limit(verse_texts)
        print(f"After dev limit: {len(verse_texts)} verses")

        # Organize verse texts by section
        sections = organize_verses_by_section(verse_texts)
        print(f"Organized into {len(sections)} sections")

        # Process each section
        ai_data = []
        
        for i, section in enumerate(sections, 1):
            print(f"\nProcessing section {i} of {len(sections)}")
            # Skip empty sections
            if not section:
                print("Skipping empty section")
                continue
                
            # Combine verses into section content
            section_content = combine_verses_into_content(section)
            print(f"Combined section content length: {len(section_content)}")
            
            response = self.__process_prompt(section_content)
            if response:
                print("Got valid response, adding to ai_data")
                ai_data.append(response.split('\n'))
            else:
                print("No valid response for this section")

        print(f"\nProcessed all sections. Total responses: {len(ai_data)}")
        print("="*80 + "\n")

        # Process the responses
        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                columns = row.split('\t')
                
                row_dict = {
                    'Reference': columns[0] if len(columns) > 0 else None,
                    'ID': columns[1] if len(columns) > 1 else None,
                    'Tags': columns[2] if len(columns) > 2 else None,
                    'SupportReference': columns[3] if len(columns) > 3 else None,
                    'Quote': columns[4] if len(columns) > 4 else None,
                    'Occurrence': columns[5] if len(columns) > 5 else None,
                    'Note': columns[6] if len(columns) > 6 else None
                }
                if row_dict['Quote']:
                    row_dict['Quote'] = row_dict['Quote'].strip('.,:;“”‘’"!?') # AI don't change the curly quotes!
                if row_dict['Reference']:
                    row_dict['Reference'] = re.sub(r'\w+ ', '', row_dict['Reference'])
                    mod_ai_data.append(row_dict)

        rows = [[row.get('Reference'), row.get('ID'), row.get('Tags'), row.get('SupportReference'), 
                row.get('Quote'), row.get('Occurrence'), row.get('Note')] for row in mod_ai_data]
        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note']
        self._write_output(self.book_name, file='transformed_ai_user_defined.tsv', headers=headers_transformed, data=rows)

if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")
    user_defined = UserDefined(book_name)
    user_defined.run() 