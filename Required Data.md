# Required Data for UW Notes by SupportReference

Note: Data must be taken from the ULT for that book (master can be found here: https://git.door43.org/unfoldingWord/en_ult)

## Definitions

### "Alternate translation"
The alternate translation provides a way to express the idea from the snippet without using the translation issue identified. For example, if the note is on abstract nouns, the alternate translation will not include any abstract nouns. If the note is on passive voice, the alternate translation will not include any passive voice.
NOTE: the alternate translation must replace the snippet exactly so that the ULT verse, with the alternate translation in place, can still be read as a grammatical, fluent sentence.

### "query"
An LLM query should produce the data.

### "search"
Searching the ULT and its morphology should produce the data

### "Snippet"
These are the exact English words from the ULT that the alternate translation replaces.

### "ULT"
unfoldingWord Literal Text. Notes are always written to this text.

## Required Data for a Note in General (I have infrastructure to put data into templates, generate the corresponding Hebrew, and format everything properly)

(1) Verse reference (e.g., 1:3)
(2) Identification of issue (e.g., abstractnoun)
(3) Word or phrase under discussion, sometimes (e.g., peace)
(4) Alternate translation, following SupportReference rules (e.g., “May God make you peaceful”)
(5) Snippet (e.g., “Peace from God”)
(6) Other - various items needed for specific support references

## Required Data by SupportReference

### figs-abstractnouns

(1) Verse reference - search
(2) Identification of issue - search
(3) Word or phrase under discussion - search
(4) Alternate translation - query
(5) Snippet - query

### translate-names

(1) Verse reference - search
(2) Identification of issue - search
(3) Word or phrase under discussion - search
(5) Snippet - search
(6) Other: identification of class of thing named - query

### figs-go

(1) Verse reference - search
(2) Identification of issue - search
(3) Word or phrase under discussion - search
(4) Alternate translation - search
(5) Snippet - search
(6) Other: identify places where movement is not view - query

### figs-activepassive

(1) Verse reference - search
(2) Identification of issue - search
(4) Alternate translation - query
(5) Snippet - query

### translate-ordinals

(1) Verse reference - search
(2) Identification of issue - search
(4) Alternate translation - query
(5) Snippet - query

### figs-metaphor

(1) Verse reference - query
(2) Identification of issue - query
(4) Alternate translation - query
(5) Snippet - query
(6) Other: description of the metaphor's function, beginning with the words "This metaphor" - query

### figs-metonymy

(1) Verse reference - query
(2) Identification of issue - query
(3) Word or phrase under discussion - query
(4) Alternate translation - query
(5) Snippet - query
(6) Other: description of the meaning of the metonymy, beginning with the words "This phrase/word represents" - query

### figs-rquestions

(1) Verse reference - query
(2) Identification of issue - query
(3) Word or phrase under discussion: person speaking/writing the question - query
(4) Alternate translation - query
(5) Snippet - query
(6) Other: description of the function of the rhetorical question, beginning with the words "The author is using the question form to" - query

### figs-personification

(1) Verse reference - query
(2) Identification of issue - query
(3) Word or phrase under discussion: person speaking/writing the personification - query
(4) Alternate translation - query
(5) Snippet - query
(6) Other: description of the function of the personification, in the form "The speaker speaks of [thing] as if it were a person who could [action]" - query