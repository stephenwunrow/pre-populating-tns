# Introduction
This repo contains experiments with regards to the prepopulation of Translation Notes. These experiments are based on data from completed or in-progress book packages.

# NOTE: ALL INFORMATION BELOW NEEDS TO BE UPDATED

# Overview

Individual python scripts process inputs, primarily a tagged English translation (ULT), for a specific book. Each script then processes this data to create a TSV file of raw data. Then, this raw data is transformed into the format required by Translation Notes and written to another TSV file. Each individual script targets a specific translation issue. So far, the following issues are covered:

    * figs-go (words such as go, come, take, and bring)
    * figs-abstractnouns (such as "peace" or "happiness")
    * translate-ordinal (ordinal numbers such as “fifth” or “third”)
    * figs-activepassive
    * translate-names
    * figs-metaphor
    * figs-metonymy
    * figs-rquestions
    * figs-personification
    * figs-simile
    * figs-doublet
    * figs-parallelism
    * translate-unknowns

Some of the script (abstractnouns, activepassive, and names) also generate reports that are written to a report file. Finally, the generated notes are combined and sorted (first by chapter, then by verse, and finally by sequence of the English snippet that the note comments on).

# Inputs and Outputs

## Inputs
Each script that deals with a translation issue takes as input the book in the ULT (or UST) that the user chooses from https://git.door43.org. The script for abstract nouns includes its own list of abstract nouns (which were generated from notes in completed books). The script for names takes the list of names from Translation Words as an additional input.

The script that combines and sorts the notes takes outputs from the other scripts as its input.

It is important that these inputs are URLs. That way, whenever a new master of ULT, UST, or TW is published, these scripts access the most recent versions.

NOTE - user choice of book and version is indicated ina  .env file under the variable names 'BOOK_NAME' and 'VERSION'.

## Outputs

Scripts that deal with specific translation issues generate a TSV file of data (en_new_….tsv) and a TSV file of notes (transformed_….tsv). Some of the scripts also write data to a report file (`report.md`). 

There is also a script that generates a TSV file of the ULT translation of the selected book (`ult_book.tsv`).

The combining script outputs a file of sorted notes (`combined_notes.tsv`).

# Details by script

## Master script: `Generate_Notes.py`

This script requests user input for which issues to run. It then runs each individual script in correct sequence.

## ULT in English: `ULT.py`

This script generates a TSV file of the translation and book that the user requested. The first column contains the book, chapter, and verse, and the second column contains the English in plain text.

## The translation issue of go, come, take, and bring (1): `Go.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, saves the reference, Hebrew word, gloss, and morphology for each verb, and then narrows the lines down so that only forms of go, come, bring, and take remain. It saves these lines to en_new_figs_go.tsv. Then, using word mappings, it generates the appropriate parallel word (e.g., "come" for "go", or "taken" for "brought") for each line and writes rows in Translation Notes format (minus ID) to `transformed_figs_go.tsv`.

## The translation issue of abstract nouns (2): `AbstractNouns.py`

This script contains a list of abstract nouns, and it also scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches each chunk for each abstract noun (and the noun tag in the morphology), and for each found abstract noun saves the reference, abstract noun, Hebrew word, and snippet. It saves these lines to en_new_passives.tsv. Then, it counts the occurrences of each abstract noun and writes this data to report.md. Finally, it takes the data and writes rows in Translation Notes format (minus ID) to `transformed_passives.tsv`.

## The translation issue of ordinal numbers (3): `Ordinals.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches the morphology for words tagged as ordinals, and for each found ordinal saves the reference, Hebrew word, and snippet. It saves these lines to en_new_ordinals.tsv. Then, it takes the data and writes rows in Translation Notes format (minus ID) to `transformed_ordinals.tsv`.

## The translation issue of passive verbs (4): `Passives.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, saves the reference, Hebrew word, gloss, and morphology for each verb, and then narrows the lines down so that only English passive forms are still included (forms of the being verb + standard endings such as "ed" and "en" as well as a list of irregular past participles). Then, it analyzes the morphology for each remaining line. It categorizes the verbs by whether they are a Hebrew verbal form that is usually passive (Qal passive, Niphal, Hophal, Pual) or not. It then writes the forms that are not a normal Hebrew passive to report.md. Finally, it writes rows in Translation Notes format (minus ID) to `transformed_passives.tsv`.

