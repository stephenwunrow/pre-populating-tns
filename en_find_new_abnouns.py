import requests
from bs4 import BeautifulSoup
import re
import csv
from tqdm import tqdm
import random
import string
from io import StringIO

# TSV data included directly in the script
tsv_data = """Abstract Noun\tCount
faith	169
glory	107
grace	76
truth	75
love	71
righteousness	70
peace	63
power	59
death	58
judgment	53
knowledge	52
hope	47
kingdom	47
salvation	46
joy	46
life	41
mercy	39
wisdom	38
authority	37
honor	30
destruction	27
resurrection	26
sin	25
will	25
unrighteousness	23
evil	22
repentance	21
holiness	20
confidence	20
testimony	18
endurance	17
service	16
justice	15
fear	15
good	14
wrath	14
patience	14
works	14
affliction	13
understanding	13
darkness	13
commandment	13
obedience	13
forgiveness	12
fellowship	12
godliness	12
wickedness	11
deceit	11
tribulation	11
redemption	10
immorality	10
compassion	10
envy	10
encouragement	10
revelation	10
weakness	10
lawlessness	9
work	9
remembrance	9
humility	9
thanksgiving	9
transgression	8
sorrow	8
trespasses	8
teaching	8
tradition	8
self-control	8
jealousy	8
circumcision	8
uncircumcision	8
promise	8
sanctification	8
freedom	8
promises	8
comfort	8
faithfulness	7
royalty	7
petition	7
trouble	7
sickness	7
temptation	7
unbelief	7
condemnation	7
boldness	7
disobedience	7
command	7
blessing	7
slavery	6
abundance	6
likeness	6
covenant faithfulness	6
captivity	6
shame	6
distress	6
strength	6
kindness	6
praise	6
adultery	6
opportunity	6
sins	6
fullness	6
sincerity	6
loss	6
creation	6
dishonor	6
boasting	6
sufferings	6
purpose	6
prophecy	6
proof	6
image	6
favor	5
goodness	5
iniquity	5
request	5
priesthood	5
gentleness	5
labor	5
inheritance	5
right	5
baptism	5
courage	5
rest	5
blasphemy	5
foundation	5
prayer	5
uncleanness	5
anger	5
covetousness	5
division	5
assurance	5
earnestness	5
passions	5
strife	5
generosity	5
mystery	5
foolishness	5
compulsion	5
immortality	5
readiness	5
desire	5
behavior	5
greatness	4
sight	4
skill	4
confusion	4
wealth	4
safety	4
bitterness	4
perfection	4
falsehood	4
reproach	4
rejoicing	4
portion	4
sacrifice	4
violence	4
victory	4
greed	4
hypocrisy	4
desires	4
need	4
suffering	4
quietness	4
nature	4
incorruptibility	4
ambition	4
benefit	4
reconciliation	4
trespass	4
zeal	4
weaknesses	4
reward	4
stewardship	4
gratitude	4
dignity	4
relief	4
confession	4
discipline	4
pain	4
majesty	3
accusation	3
dedication	3
uprightness	3
hardship	3
visitation	3
vanity	3
agreement	3
persecution	3
deceitfulness	3
commandments	3
concern	3
abomination	3
desolation	3
ability	3
punishment	3
burial	3
amazement	3
poverty	3
vengeance	3
appearance	3
slaughter	3
expectation	3
citizenship	3
lust	3
penalty	3
deeds	3
favoritism	3
propitiation	3
justification	3
gracious gift	3
eternal life	3
adoption	3
powers	3
election	3
ministry	3
diligence	3
conscience	3
drunkenness	3
craftiness	3
idolatry	3
varieties	3
interpretation	3
rule	3
affections	3
meekness	3
submission	3
value	3
removal	3
dispersion	3
licentiousness	3
rigor	2
anguish	2
oppression	2
report	2
emptiness	2
craftsmanship	2
beauty	2
might	2
guilt	2
exile	2
integrity	2
consolation	2
injustice	2
futility	2
counsel	2
habitation	2
deliverance	2
terror	2
corruption	2
outcry	2
measure	2
doctrines	2
depth	2
repayment	2
marriage	2
waste	2
hardness	2
afflictions	2
fillings	2
evils	2
childhood	2
persecutions	2
murder	2
foreknowledge	2
exultation	2
possession	2
trickery	2
thankfulness	2
religion	2
care	2
hindrance	2
apostleship	2
witness	2
ungodliness	2
full awareness	2
malice	2
decree	2
forbearance	2
unfaithfulness	2
distinction	2
demonstration	2
character	2
gift	2
lusts	2
outcome	2
mindset	2
practices	2
decay	2
remnant	2
offense	2
completion	2
acceptance	2
severity	2
judgments	2
compassions	2
thought	2
instruction	2
offering	2
deed	2
divisions	2
speech	2
flattery	2
preaching	2
mind	2
trembling	2
proclamation	2
defense	2
mysteries	2
sufficiency	2
defilement	2
mourning	2
genuineness	2
equality	2
eternity	2
purity	2
impurity	2
curse	2
unity	2
perseverance	2
progress	2
struggle	2
attitude	2
gains	2
goal	2
end	2
requests	2
passion	2
enjoyment	2
maturity	2
consciousness	2
forgetfulness	2
ignorance	2
steadfastness	2
dread	1
wonders	1
trustworthiness	1
reign	1
splendor	1
serving	1
drinking	1
permission	1
banishment	1
confiscation	1
imprisonment	1
help	1
ambush	1
iniquities	1
plunder	1
blacknesses	1
indignation	1
resentment	1
initiative	1
greenness	1
trust	1
despair	1
worthlessness	1
prudence	1
consolations	1
recompense	1
provocations	1
satisfaction	1
dominion	1
ransom	1
investigation	1
correction	1
pleasantness	1
habitations	1
supplications	1
folly	1
double	1
difficulty	1
contempt	1
bondage	1
servitude	1
produce	1
burning	1
fight	1
support	1
faithful kindness	1
repetitions	1
force	1
health	1
worry	1
action	1
flight	1
deception	1
beginning	1
blasphemies	1
worries	1
visibility	1
openness	1
testimonies	1
insurrection	1
kingship	1
stature	1
persistence	1
dispute	1
wonder	1
refreshment	1
restoration	1
custody	1
security	1
humiliation	1
generation	1
conversion	1
pollution	1
apostasy	1
purification	1
strictness	1
fairness	1
abstinence	1
qualities	1
perversion	1
evil intent	1
secrets	1
advantage	1
obligation	1
blessedness	1
deadness	1
access	1
pattern	1
newness	1
oldness	1
hostility	1
hunger	1
riches	1
good pleasure	1
full knowledge	1
retribution	1
rejection	1
gifts	1
calling	1
renewal	1
function	1
cheerfulness	1
wicked	1
brotherly love	1
needs	1
hospitality	1
authorities	1
obligations	1
fulfillment	1
celebrations	1
forethought	1
insults	1
contribution	1
prayers	1
obstacles	1
haste	1
growth	1
reasonings	1
concession	1
observance	1
opinion	1
distraction	1
custom	1
boast	1
admonition	1
traditions	1
disgrace	1
directions	1
ministries	1
display	1
workings	1
discernments	1
administration	1
meaning	1
danger	1
mercies	1
supplication	1
grief	1
recommendation	1
manifestation	1
illumination	1
tribulations	1
hardships	1
distresses	1
partnership	1
light	1
harmony	1
conflicts	1
fears	1
longing	1
regret	1
lack	1
thanksgivings	1
warfare	1
situation	1
imprisonments	1
deaths	1
dangers	1
debauchery	1
manner	1
transgressions	1
trial	1
burdens	1
reason	1
cleverness	1
scheming	1
rage	1
recklessness	1
honesty	1
goodwill	1
provision	1
gain	1
conceit	1
worth	1
profitable	1
working	1
full assurance	1
philosophy	1
decrees	1
commands	1
teachings	1
indulgence	1
complaint	1
examples	1
pretext	1
eternal destruction	1
eternal	1
belief	1
example	1
argument	1
modesty	1
overseership	1
quickness	1
prejudgment	1
partiality	1
benefaction	1
controversies	1
contentment	1
ruin	1
sorrows	1
uncertainty	1
oppositions	1
incorruption	1
godlessness	1
pleasures	1
brightness	1
representation	1
being	1
attention	1
atonement	1
provocation	1
thoughts	1
intentions	1
source	1
message	1
confirmation	1
quality	1
refuge	1
annulment	1
introduction	1
regulations	1
worship	1
presentation	1
reminder	1
habit	1
preservation	1
conception	1
release	1
opposition	1
reverence	1
awe	1
exhortation	1
testing	1
exaltation	1
lowliness	1
doing	1
cursing	1
conduct	1
unsettledness	1
friendship	1
enmity	1
laughter	1
gloom	1
pretensions	1
miseries	1
glories	1
hypocrisies	1
envies	1
slanders	1
adornment	1
good conscience	1
appeal	1
carousing	1
oversight	1
excellence	1
brotherly affection	1
cleansing	1
seeing	1
hearing	1
pleasure	1
deceptions	1
rebuke	1
irrationality	1
defilements	1
mockery	1
anointing	1
error	1
triumph	1
necessity	1
lordship	1
thanks	1
tribulatron	1
indecency	1
"""

