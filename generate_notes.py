import subprocess
import os

def run_script(script_path, book_name, version):
    # Set environment variables
    env = os.environ.copy()
    env['BOOK_NAME'] = book_name
    env['VERSION'] = version

    # Construct the command to run the script
    command = ['python3', script_path]
    subprocess.run(command, check=True, env=env)

def write_report(book_name):
    report_content = f"# Report for {book_name}\n"

    with open("report.md", "w") as report_file:
        report_file.write(report_content)

def main():
    # Get inputs from the user
    book_name = input("Enter the book name (e.g., 2 Chronicles): ")
    version = input("Enter the version (e.g., ult or ust): ")

    # Write to report.md
    write_report(book_name)

    # List of scripts to run (add more as needed)
    scripts_to_run = [
        'usfm_extraction.py',
        'en_find_figs_go.py',
        'en_find_new_abnouns.py',
        'en_find_ordinals.py',
        'en_find_passives.py',
        'en_find_prop_names.py',
        'combine_tsv.py'
    ]

    # Run each script in sequence
    for script in scripts_to_run:
        try:
            run_script(script, book_name, version)
            print(f"Script {script} executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")

if __name__ == "__main__":
    main()