## The translation issue of names (5): `Names.py`

This script scrapes the usfm data for the requested book and translation. It chunks the data by Hebrew word, searches the morphology for words tagged as proper nouns, and for each found proper noun saves the reference, Hebrew word, proper noun, and snippet. It also counts how many times each proper noun appears. Then, it scrapes a list of names addressed in Translation Words and removes the lines that contain these names. After that, it writes each remaining name and count to report.md and the rows of data to en_new_names.tsv. Then, for each first occurrence of a name, it writes a row in Translation Notes format (minus ID) to `transformed_names.tsv`. For all following occurrences of the name, no row is written.

## The translation issue of metaphor (6): `Metaphors.py`

This script asks an LLM to identify metaphor, and if found, runs through several queries to identify the data needed to create a note. That data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file. 

## The translation issue of metonymy (7): `Metonymy.py`

This script asks an LLM to identify metonymy, and if found, runs through several queries to identify the data needed to create a note. That data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file. 

## The translation issue of rhetorical questions (8): `RQuestion.py`

This script asks an LLM to identify rhetorical questions, and if found, runs through several queries to identify the data needed to create a note. That data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file. 

## The translation issue of personification (9): `Personification.py`

This script is a first attempt to pass an entire chapter to an LLM and ask it to generate a table of personification data for the chapter. The data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file.

## The translation issue of personification (10): `Similes.py`

This script is another attempt to pass an entire chapter to an LLM and ask it to generate a table of simile data for the chapter. The data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file.

## The translation issue of personification (11): `Doublets.py`

This script is another attempt to pass an entire chapter to an LLM and ask it to generate a table of doublet data for the chapter. The data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file.

## The translation issue of personification (12): `Parallelism.py`

This script is another attempt to pass an entire chapter to an LLM and ask it to generate a table of parallelism data for the chapter. The data is written to a TSV file. Then, the data is transformed into Translation Notes format (minus ID) and written to another TSV file.

## The translation issue of personification (13): `Unknowns.py`

This script is another attempt to pass an entire chapter to an LLM and ask it to generate a table of parallelism data for the chapter. The data is written to a TSV file. Then, the identified words and phrases are checked against the list of defined terms in the Translation Words resource. If the word or phrase is not found in Translation Words, the row is transformed into Translation Notes format (minus ID) and written to another TSV file.

## Combining notes: `Combine_Notes.py`

This script reads all the "transformed_….tsv" files created by the previous scripts. It combines them and then sorts them. It sorts first by chapter, then by verse, and then by placement of the start of the "snippet" text within the English verse text provided by ult_book.tsv (in doing this, it treats … as a wildcard of up to 40 characters). It then adds a unique ID for each row. Finally, it writes the rows to `combined_notes.tsv`.

## Generating additional data: `ATs_snippets.py`

This script runs through the combined notes and queries an LLM for additional required data for certain SupportReferences. It then combines "translate-names" notes in a verse when the names refer to the same class (e.g., "man" or "region"). It then writes the modified lines to `ai_notes.tsv`.

## Generating correct Hebrew: `Final_Snippets.py`

This script creates dictionaries for Hebrew and ULT words, finds the Hebrew for the generated ATs, and lengthens the ATs as needed to match the Hebrew. It writes the final notes to `final_notes.tsv`.

## Running the scripts

### Requirements
It is advisable to setup this project inside a 'virtual environment', so that it doesn't conflict with your other projects. 

To install requirements:
`pip install -f requirements.txt`

### The scripts
There are some file paths and variables to set up in a .env file. These include book name, version, API key, and file paths to the ULT text and `combined_notes.tsv`.

# Further Work/Todo

- Right now, output files are being overwritten when it's the same book. How bad is that?

There are at least three areas in which further development is ongoing:

1. There are many more translation issues to write individual scripts for
2. What is the best workflow for a final product?