# Parse the TSV data from the string
ab_nouns = []
reader = csv.DictReader(StringIO(tsv_data), delimiter='\t')

# Validate the header
if reader.fieldnames == ["Abstract Noun", "Count"]:
    for row in reader:
        ab_noun = row['Abstract Noun'].strip()
        ab_nouns.append(ab_noun)
else:
    print("The header does not match the expected format.")

# Mapping of book names to their respective acronyms
acronym_mapping = {
    "Genesis": "01-GEN",
    "Exodus": "02-EXO",
    "Leviticus": "03-LEV",
    "Numbers": "04-NUM",
    "Deuteronomy": "05-DEU",
    "Joshua": "06-JOS",
    "Judges": "07-JDG",
    "Ruth": "08-RUT",
    "1 Samuel": "09-1SA",
    "2 Samuel": "10-2SA",
    "1 Kings": "11-1KI",
    "2 Kings": "12-2KI",
    "1 Chronicles": "13-1CH",
    "2 Chronicles": "14-2CH",
    "Ezra": "15-EZR",
    "Nehemiah": "16-NEH",
    "Esther": "17-EST",
    "Job": "18-JOB",
    "Psalms": "19-PSA",
    "Proverbs": "20-PRO",
    "Song of Solomon": "22-SNG",
    "Isaiah": "23-ISA",
    "Jeremiah": "24-JER",
    "Lamentations": "25-LAM",
    "Ezekiel": "26-EZK",
    "Daniel": "27-DAN",
    "Hosea": "28-HOS",
    "Joel": "29-JOL",
    "Amos": "30-AMO",
    "Obadiah": "31-OBA",
    "Jonah": "32-JON",
    "Micah": "33-MIC",
    "Nahum": "34-NAM",
    "Habakkuk": "35-HAB",
    "Zephaniah": "36-ZEP",
    "Haggai": "37-HAG",
    "Zechariah": "38-ZEC",
    "Malachi": "39-MAL",
    "Matthew": "41-MAT",
    "Mark": "42-MRK",
    "Luke": "43-LUK",
    "John": "44-JHN",
    "Acts": "45-ACT",
    "Romans": "46-ROM",
    "1 Corinthians": "47-1CO",
    "2 Corinthians": "48-2CO",
    "Galatians": "49-GAL",
    "Ephesians": "50-EPH",
    "Philippians": "51-PHP",
    "Colossians": "52-COL",
    "1 Thessalonians": "53-1TH",
    "2 Thessalonians": "54-2TH",
    "1 Timothy": "55-1TI",
    "2 Timothy": "56-2TI",
    "Titus": "57-TIT",
    "Philemon": "58-PHM",
    "Hebrews": "59-HEB",
    "James": "60-JAS",
    "1 Peter": "61-1PE",
    "2 Peter": "62-2PE",
    "1 John": "63-1JN",
    "2 John": "64-2JN",
    "3 John": "65-3JN",
    "Jude": "66-JUD",
    "Revelation": "67-REV"
}

