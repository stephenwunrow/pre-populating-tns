from TNPrepper import TNPrepper
import os
from dotenv import load_dotenv

load_dotenv()

class ScriptRunner(TNPrepper):
    def __init__(self, script_path):

        # Mapping from category to script name
        self.script_mapping = {
            "abstract nouns": "AbstractNouns.py",
            "go": "Go.py",
            "names": "Names.py",
            "ordinals": "Ordinals.py",
            "passives": "Passives.py",
            "rhetorical questions": "RQuestion.py",
            "logical relationships": "Logical_Relationships.py",
            "parallelism": "Parallelism.py",
            "doublets": "Doublets.py",
            "unknowns": "Unknowns.py",
            "explicit": "Explicit.py",
            "ellipsis": "Ellipsis.py",
            "figures of speech": "Figs_of_Speech.py",
            "123person": "123person.py",
            "kinship": "Kinship.py",
            "quotations": "Quotations.py",
            "pronouns": "Pronouns.py",
            "collective nouns": "Collective_Nouns.py",
            "gender notations": "Gender.py",
            "generic nouns": "Generic_Nouns.py",
            "nominal adjectives": "Nominal_Adjectives.py"
            # Add more categories and corresponding scripts here
        }

        self.script_path = script_path

    def get_excluded_categories(self):
        # Display the list of categories to the user
        print("Available categories:")
        for category in self.script_mapping.keys():
            print(f"- {category}")

        # Ask the user which categories they do not want to run
        excluded_categories = input("Please enter the categories you do not want to run, separated by commas: ")
        excluded_categories = [category.strip() for category in excluded_categories.split(",")]
        return excluded_categories

    def run_scripts(self):
        self.run_script('ULT.py')
        print('Running ULT.py')

        excluded_categories = self.get_excluded_categories()

        for category, script_name in self.script_mapping.items():
            if category not in excluded_categories:
                print(f"Running script for category: {category}")
                self.run_script(script_name)
            else:
                print(f"Skipping script for category: {category}")

        print('Running Combine_Notes.py')
        self.run_script('Combine_Notes.py')

        print('Running ATs_snippets.py')
        self.run_script('ATs_snippets.py')

        print('Running Final_Snippets.py')
        self.run_script('Final_Snippets.py')
        
        print('All data can found in output/book_name')
        print('Final product is "final_notes.tsv"')

    def run_script(self, script_name):
        os.system(f"cd {self.script_path} && python3 {script_name}")

if __name__ == "__main__":

    script_path = os.getenv("SCRIPT_PATH")

    script_runner = ScriptRunner(script_path)
    script_runner.run_scripts()
