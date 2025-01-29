import os
import csv
import re
import yaml

def read_tsv(file_path):
    """Read a TSV file and return a list of dictionaries."""
    verse_texts = []
    with open(file_path, 'r', encoding='utf-8') as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter='\t')
        for row in reader:
            verse_texts.append(row)
    return verse_texts

def get_ai_query_function(which_ai, instance):
    """Get the appropriate AI query function based on environment variable."""
    if which_ai == 'openai':
        return instance._query_openai
    elif which_ai == 'gemini':
        return instance._query_gemini
    elif which_ai == 'claude':
        return instance._query_claude
    else:
        raise ValueError(f"Invalid AI model specified: {which_ai}")

def apply_dev_verse_limit(verse_texts):
    """Apply development verse limit if in dev mode."""
    if os.getenv('STAGE') == 'dev':
        try:
            max_verses = int(os.getenv('DEV_NUMBER_OF_VERSES', 0))
            if max_verses > 0:
                return verse_texts[:max_verses]
        except ValueError:
            print("Warning: Invalid DEV_NUMBER_OF_VERSES value")
    return verse_texts

def organize_verses_by_chapter(verse_texts):
    """Organize verses by chapter."""
    chapters = {}
    for verse in verse_texts:
        reference = verse['Reference']
        if reference == '-':
            continue
        try:
            book_name, chapter_and_verse = reference.rsplit(' ', 1)
            chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(verse)
        except ValueError:
            print(f"Warning: Malformed reference '{reference}'")
            continue
    return chapters

def organize_verses_by_section(verse_texts):
    """Organize verses by section, where sections are separated by '-' entries."""
    sections = []
    current_section = []
    
    # Handle first verse
    if verse_texts and verse_texts[0]['Verse'] != '-':
        current_section.append(verse_texts[0])
    
    # Process remaining verses
    for verse in verse_texts[1:]:
        if verse['Verse'] == '-':
            if current_section:  # Only append if section has verses
                sections.append(current_section)
            current_section = []
        else:
            current_section.append(verse)
    
    # Add the last section if it exists
    if current_section:
        sections.append(current_section)
        
    return sections

def combine_verses_into_content(verses, include_reference=True):
    """Combine verses into a single string for AI processing."""
    if include_reference:
        return "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
    return "\n".join([verse['Verse'] for verse in verses])

def process_malformed_references(reference, log_func=None):
    """Process and validate verse references, optionally logging issues."""
    if reference == '-' or ' ' not in reference:
        if log_func:
            log_func(f"Skipping malformed reference: {reference}")
        return None
    
    try:
        book_name, chapter_and_verse = reference.rsplit(' ', 1)
        return book_name, chapter_and_verse
    except ValueError as e:
        if log_func:
            log_func(f"Error processing reference '{reference}': {e}")
        return None