# Get the book name from the user
book_name = input("Enter the book name (e.g., 2 Chronicles): ")
version = input("Enter the version (e.g., ult or ust): ")

# Get the acronym from the acronym mapping
if book_name in acronym_mapping:
    acronym = acronym_mapping[book_name]
else:
    print("Invalid book name. Please enter a valid book name.")
    exit()

# URL of the file to download
url = f"https://git.door43.org/unfoldingWord/en_{version}/raw/branch/master/{acronym}.usfm"

# Function to get the content of the file
def get_file_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return ''

# Get the file content
file_content = get_file_content(url)

# Process the file content
soup = BeautifulSoup(file_content, 'html.parser')

# Initialize variables
chapter = None
verse = None
verse_data = []

# Build the search patterns
patterns = {}
for ab_noun in ab_nouns:
    if ' ' in ab_noun:
        ab_noun1, ab_noun2 = ab_noun.split(' ', 1)
        patterns[ab_noun] = re.compile(rf'x-strong.*?x-morph="[^"]*?Nc[^"]*?".+?x-content="([^"]+?)".*?\\w {ab_noun1}\|.*?\\w {ab_noun2}\|.*?zaln-e', re.IGNORECASE | re.DOTALL)
    else:
        patterns[ab_noun] = re.compile(rf'x-strong.*?x-morph="[^"]*?Nc[^"]*?".+?x-content="([^"]+?)".*?\\w {ab_noun}\|.*?zaln-e', re.IGNORECASE | re.DOTALL)

# Combine all lines into a single string
combined_text = soup.get_text(separator='\n')

# Split the combined text by "\\zaln-s"
chunks = combined_text.split('\\zaln-s')

