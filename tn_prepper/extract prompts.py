import os
import re

def extract_prompts(file_content):
    # This pattern looks for assignments to variables named prompt, prompt1, prompt2, etc.
    prompt_pattern = re.compile(r'(prompt\d*\s*=\s*)(\(?\s*[f]?(?:"""|\'))(.*?)(\2\s*\)?)', re.DOTALL)
    prompts = prompt_pattern.findall(file_content)
    return [(match[0].strip(), match[2].strip()) for match in prompts]

def write_prompts_to_file(output_file, prompts_by_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for filename, prompts in prompts_by_file.items():
            f.write(f"File: {filename}\n")
            f.write("="*50 + "\n\n")
            for prompt_name, prompt_content in prompts:
                f.write(f"{prompt_name}:\n")
                f.write("-"*30 + "\n")
                f.write(prompt_content + "\n\n")
            f.write("\n\n")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'extracted_prompts.txt')
    prompts_by_file = {}

    for filename in os.listdir(script_dir):
        if filename.endswith('.py'):
            file_path = os.path.join(script_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                prompts = extract_prompts(content)
                if prompts:
                    prompts_by_file[filename] = prompts

    write_prompts_to_file(output_file, prompts_by_file)
    print(f"Prompts have been extracted and written to {output_file}")

if __name__ == "__main__":
    main()