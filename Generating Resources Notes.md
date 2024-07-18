# Intro
Based on the tests I've run, I'm including here what seem to be requirements for "success," problems I've run into consistently that need to be resolved for "success," and a proposed points system for ranking output.

# General Requirements for Success
(1) Accuracy
    The model must be able to identify all translation issues, identify the correct issue in each case, and generate the correct sup ref and note template for that issue.

(2) Repeatability
    The model must be able to repeatedly generate the same or very similar outputs for the same section of text.

(3) Speed
    The model must be able to generate the output in a reasonable amount of time (not sure exactly what number to assign to this for success).

(4) Cost
    The model must be reasonably priced (again, not sure what number to assign to this).

(5) Output format
    The output must be either in correct TN format or in a table that can easily be adapted to TN format. For each note, the following data must be generated:
    (a) chapter and verse
    (b) translation issue
    (c) explanation of issue (following appropriate template for sup ref)
    (d) snippet (either in English or in original language)
    (e) alternate translation (following guidelines for sup ref and exactly replacing snippet)

# Consistent Problems
(1) Inconsistent identification of translation issues
    Models I've been using will only identify some of the translation issue types
    Also, they will identify the issue on a first run and then fail to identify it on a second run or vice versa

(2) Misidentification of figures of speech
    Models I've been using will frequently identify the wrong figure of speech
    Particularly, personification, hyperbole, and metaphor are often expanded to cover too many situations

(3) Misidentification of the function of discourse features
    Models I've been using will incorrectly identify the function of transition words
    Also, they sometimes grab things that are not actually logical transition markers

(4) Misquoting snippet
    Although this is pretty easily improved, some models with a certain type of instruction will misquote the text when generating a snippet

(5) Mismatch between AT and snippet
    Frequently, the snippet is much longer than the AT or vice versa
    Giving very precise instructions in the correct sequence seems to help

(6) Insufficient or incorrect explanation of translation issue
    If the templates are at all vague, the models I've been using will often over- or under-explain the translation issue
    If we can get cleaned up and precise templates, things should go a lot better

# Points System for Rating Output
    * Recognition of issue and note written
        If issue not recognized, give zero points

    * 6 points - Appropriate sup ref and note template
    * 6 points - Appropriate AT for sup ref
    * 4 points - Appropriate snippet
    * 4 points - AT exactly replaces snippet

A perfect note is thus 20 points, while a missing note is zero points. 
Divide the total number of points by the possible number of points to get the percentage.

Goal percentage: 90%
Acceptable percentage: 75%

# Ideas/Recommendations for Ongoing Work
(1) Create a set of precise model templates for each sup reference, ideally two or three for each one
(2) Generate as much data as possible ahead of time (for example, we can find all passives, names, and ordinals ahead of time and feed them to the model)
(3) Be sure to check names and unknowns against TW somewhere in the process
(4) Always check repeatability