# tqdm setup for chunks
with tqdm(total=len(chunks), desc="Processing Chunks") as pbar:
    for chunk in chunks:
        pbar.update(1)  # Update progress bar

        for ab_noun, pattern in patterns.items():
            matches = pattern.findall(chunk)
            if matches:  # Only proceed if there are matches
                for match in matches:
                    lexeme = match
                    # Append to verse_data with lexeme, verse reference, and ab_noun
                    verse_data.append(f'{book_name} {chapter}:{verse}\t{ab_noun}\t{lexeme}')

        # Find chapter in the chunk
        chapter_match = re.search(r'\\c (\d+)', chunk)
        if chapter_match:
            chapter = int(chapter_match.group(1))
        
        # Find verse in the chunk
        verse_match = re.search(r'\\v (\d+)', chunk)
        if verse_match:
            verse = int(verse_match.group(1))

# Apply regex replacements repeatedly
def apply_replacements(text, patterns):
    while True:
        new_text = text
        for pattern, replacement in patterns:
            new_text = re.sub(pattern, replacement, new_text)
        if new_text == text:
            break
        text = new_text
    return text

# Define the patterns and replacements
replacements = [
    (r'(.+?)(\t)(\w+) (\w+)(\t.+?)\n\1\t\3.+', r'\1\2\3 \4\5'),
    (r'(.+?)(\t)(\w+) (\w+)(\t.+?)\n\1\t\4.+', r'\1\2\3 \4\5'),
    (r'(.+?)(\t)(\w+)(\t.+?\n)(\1\t\w+ \3\t.+)', r'\5'),
    (r'(.+?)(\t)(\w+)(\t.+?\n)(\1\t\3 \w+\t.+)', r'\5')
]

# Join the verse_data list into a single string
verse_data_str = '\n'.join(verse_data)

# Apply the replacements
verse_data_str = apply_replacements(verse_data_str, replacements)

# Split back into a list
verse_data = verse_data_str.split('\n')


# Count occurrences of each abstract noun
abstract_noun_counts = {}
for line in verse_data:
    if line:
        parts = line.split('\t')
        if len(parts) == 3:
            ab_noun = parts[1]
            if ab_noun in abstract_noun_counts:
                abstract_noun_counts[ab_noun] += 1
            else:
                abstract_noun_counts[ab_noun] = 1

# Sort abstract nouns by count in descending order
sorted_counts = sorted(abstract_noun_counts.items(), key=lambda x: x[1], reverse=True)

# Append the report to report.txt
with open('report.txt', 'a', encoding='utf-8') as report_file:
    report_file.write(f"\n\nAbstract nouns from {book_name}\nAbstract Noun\tFrequency\n")
    for ab_noun, count in sorted_counts:
        report_file.write(f"{ab_noun}\t{count}\n")

print("Report has been appended to report.txt")

# Write all collected data to the output file only if there are abstract nouns found
if verse_data:
    with open('en_new_ab_nouns.tsv', 'w', encoding='utf-8') as f:
        f.write('Reference\tAbstract Noun\tLexeme\n')
        for line in verse_data:
            f.write(line + '\n')

    print(f"Data has been written to en_new_ab_nouns.tsv")
else:
    print("No abstract nouns found. Output file not created.")

# Function to generate a random, unique four-letter and number combination
def generate_random_code():
    first_char = random.choice(string.ascii_lowercase)
    remaining_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return first_char + remaining_chars

# Standard link and note
standard_link = 'rc://*/ta/man/translate/figs-abstractnouns'
standard_note_template = 'If your language does not use an abstract noun for the idea of **{ab_noun}**, you could express the same idea in another way. Alternate translation: “alternate_translation”'

# Read the input file
with open('en_new_ab_nouns.tsv', 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile, delimiter='\t')
    # Skip the header
    next(reader)
    rows = [row for row in reader]

# Write to the output file
with open('transformed_ab_nouns.tsv', 'w', encoding='utf-8') as outfile:
    writer = csv.writer(outfile, delimiter='\t')
    # Write the headers
    writer.writerow(['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note'])
    
    for row in rows:
        if len(row) == 3:
            reference = row[0]
            ab_noun = row[1]
            lexeme = row[2]

            # Extract chapter and verse from the reference
            chapter_verse = reference.split(' ', 1)[1]

            # Generate a random code
            random_code = generate_random_code()

            # Create the new row
            transformed_row = [
                chapter_verse,  # Reference without the book name
                random_code,    # ID: random, unique four-letter and number combination
                '',             # Tags: blank
                standard_link,  # SupportReference: standard link
                lexeme,         # Quote: lexeme
                '1',            # Occurrence: the number 1
                standard_note_template.format(ab_noun=ab_noun)  # Note: standard note with {ab_noun}
            ]

            # Write the transformed row to the output file
            writer.writerow(transformed_row)

print(f"Data has been transformed and written to transformed_ab_nouns.tsv")
