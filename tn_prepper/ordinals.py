from TNPrepper import TNPrepper

# Create an instance of TNPrepper
prepper = TNPrepper()

# Call the method from the TNPrepper class
book_name = "Esther"
version = "ult"
soup = prepper._scrape_and_read_data(book_name, version)

# Define the identification pattern
identification_pattern = r'x-morph="([^"]*?Ao[^"]*?)".+?x-content="([^"]+?)".+\\w .+?\|'

# Create verse data
verse_data = prepper._create_verse_data(soup, book_name, identification_pattern)

# Transform the data
SupportReference = "rc://*/ta/man/translate/translate-ordinal"
note_template = "If your language does not use ordinal numbers, you could use a cardinal number here or an equivalent expression. Alternate translation: “alternate_translation”"
output_path = "output"
file_name = "transformed_data.tsv"

prepper._transform_data(verse_data, output_path, SupportReference, note_template, file_name)