def read_referenced_file(file_path):
    """Read a referenced file and return its contents as text."""
    try:
        full_path = os.path.join('tn_prepper', file_path)
        print(f"\nReading file: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            print(f"Successfully read {len(content)} characters")
            return content
    except FileNotFoundError:
        print(f"ERROR: Referenced file {full_path} not found")
        return ""
    except Exception as e:
        print(f"ERROR: Failed to read {full_path}: {str(e)}")
        return ""

def process_template_string(template_str):
    """Process a template string, replacing both variable and file references."""
    if not isinstance(template_str, str):
        return template_str, {}
    
    print("\n" + "-"*40)
    print("Processing template string")
    print(f"Preview: {template_str[:100]}...")
    
    # Find all references in curly braces
    refs = re.finditer(r'\{([^}]+)\}', template_str)
    variables = {}
    processed = template_str
    
    for match in refs:
        ref = match.group(1)
        print(f"\nFound reference: {ref}")
        # If reference ends in a file extension, treat as file
        if re.search(r'\.(json|txt|tsv|md)$', ref):
            print(f"Processing as file reference: {ref}")
            file_content = read_referenced_file(ref)
            processed = processed.replace(match.group(0), file_content)
            print(f"Replaced file content (preview): {file_content[:100]}...")
        else:
            print(f"Processing as variable reference: {ref}")
            variables[ref] = None
            
    print(f"\nFound {len(variables)} variables: {list(variables.keys())}")
    print("-"*40)
    return processed, variables

def process_prompt_references(prompts):
    """Process file references in prompts configuration."""
    print("\n" + "="*80)
    print("Processing prompt references")
    
    # Process config section if it exists
    if 'config' in prompts:
        print("\nProcessing config section")
        for key, value in prompts['config'].items():
            if isinstance(value, str):
                print(f"Processing config key: {key}")
                prompts['config'][key], _ = process_template_string(value)
    
    # Process prompts section if it exists
    if 'prompts' in prompts:
        print("\nProcessing prompts section")
        for prompt_name, prompt_data in prompts['prompts'].items():
            print(f"\nProcessing prompt: {prompt_name}")
            if isinstance(prompt_data, dict) and 'content' in prompt_data:
                prompts['prompts'][prompt_name]['content'], _ = process_template_string(prompt_data['content'])
    
    print("\nFinished processing prompt references")
    print("="*80)
    return prompts 

def load_prompts(script_name=None):
    """Load prompts from prompts.yaml file."""
    print("\n" + "="*80)
    print(f"Loading prompts for script: {script_name}")
    
    try:
        with open('tn_prepper/prompts.yaml', 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
            
        if script_name:
            if script_name == 'system':
                print("Returning system prompts")
                result = prompts['system']
            else:
                print(f"Returning prompts for script: {script_name}")
                result = prompts['scripts'].get(script_name, {})
        else:
            print("Returning all prompts")
            result = prompts
            
        print(f"Successfully loaded prompts with keys: {list(result.keys())}")
        print("="*80)
        return result
        
    except Exception as e:
        print(f"ERROR: Failed to load prompts: {str(e)}")
        print("="*80)
        return {} 

def load_issue_descriptions():
    """Load and process issue descriptions from the data file.
    Returns a dictionary mapping issue types to their descriptions and examples."""
    descriptions = {}
    current_block = []
    current_support_ref = None
    
    try:
        with open('tn_prepper/data/sample tns-all issues with descriptions.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('Type of translation issue:'):
                    # Start a new block
                    if current_block and current_support_ref:
                        # Store the previous block
                        ref_key = current_support_ref.split('/')[-1]  # Get the last part of the reference
                        if ref_key not in descriptions:
                            descriptions[ref_key] = []
                        descriptions[ref_key].append('\n'.join(current_block))
                    current_block = [line]
                    current_support_ref = None
                elif line.startswith('SupportReference:'):
                    current_support_ref = line.split(':', 1)[1].strip()
                elif line:
                    current_block.append(line)
            
            # Don't forget to store the last block
            if current_block and current_support_ref:
                ref_key = current_support_ref.split('/')[-1]
                if ref_key not in descriptions:
                    descriptions[ref_key] = []
                descriptions[ref_key].append('\n'.join(current_block))
                
        # Combine multiple blocks for each issue type
        combined_descriptions = {}
        for ref_key, blocks in descriptions.items():
            # Remove redundant descriptions, keep unique examples
            first_block = blocks[0]
            description_line = next((line for line in first_block.split('\n') if line.startswith('description of issue:')), '')
            
            # Combine all blocks but keep only one description
            combined = [first_block]
            for block in blocks[1:]:
                # Skip the type and description lines in subsequent blocks
                block_lines = block.split('\n')
                filtered_lines = [line for line in block_lines 
                                if not line.startswith('Type of translation issue:') 
                                and not line.startswith('description of issue:')]
                if filtered_lines:
                    combined.append('\n'.join(filtered_lines))
            
            combined_descriptions[ref_key] = '\n'.join(combined)
                
        print(f"Successfully loaded {len(combined_descriptions)} issue descriptions")
        return combined_descriptions
    except Exception as e:
        print(f"Error loading issue descriptions: {str(e)}")
        return {} 