# Introduction
This repo contains experiments with regards to the prepopulation of Translation Notes. These experiments are based on data from completed or in-progress book packages.

# Overview

Individual python scripts process inputs, primarily a tagged English translation (ULT), for a specific book. Each script then processes this data to create a TSV file of raw data. Then, this raw data is transformed into the format required by Translation Notes and written to another TSV file. Each individual script targets a specific translation issue. So far, the following issues are covered:

    * figs-go (words such as go, come, take, and bring)
    * figs-abstractnouns (such as "peace" or "happiness")
    * translate-ordinal (ordinal numbers such as “fifth” or “third”)
    * figs-activepassive
    * translate-names

Some of the script (abstractnouns, activepassive, and names) also generate reports that are written to a report file. Finally, the generated notes are combined and sorted (first by chapter, then by verse, and finally by sequence of the English snippet that the note comments on).

# Inputs and Outputs

## Inputs
Each script that deals with a translation issue takes as input the book in the ULT (or UST) that the user chooses from https://git.door43.org. The script for abstract nouns includes its own list of abstract nouns (which were generated from notes in completed books). The script for names takes the list of names from Translation Words as an additional input.

The script that combines and sorts the notes takes outputs from the other scripts as its input.

It is important that these inputs are URLs. That way, whenever a new master of ULT, UST, or TW is published, these scripts access the most recent versions.

## Outputs

Scripts that deal with specific translation issues generate a TSV file of data (en_new_….tsv) and a TSV file of notes (transformed_….tsv). Some of the scripts also write data to a report file (`report.md`). 

There is also a script that generates a TSV file of the ULT translation of the selected book (`ult_book.tsv`).

The combining script outputs a file of sorted notes (`combined_notes.tsv`).

# Details by script

## Master script: `generate_notes.py`

This script requests user input to generate the book name and the version that will be the input for all processes (it passes these off as environmental variables). It then runs each individual script in correct sequence.

## ULT in English: `usfm_extraction.py`

This script generates a TSV file of the translation and book that the user requested. The first column contains the book, chapter, and verse, and the second column contains the English in plain text.

## The translation issue of go, come, take, and bring (1): `en_find_figs_go.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, saves the reference, Hebrew word, gloss, and morphology for each verb, and then narrows the lines down so that only forms of go, come, bring, and take remain. It saves these lines to en_new_figs_go.tsv. Then, using word mappings, it generates the appropriate parallel word (e.g., "come" for "go", or "taken" for "brought") for each line and writes rows in Translation Notes format (minus ID) to `transformed_figs_go.tsv`.

## The translation issue of abstract nouns (2): `en_find_new_abnouns.py`

This script contains a list of abstract nouns, and it also scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches each chunk for each abstract noun (and the noun tag in the morphology), and for each found abstract noun saves the reference, abstract noun, Hebrew word, and snippet. It saves these lines to en_new_passives.tsv. Then, it counts the occurrences of each abstract noun and writes this data to report.md. Finally, it takes the data and writes rows in Translation Notes format (minus ID) to `transformed_passives.tsv`.

## The translation issue of ordinal numbers (3): `en_find_ordinals.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches the morphology for words tagged as ordinals, and for each found ordinal saves the reference, Hebrew word, and snippet. It saves these lines to en_new_ordinals.tsv. Then, it takes the data and writes rows in Translation Notes format (minus ID) to `transformed_ordinals.tsv`.

## The translation issue of passive verbs (4): `en_find_passives.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, saves the reference, Hebrew word, gloss, and morphology for each verb, and then narrows the lines down so that only English passive forms are still included (forms of the being verb + standard endings such as "ed" and "en" as well as a list of irregular past participles). Then, it analyzes the morphology for each remaining line. It categorizes the verbs by whether they are a Hebrew verbal form that is usually passive (Qal passive, Niphal, Hophal, Pual) or not. It then writes the forms that are not a normal Hebrew passive to report.md. Finally, it writes rows in Translation Notes format (minus ID) to `transformed_passives.tsv`.

## The translation issue of names (5): `en_find_prop_names.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches the morphology for words tagged as proper nouns, and for each found proper noun saves the reference, Hebrew word, proper noun, and snippet. It also counts how many times each proper noun appears. Then, it scrapes a list of names addressed in Translation Words and removes the lines that contain these names. After that, it writes each remaining name and count to report.md and the rows of data to en_new_names.tsv. Then, for each first occurrence of a name, it writes a row in Translation Notes format (minus ID) to `transformed_names.tsv`. For all following occurrences of the name, no row is written.

## Combining notes: `combine_tsv.py`

This script reads all the "transformed_….tsv" files created by the previous scripts. It combines them and then sorts them. It sorts first by chapter, then by verse, and then by placement of the start of the "snippet" text within the English verse text provided by ult_book.tsv (in doing this, it treats … as a wildcard of up to 40 characters). It then adds a unique ID for each row. Finally, it writes the rows to `combined_notes.tsv`.

## Running the scripts

### Requirements
It is advisable to setup this project inside a 'virtual environment', so that it doesn't conflict with your other projects. 

To install requirements:
`pip install -f requirements.txt`

### The scripts
To run the entire set of scripts to generate notes for each issue, simply run `generate_notes.py`, input the book name and version (ult), and check the outputs. 

The scripts `usfm_extraction.py` or `combine_tsv.py` can also simply be run. 

To run the scripts that deal with specific translation issues individually, the environmental variables must be provided in this form:

`$ BOOK_NAME="Esther" VERSION="ult" python3 script_name.py`

# Further Work/Todo

- Right now, output files are being overwritten, even when it's a completely different book / translation. How bad is that?
- Refactoring into classes + 'motherclass' will be a tremendous help in extendability

There are at least three areas in which further development is ongoing:

1. There are many more translation issues to write individual scripts for
2. The generated notes do not include alternate translations or matching snippets; the plan is to query an LLM to generate these
3. The sort function in combine_tsv.py needs improvement to be completely trustworthy when it comes to snippets with ellipses and snippets that begin with the same word (in such a case, the longer snippet should be first)