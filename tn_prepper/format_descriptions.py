import re
import json

def process_file(input_file, output_file):
    issues_data = {}
    issue = None
    issue_description = None
    samples = []
    bible_reference = None
    entire_verse = None
    portion_of_verse_with_issue = None
    translation_note = None
    alternate_translation = None
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('Type of translation issue:'):
                if issue == line.split(':')[1].strip():
                    continue
                else:                                            
                    # Create sample when we have all the required data
                    if all([issue, issue_description]) and len(samples) >= 1:
                        issues_data[issue.lower()] = {
                            "description": issue_description,
                            "samples": samples
                        }
                    # Reset the current values
                    issue = line.split(':')[1].strip()
                    issue_description = None
                    samples = []                    
                    bible_reference = None
                    entire_verse = None
                    portion_of_verse_with_issue = None
                    translation_note = None
                    alternate_translation = None                    

            elif line.startswith('description of issue:'):
                if issue_description == line.split(':')[1].strip():
                    continue
                else:
                    issue_description = line.split(':')[1].strip()
            elif line.startswith('SupportReference:'):
                support_reference = ':'.join(line.split(':')[1:]).strip()
            elif line.startswith('Bible Reference:'):
                bible_reference = ':'.join(line.split(':')[1:]).strip()
            elif line.startswith('Entire verse:'):
                entire_verse = ':'.join(line.split(':')[1:]).strip()
            elif line.startswith('Portion of verse with issue:'):
                portion_of_verse_with_issue = ':'.join(line.split(':')[1:]).strip()
            elif line.startswith('Translation note:'):
                translation_note = ':'.join(line.split(':')[1:]).strip()
            elif re.match(r'Alternate translation.*?:', line):
                alternate_translation = ':'.join(line.split(':')[1:]).strip()
                if "OR" in alternate_translation:
                    # Split on OR and strip whitespace from each options
                    alternate_translation = [opt.strip() for opt in alternate_translation.split("OR")]
                else:
                    # Single option becomes a list with one item
                    alternate_translation = [alternate_translation]
                sample = {
                    "input": {
                        "Bible Reference": bible_reference,
                        "issue": issue.lower(),
                        "Entire verse": entire_verse,
                        "Portion of verse with issue": portion_of_verse_with_issue
                    },
                    "output": {
                        "Reference": bible_reference.split()[-1],
                        "SupportReference": support_reference,
                        "TranslationNote": translation_note,
                        "AlternateTranslation": alternate_translation
                    }
                }
                samples.append(sample)
 
    # Write formatted JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(issues_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    input_file = "tn_prepper/data/sample tns-all issues with descriptions.txt"
    output_file = "tn_prepper/data/translation_issues2.json"
    process_file(input_file, output_file)
    print(f"Converted {input_file} to JSON format at {output_file}") 