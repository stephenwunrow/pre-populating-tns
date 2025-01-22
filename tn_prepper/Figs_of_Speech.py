from TNPrepper import TNPrepper
from groq import Groq
import os
import csv
import re
from dotenv import load_dotenv




class Figs(TNPrepper):
    def __init__(self, book_name):
        super().__init__()

        self.verse_text = f'output/{book_name}/ult_book.tsv'

    def __process_prompt(self, chapter_content):
                # Get the AI model type and corresponding query function
        which_ai = os.getenv('WHICH_AI')
        if which_ai == 'openai':
            query_func = self._query_openai
        elif which_ai == 'gemini':
            query_func = self._query_gemini
        elif which_ai == 'claude':
            query_func = self._query_claude
        else:
            raise ValueError(f"Invalid AI model specified: {which_ai}")     
        
        prompt1 = (
            "You have been given a chapter from the Bible. I want you to look for each of the following specific figures of speech in the chapter: metaphor, simile, idiom, personification, metonymy, synecdoche, apostrophe, euphemism, hendiadys, litotes, merism, hyperbole. This list is roughly in order from most common to least common."
            "\n\nAs you are looking for each figure of speech, make sure that you carefully consider the definition of that figure of speech. Ensure that what you find for each figure of speech is not better classified as a different figure of speech."
            "\n\nFor each figure of speech you find, provide the following information in a tab-separated format:"
            "\n(1) The verse reference (e.g., 1 Kings 1:1)."
            "\n(2) The type of figure of speech."
            "\n(3) An exact quote from the verse that contains the figure of speech."
            "\n\nIf there are several figures of speech in one verse, include a separate set of data for each one."
        )

        response1 = query_func(chapter_content, prompt=prompt1, temp=0.8)
        print(f"\nResponse 1: {response1}")
        self.write_to_log()
        prompt1a = (
            "Here are examples of really good notes along with context:"
            """
            [
  {
    "type_of_translation_issue": "apostrophe",
    "SupportReference": "rc://*/ta/man/translate/figs-apostrophe",
    "BibleRef": "Luke 10:13",
    "BibleVerse": "Woe to you, Chorazin! Woe to you, Bethsaida! For if the miracles had happened in Tyre and Sidon which happened in you, they would have repented long ago, sitting in sackcloth and ashes.",
    "VerseSnippet": "Woe to you, Chorazin! Woe to you, Bethsaida!",
    "translationNote": "Jesus is speaking to two cities that he knows cannot hear him. He is doing this to show in a very strong way how he feels about those cities. He is actually speaking to the people who can hear him, the disciples whom he is sending out. If your readers might not understand why Jesus is speaking to someone who is not present, you could translate his words as if he were speaking directly to his disciples.",
    "alternateTranslations": [
      "Chorazin and Bethsaida are two of the cities whose people God will judge severely for rejecting my message"
    ]
  },
  {
    "type_of_translation_issue": "apostrophe",
    "SupportReference": "rc://*/ta/man/translate/figs-apostrophe",
    "BibleRef": "Judges 9:29",
    "BibleVerse": "Who will give this people into my hand? Then I would depose Abimelech. He said to Abimelech, ‘Enlarge your army and come forth.’”",
    "VerseSnippet": "And he said to Abimelek, “Increase your army and come out.”",
    "translationNote": "Gaal is speaking to Abimelek even though he is not present and cannot hear him. Gaal is doing this to show in a strong way how he feels about Abimelek. He is actually speaking to the people who can hear him, the others who are present at this feast. If your readers might not understand why Gaal is speaking to someone who is not present, you could translate his words as if he were speaking directly to others who are present. Alternate translation, continuing the direct quotation: I would fight against him and his whole army and defeat him!"
  },
  {
    "type_of_translation_issue": "aside",
    "SupportReference": "rc://*/ta/man/translate/figs-aside",
    "BibleRef": "Obadiah 1:7",
    "BibleVerse": "All the men of your covenant are sending you away as far as the border. The men of your peace are deceiving you and are prevailing against you. They of your bread will set a trap under you. There is no understanding in him.",
    "VerseSnippet": "There is no understanding in him",
    "translationNote": "Yahweh has been telling the people of Edom what will happen to them because they did not help the people of Judah. Here he pauses to say something to himself about Edom. If it would be natural and give the right meaning in your language, consider translating this as Yahweh speaking about Edom. But if this way of speaking would be unclear, you can translate this as Yahweh speaking to the people of Edom, but make clear that he is now expressing his thoughts and feelings about them.",
    "alternateTranslations": [
      "You do not understand any of this"
    ]
  },
  {
    "type_of_translation_issue": "aside",
    "SupportReference": "rc://*/ta/man/translate/figs-aside",
    "BibleRef": "Nehemiah 13:31",
    "BibleVerse": "and for the offering of pieces of wood at the appointed times; and for the firstfruits. Remember me, my God, for good.",
    "VerseSnippet": "Remember me, my God, for good.",
    "translationNote": "Here Nehemiah is pausing from addressing the audience that is hearing his story to speak confidentially to God in prayer about two of the characters in the story. If it would be helpful in your language, you could show this is a prayer is distinct from the story by punctuating it as a direct quotation.",
    "alternateTranslations": [
      "“Remember me, my God, for good.”"
    ]
  },
  {
    "type_of_translation_issue": "doublet",
    "SupportReference": "rc://*/ta/man/translate/figs-doublet",
    "BibleRef": "Job 38:23",
    "BibleVerse": "which I keep for a time of trouble, for a day of battle and war?",
    "VerseSnippet": "battle and war",
    "translationNote": "The terms **battle** and **war** mean similar things. Yahweh is using the two terms together for emphasis. If it would be clearer for your readers, you could express the emphasis with a single phrase.",
    "alternateTranslations": [
      "great warfare"
    ]
  },
  {
    "type_of_translation_issue": "doublet",
    "SupportReference": "rc://*/ta/man/translate/figs-doublet",
    "BibleRef": "Acts 2:12",
    "BibleVerse": "So they were all amazed and were perplexed, saying one to another, “What does this want to be?”",
    "VerseSnippet": "they were all amazed and perplexed",
    "translationNote": "The words **amazed** and **perplexed** mean similar things. Luke is using them together to emphasize that the people could not understand what was happening. If it would be clearer for your readers, you could express the emphasis with a single phrase.",
    "alternateTranslations": [
      "they were all very perplexed"
    ]
  },
  {
    "type_of_translation_issue": "duphemism",
    "SupportReference": "rc://*/ta/man/translate/figs-euphemism",
    "BibleRef": "Luke 1:34",
    "BibleVerse": "But Mary said to the angel, “How will this be, since I have not known a man?”",
    "VerseSnippet": "I have not known a man",
    "translationNote": "Mary is using a polite expression to say that she has never had sexual relations with a man. If this would be misunderstood in your language, use your own polite way of referring to this or use plain language.",
    "alternateTranslations": [
      "I have never slept with a man",
      "I have never had sexual relations with a man"
    ]
  },
  {
    "type_of_translation_issue": "duphemism",
    "SupportReference": "rc://*/ta/man/translate/figs-euphemism",
    "BibleRef": "Acts 7:60",
    "BibleVerse": "But having put down {his} knees, he cried out with a loud voice, “Lord, do not hold this sin against them.” And having said this, he fell asleep.",
    "VerseSnippet": "he fell asleep",
    "translationNote": "Luke is describing the death of Stephen when he says **he fell asleep**. This is a polite way of referring to something unpleasant. If this would be misunderstood in your language, use your own polite way of referring to this or use plain language.",
    "alternateTranslations": [
      "he passed away",
      "he died"
    ]
  },
  {
    "type_of_translation_issue": "hendiadys",
    "SupportReference": "rc://*/ta/man/translate/figs-hendiadys",
    "BibleRef": "Judges 4:20",
    "BibleVerse": "And he said to her, “Stand {at} the entrance of the tent, and it shall be, if anyone comes and asks you and says, ‘Is there anyone here?’ then you shall say ‘No one.’”",
    "VerseSnippet": "asks you and says",
    "translationNote": "This phrase expresses a single idea by using two words connected with **and**. The word **asks** indicates that what this person **says** will be a question. If it would be clearer in your language, you can express the same meaning with only one of these words.",
    "alternateTranslations": [
      "asks you",
      "says to you"
    ]
  },
  {
    "type_of_translation_issue": "hendiadys",
    "SupportReference": "rc://*/ta/man/translate/figs-hendiadys",
    "BibleRef": "Job 26:11",
    "BibleVerse": "The pillars of the heavens tremble and marvel at his rebuke.",
    "VerseSnippet": "tremble and marvel",
    "translationNote": "This phrase expresses a single idea by using two words connected with **and**. The word **marvel**, a reference to being astonished by the power of God, tells why the pillars of the heavens **tremble**. If it would be more natural in your language, you could express this meaning with an equivalent phrase that does not use “and.”",
    "alternateTranslations": [
      "shake with fear"
    ]
  },
  {
    "type_of_translation_issue": "hyperbole",
    "SupportReference": "rc://*/ta/man/translate/figs-hyperbole",
    "BibleRef": "Esther 1:17",
    "BibleVerse": "For the matter of the queen will go out to all the women in order to make their husbands despised in their eyes when they say, ‘The king Ahasuerus said to bring Vashti the queen before his face, but she did not come.’",
    "VerseSnippet": "all the women",
    "translationNote": "To emphasize his point, Memukan makes an overstatement and says that **all the women** in the empire will hear about Queen Vashti refusing to obey King Ahasuerus.",
    "alternateTranslations": [
      "women all over the empire"
    ]
  },
  {
    "type_of_translation_issue": "hyperbole",
    "SupportReference": "rc://*/ta/man/translate/figs-hyperbole",
    "BibleRef": "Luke 5:17",
    "BibleVerse": "And it happened on one of those days that he was teaching, and there were Pharisees and law teachers sitting there who had come from every village of Galilee and Judea and from Jerusalem, and power of the Lord was upon him to heal.",
    "VerseSnippet": "from every village of Galilee and Judea",
    "translationNote": "Luke is making a generalization for emphasis. He says **every** in order to emphasize from how many different villages these religious leaders came.",
    "alternateTranslations": [
      "from villages throughout Galilee and Judea"
    ]
  },
  {
    "type_of_translation_issue": "idiom",
    "SupportReference": "rc://*/ta/man/translate/figs-idiom",
    "BibleRef": "Judges 9:17",
    "BibleVerse": "that my father fought on your behalf, and threw aside his life even out front, when he delivered you out of the hand of Midian,",
    "VerseSnippet": "and threw his life in front",
    "translationNote": "Jotham is using a common expression that means that Gideon risked his life by leading the armies of Israel into battle against the Midianites. Your language may have a comparable expression that you can use in your translation. You could also state the meaning plainly.",
    "alternateTranslations": [
      "and put his life on the line",
      "and risked his life"
    ]
  },
  {
    "type_of_translation_issue": "idiom",
    "SupportReference": "rc://*/ta/man/translate/figs-idiom",
    "BibleRef": "Acts 17:20",
    "BibleVerse": "For you are bringing some startling things into our ears. Therefore, we wish to know what these things want to be.”",
    "VerseSnippet": "what these things want to be",
    "translationNote": "The philosophers are using common expression whose meaning comes from the phrase taken as a whole rather than from the words understood individually. Your language may have a similar expression that you could use in your translation. You could also state the meaning plainly.",
    "alternateTranslations": [
      "what this is all about",
      "what these things mean"
    ]
  },
  {
    "type_of_translation_issue": "irony",
    "SupportReference": "rc://*/ta/man/translate/figs-irony",
    "BibleRef": "Job 12:2",
    "BibleVerse": "“Truly, then, you are the people, and wisdom will die with you",
    "VerseSnippet": "Truly, then, you are the people, and wisdom will die with you",
    "translationNote": "For emphasis, Job is saying the opposite of what he means. If a speaker of your language would not do this, in your translation you could indicate what Job actually means.",
    "alternateTranslations": [
      "You are speaking as if you were the people and as if wisdom would die with you, but that is not true"
    ]
  },
  {
    "type_of_translation_issue": "irony",
    "SupportReference": "rc://*/ta/man/translate/figs-irony",
    "BibleRef": "Luke 9:13",
    "BibleVerse": "But he said to them, “You give them to eat.” But they said, “There are not more than five loaves and two fish with us—unless we go buy food for all these people.”",
    "VerseSnippet": "unless we go buy food for all these people",
    "translationNote": "The disciples are not making a serious suggestion here. They actually mean to communicate emphatically the opposite of the literal meaning of their words.",
    "alternateTranslations": [
      "and we certainly cannot go and buy food for all these people"
    ]
  },
  {
    "type_of_translation_issue": "litany",
    "SupportReference": "rc://*/ta/man/translate/figs-litany",
    "BibleRef": "Obadiah 1:12",
    "BibleVerse": "But you should not have looked on the day of your brother, on the day of his misfortune. And you should not have rejoiced over the sons of Judah in the day of their perishing. And you should not have made your mouth great in a day of distress.",
    "VerseSnippet": "But you should not have looked & And you should not have rejoiced & And you should not have made",
    "translationNote": "Yahweh uses a repetitive series of sentences in verses 12–14 to show how badly the people of Edom have treated the people of Judah. This repetitive style of speaking or writing is called a “litany.” This is a list of the charges against the people of Edom. Yahweh goes on to say in verses 15 and 16 that he has found them guilty of all of these charges and that he will punish them. Use a form in your language that someone would use to list things that someone has done wrong."
  },
  {
    "type_of_translation_issue": "litany",
    "SupportReference": "rc://*/ta/man/translate/figs-litany",
    "BibleRef": "Revelation 22:11",
    "BibleVerse": "Let the one being unrighteous still be unrighteous, and let the filthy one still be filthy, and let the righteous one still do righteousness, and let the holy one still be holy.”",
    "VerseSnippet": "Let the one being unrighteous still be unrighteous, and let the filthy one still be filthy, and let the righteous one still do righteousness, and let the holy one still be holy",
    "translationNote": "In this verse, the angel is using a series of similar phrases in order to emphasize the idea that the phrases express. Try to translate each of these phrases in such a way as to show their similarity. You may also wish to summarize the idea behind the phrases beforehand, if that would be helpful to your readers.",
    "alternateTranslations": [
      "The time is so near that it is too late for people to change the way they are living. So let the one being unrighteous still be unrighteous, and let the filthy one still be filthy, and let the righteous one still do righteousness, and let the holy one still be holy"
    ]
  },
  {
    "type_of_translation_issue": "litotes",
    "SupportReference": "rc://*/ta/man/translate/figs-litotes",
    "BibleRef": "Job 39:24",
    "BibleVerse": "With shaking and rage it swallows the ground, and it does not stand still when {there is} the sound of the horn",
    "VerseSnippet": "and it does not stand still",
    "translationNote": "Yahweh is expressing a positive meaning by using a negative word together with a term that is the opposite of his intended meaning. If it would be clearer in your language, you could state the meaning plainly.",
    "alternateTranslations": [
      "and it charges forward"
    ]
  },
  {
    "type_of_translation_issue": "litotes",
    "SupportReference": "rc://*/ta/man/translate/figs-litotes",
    "BibleRef": "Acts 19:11",
    "BibleVerse": "And God was doing not ordinary miracles by the hands of Paul,",
    "VerseSnippet": "not ordinary",
    "translationNote": "Luke is expressing a positive meaning by using a negative word together with a term that is the opposite of the intended meaning. If it would be clearer in your language, you could state the meaning plainly.",
    "alternateTranslations": [
      "extraordinary"
    ]
  },
  {
    "type_of_translation_issue": "merism",
    "SupportReference": "rc://*/ta/man/translate/figs-merism",
    "BibleRef": "Job 3:19",
    "BibleVerse": "Small and great {are} there the same, and a servant {is} free from his master.",
    "VerseSnippet": "Small and great are there",
    "translationNote": "Job is using two extremes of people, **Small** and **great**, to mean them and everyone in between. If it would be helpful in your language, you could use an equivalent expression or plain language.",
    "alternateTranslations": [
      "People of every kind are there"
    ]
  },
  {
    "type_of_translation_issue": "merism",
    "SupportReference": "rc://*/ta/man/translate/figs-merism",
    "BibleRef": "Luke 8:34",
    "BibleVerse": "And having seen what had happened, the ones tending the pigs ran away and reported it in the city and in the countryside.",
    "VerseSnippet": "in the city and in the countryside",
    "translationNote": "Luke is referring to a whole region by naming the two constituent parts of it.",
    "alternateTranslations": [
      "throughout the whole area"
    ]
  },
  {
    "type_of_translation_issue": "metaphor",
    "SupportReference": "rc://*/ta/man/translate/figs-metaphor",
    "BibleRef": "Job 4:8",
    "BibleVerse": "According to what I have seen, the ones plowing misery and sowing trouble reap it.",
    "VerseSnippet": "the ones plowing misery and sowing trouble reap it",
    "translationNote": "Eliphaz is speaking as if people could literally plow **misery**, sow **trouble**, and **reap** those things. If it would be clearer in your language, you could state the meaning plainly.",
    "alternateTranslations": [
      "those who do wicked things and cause trouble for others will experience trouble themselves"
    ]
  },
  {
    "type_of_translation_issue": "metaphor",
    "SupportReference": "rc://*/ta/man/translate/figs-metaphor",
    "BibleRef": "2 Timothy 2:3",
    "BibleVerse": "Suffer together as a good soldier of Jesus Christ.",
    "VerseSnippet": "as a good soldier of Jesus Christ",
    "translationNote": "Here Paul speaks as if Timothy were a soldier who fights for and serves Jesus Christ. If it would be helpful in your language, you could express the idea as a comparison or state the meaning plainly.",
    "alternateTranslations": [
      "as if you were a good soldier and Jesus Christ were your commander",
      "as someone who faithfully serves Jesus Christ"
    ]
  },
  {
    "type_of_translation_issue": "metonymy",
    "SupportReference": "rc://*/ta/man/translate/figs-metonymy",
    "BibleRef": "Judges 5:30",
    "BibleVerse": "‘Are they not finding, {are} they {not} dividing spoil, a maiden, two maidens to the head of a warrior, spoil of dyed fabrics for Sisera, spoil of dyed fabrics {and} embroidery, dyed fabric {and} two embroideries for the necks of the spoil?’",
    "VerseSnippet": "for the necks of the spoil",
    "translationNote": "Sisera’s mother is using the term **spoil** by association to mean the soldiers who are collecting this plunder after the battle.",
    "alternateTranslations": [
      "for the necks of the soldiers collecting this plunder"
    ]
  },
  {
    "type_of_translation_issue": "metonymy",
    "SupportReference": "rc://*/ta/man/translate/figs-metonymy",
    "BibleRef": "Job 7:15",
    "BibleVerse": "and my soul chooses strangling, death, rather than my bones.",
    "VerseSnippet": "rather than my bones",
    "translationNote": "Job is using the term **bones** to mean life, by association with the way people are supported by their bones as they live on earth. If it would be helpful in your language, you could state the meaning plainly.",
    "alternateTranslations": [
      "rather than life",
      "rather than continuing to live"
    ]
  },
  {
    "type_of_translation_issue": "parallelism",
    "SupportReference": "rc://*/ta/man/translate/figs-parallelism",
    "BibleRef": "Esther 3:2",
    "BibleVerse": "And all the servants of the king who were at the gate of the king were bowing down and prostrating themselves to Haman, for thus the king had commanded concerning him. But Mordecai would neither bow down nor would he prostrate himself.",
    "VerseSnippet": "But Mordecai would neither bow down, nor would he prostrate himself.",
    "translationNote": "These two phrases mean basically the same thing. The repetition is used to emphasize how serious an offense this was against the king’s command and how much determination it took for Mordecai to remain standing. If it would be clearer in your language, you could combine these phrases and express the emphasis in another way.",
    "alternateTranslations": [
      "But Mordecai persistently refused to bow down to Haman"
    ]
  },
  {
    "type_of_translation_issue": "parallelism",
    "SupportReference": "rc://*/ta/man/translate/figs-parallelism",
    "BibleRef": "Acts 1:20",
    "BibleVerse": "“For it is written in the book of Psalms, ‘Let his habitation become desolate, and let not one dwelling be in it,’ and ‘Let another take his overseership.’",
    "VerseSnippet": "Let his habitation become desolate, and let not one dwelling be in it",
    "translationNote": "These two phrases mean basically the same thing. The second emphasizes the meaning of the first by repeating the same idea with different words. Hebrew poetry was based on this kind of repetition, and it would be good to show this to your readers by including both phrases in your translation rather than combining them. However, if this might be unclear in your language, you could connect the phrases with a word other than **and** in order to show that the second phrase is repeating the first one, not saying something additional. Alternatively, you could combine the phrases and express the emphasis in another way.",
    "alternateTranslations": [
      "Let his habitation be made desolate, yes, let no one dwell in it",
      "Let his habitation be made completely desolate"
    ]
  },
  {
    "type_of_translation_issue": "personification",
    "SupportReference": "rc://*/ta/man/translate/figs-personification",
    "BibleRef": "Judges 3:11",
    "BibleVerse": "And the land rested 40 years. Then Othniel the son of Kenaz died.",
    "VerseSnippet": "And the land rested 40 years",
    "translationNote": "The author is speaking as if the **land** on which the Israelites lived were a living thing that **rested** after a foreign occupier was driven away. If it would be clearer in your language, you could state the meaning plainly.",
    "alternateTranslations": [
      "And there were no more wars for 40 years"
    ]
  },
  {
    "type_of_translation_issue": "personification",
    "SupportReference": "rc://*/ta/man/translate/figs-personification",
    "BibleRef": "Acts 21:3",
    "BibleVerse": "And having sighted Cyprus and having left it behind on the port side, we sailed to Syria and came down to Tyre, for there the ship was unloading {its} cargo.",
    "VerseSnippet": "the ship was unloading {its} cargo",
    "translationNote": "Luke is speaking of this **ship** as if it were a living thing that would be **unloading** its own **cargo**. Luke means that the crew of this ship would be doing the unloading. If it would be helpful in your language, you could state that meaning plainly.",
    "alternateTranslations": [
      "the ship’s crew was to unload its cargo"
    ]
  },
  {
    "type_of_translation_issue": "predictive past",
    "SupportReference": "rc://*/ta/man/translate/figs-pastforfuture",
    "BibleRef": "Judges 7:9",
    "BibleVerse": "Now it happened during that night that Yahweh said to him, “Arise! Go down into the camp, for I have given it into your hand.",
    "VerseSnippet": "I have given it into your hand",
    "translationNote": "Yahweh is using the past tense to describe something that is going to happen in the future. He is doing this to show that the event will certainly happen. If it would be clearer in your language, you could use the future tense in your translation and express the emphasis in another way.",
    "alternateTranslations": [
      "I will certainly give it into your hand"
    ]
  },
  {
    "type_of_translation_issue": "predictive past",
    "SupportReference": "rc://*/ta/man/translate/figs-pastforfuture",
    "BibleRef": "Isaiah 5:13",
    "BibleVerse": "Therefore, my people have gone into captivity for lack of understanding, and its honorable people are hungry, and its parched multitude is thirsty.",
    "VerseSnippet": "my people have gone into captivity",
    "translationNote": "Yahweh is using the past tense to describe something that is going to happen in the future. He is doing this to show that the event will certainly happen. If it would be clearer in your language, you could use the future tense in your translation and express the emphasis in another way.",
    "alternateTranslations": [
      "my people will certainly go into captivity"
    ]
  },
  {
    "type_of_translation_issue": "rhetorical question",
    "SupportReference": "rc://*/ta/man/translate/figs-rquestion",
    "BibleRef": "Luke 10:40",
    "BibleVerse": "But Martha was distracted with much service, and coming up, she said, “Lord, are you not concerned that my sister has left me alone to serve? Therefore, speak to her so that she might help me.”",
    "VerseSnippet": "Lord, are you not concerned that my sister has left me alone to serve?",
    "translationNote": "Martha is complaining that Jesus is allowing Mary to sit listening to him when there is so much work to do. Martha respects the Lord, so she uses a rhetorical question to make her complaint more polite. If it would be helpful in your language, you could translate her words as a statement.",
    "alternateTranslations": [
      "Lord, it seems as if you do not care that my sister has left me alone to serve."
    ]
  },
  {
    "type_of_translation_issue": "rhetorical question",
    "SupportReference": "rc://*/ta/man/translate/figs-rquestion",
    "BibleRef": "Revelation 17:7",
    "BibleVerse": "But the angel said to me, “Why are you wondering? I will tell to you the mystery of the woman and of the beast carrying her having the seven heads and the ten horns.",
    "VerseSnippet": "Why are you wondering?",
    "translationNote": "The angel is using the question form for emphasis. If you would not use the question form for this purpose in your language, you could translate this as a statement or as an exclamation.",
    "alternateTranslations": [
      "You do not need to wonder!"
    ]
  },
  {
    "type_of_translation_issue": "simile",
    "SupportReference": "rc://*/ta/man/translate/figs-simile",
    "BibleRef": "Judges 7:12",
    "BibleVerse": "Now Midian and Amalek and all of the sons of the east were lying in the valley like the locust in multitude. And to their camels there was not a number, like the sand that {is} along the edge of the sea in multitude.",
    "VerseSnippet": "like the locust in multitude",
    "translationNote": "The point of this comparison is that just as a **locust** swarm is very great **in multitude**, that is, extremely numerous, so this combined army had a very great number of soldiers. If it would be helpful in your language, you could make this point explicitly.",
    "alternateTranslations": [
      "in huge numbers, such as in a swarm of locusts"
    ]
  },
  {
    "type_of_translation_issue": "simile",
    "SupportReference": "rc://*/ta/man/translate/figs-simile",
    "BibleRef": "Luke 17:6",
    "BibleVerse": "So the Lord said, “If you had faith like a mustard seed, you would say to this mulberry tree, ‘Be uprooted, and be planted in the sea,’ and it would listen to you.",
    "VerseSnippet": "faith like a mustard seed",
    "translationNote": "A **mustard seed** is a very small seed, and so Jesus is using this comparison to mean a very small amount of faith.",
    "alternateTranslations": [
      "even a tiny amount of faith"
    ]
  },
  {
    "type_of_translation_issue": "synecdoche",
    "SupportReference": "rc://*/ta/man/translate/figs-synecdoche",
    "BibleRef": "Luke 9:3",
    "BibleVerse": "And he said to them, “Take nothing for the road—neither staff, nor bag, nor bread, nor silver—nor have two tunics.",
    "VerseSnippet": "bread",
    "translationNote": "Jesus is using one kind of food, **bread**, to represent food in general.",
    "alternateTranslations": [
      "food"
    ]
  },
  {
    "type_of_translation_issue": "synecdoche",
    "SupportReference": "rc://*/ta/man/translate/figs-synecdoche",
    "BibleRef": "Acts 15:7",
    "BibleVerse": "And much debate having happened, Peter, arising, said to them,",
    "VerseSnippet": "“Men, brothers, you know that from original days God chose among you: By my mouth the Gentiles would hear the word of the gospel and believe.",
    "translationNote": "By my mouth",
    "alternateTranslations": [
      "Peter is using one part of himself, his **mouth**, to represent all of himself in the act of speaking. If it would be helpful in your language, you could use an equivalent expression from your culture or plain language."
    ]
  },
  {
    "type_of_translation_issue": "abstract nouns",
    "SupportReference": "rc://*/ta/man/translate/figs-abstractnouns",
    "BibleRef": "Acts 2:26",
    "BibleVerse": "Because of this, my heart was glad and my tongue exulted, and indeed my flesh will also dwell in hope.",
    "VerseSnippet": "dwell in hope",
    "translationNote": "If your language does not use an abstract noun for the idea behind the word **hope**, you could express the same idea in another way.",
    "alternateTranslations": [
      "live hopefully"
    ]
  },
  {
    "type_of_translation_issue": "abstract nouns",
    "SupportReference": "rc://*/ta/man/translate/figs-abstractnouns",
    "BibleRef": "Nehemiah 9:36",
    "BibleVerse": "Behold us today; we are servants. And the land that you gave to our fathers, to eat its fruit and its goodness; behold us, we are servants in it!",
    "VerseSnippet": "and its goodness",
    "translationNote": "If your language does not use an abstract noun for the idea behind the word **goodness**, you could express the same idea in another way.",
    "alternateTranslations": [
      "and the good things that grow in it"
    ]
  },
  {
    "type_of_translation_issue": "passive verbal forms (active-passive)",
    "SupportReference": "rc://*/ta/man/translate/figs-activepassive",
    "BibleRef": "Luke 24:34",
    "BibleVerse": "saying, “Truly the Lord has been raised, and he has been seen by Simon!”",
    "VerseSnippet": "and he has been seen by Simon",
    "translationNote": "If your language does not use this passive form, you could express the idea in active form or in another way that is natural in your language.",
    "alternateTranslations": [
      "and Simon has seen him"
    ]
  },
  {
    "type_of_translation_issue": "passive verbal forms (active-passive)",
    "SupportReference": "rc://*/ta/man/translate/figs-activepassive",
    "BibleRef": "Esther 2:1",
    "BibleVerse": "After these things, when the rage of the king Ahasuerus subsided, he remembered Vashti and what she had done, and what had been decided concerning her.",
    "VerseSnippet": "what had been decided",
    "translationNote": "If your language does not use this passive form, you could express the idea in active form or in another way that is natural in your language.",
    "alternateTranslations": [
      "what he had decided"
    ]
  },
  {
    "type_of_translation_issue": "collective nouns",
    "SupportReference": "rc://*/ta/man/translate/grammar-collectivenouns",
    "BibleRef": "Acts 4:24",
    "BibleVerse": "And having heard, they raised their voice unanimously to God and said, “Lord, you {are} the one having made the heaven and the earth and the sea and all that {is} in them,",
    "VerseSnippet": "their voice"
  },
  {
    "type_of_translation_issue": "Since Luke is referring to a group of people, it might be more natural in your language to use the plural form of **voice**.",
    "SupportReference": "their voices"
  },
  {
    "type_of_translation_issue": "collective nouns",
    "SupportReference": "rc://*/ta/man/translate/grammar-collectivenouns",
    "BibleRef": "Exodus 8:22",
    "BibleVerse": "And in that day, I will distinguish the land of Goshen, on which my people dwell, so that the swarm will not be there, in order that you may know that I am Yahweh in the middle of the land.",
    "VerseSnippet": "the swarm",
    "translationNote": "Here, **the swarm** is a collective singular noun that refers to a great number of flying, biting insects traveling in a group. If your language does not use singular nouns in that way, you can use a different expression.",
    "alternateTranslations": [
      "swarms of flies"
    ]
  },
  {
    "type_of_translation_issue": "distinguishing versus informing or reminding (restrictive vs. non-restrictive relative clauses)",
    "SupportReference": "rc://*/ta/man/translate/figs-distinguish",
    "BibleRef": "Leviticus 15:31",
    "BibleVerse": "And you shall hold back the sons of Israel from their uncleanness, and they will not die by their uncleanness, by their defiling my Dwelling, which is in their midst.",
    "VerseSnippet": "my Dwelling, which is in their midst",
    "translationNote": "Yahweh is not distinguishing this **Dwelling** in the **midst** of the Israelites from another Dwelling that in not in their midst. Yahweh is reminding them about the location of his Dwelling with them. Be sure that this is clear in your translation.",
    "alternateTranslations": [
      "my Dwelling. After all, it is in their midst"
    ]
  },
  {
    "type_of_translation_issue": "distinguishing versus informing or reminding (restrictive vs. non-restrictive relative clauses)",
    "SupportReference": "rc://*/ta/man/translate/figs-distinguish",
    "BibleRef": "Psalm 31:6",
    "BibleVerse": "I hate those who serve worthless idols, but I trust in Yahweh.",
    "VerseSnippet": "worthless idols",
    "translationNote": "David is not distinguishing between certain **idols** that are **worthless** and other idols that are not worthless. Be sure that this is clear in your translation.",
    "alternateTranslations": [
      "idols, which are worthless"
    ]
  },
  {
    "type_of_translation_issue": "double negatives",
    "SupportReference": "rc://*/ta/man/translate/figs-doublenegatives",
    "BibleRef": "Hebrews 9:7",
    "BibleVerse": "but into the second {tent}, once {in} the year only the high priest {enters}, {and} not without blood that he offers on behalf of himself and of the unintentional sins of the people.",
    "VerseSnippet": "not without blood",
    "translationNote": "If it would be clearer in your language, you could use a positive expression to convey the emphasis of this double negative that consists of the two negative words **not** and **without**.",
    "alternateTranslations": [
      "always with blood"
    ]
  },
  {
    "type_of_translation_issue": "double negatives",
    "SupportReference": "rc://*/ta/man/translate/figs-doublenegatives",
    "BibleRef": "Job 5:17",
    "BibleVerse": "Behold, blessed is the man God corrects, and the chastening of the Almighty do not despise.",
    "VerseSnippet": "do not despise",
    "translationNote": "If it would be clearer in your language, you could use a positive expression to translate this double negative that consists of the negative particle **not** and the negative verb **despise**.",
    "alternateTranslations": [
      "appreciate"
    ]
  },
  {
    "type_of_translation_issue": "ellipsis",
    "SupportReference": "rc://*/ta/man/translate/figs-ellipsis",
    "BibleRef": "Judges 7:5",
    "BibleVerse": "So he brought the people down to the water, and Yahweh said to Gideon, “Anyone who laps with his tongue from the water as that a dog laps, you shall set him apart, and anyone who kneels upon his knees to drink.”",
    "VerseSnippet": "and anyone who kneels upon his knees to drink",
    "translationNote": "Yahweh is leaving out some of the words that in many languages a sentence would need in order to be complete. You can supply these words from the context if that would be clearer in your language. Alternate translation: “and you shall put in a different group anyone who kneels upon his knees to drink”"
  },
  {
    "type_of_translation_issue": "ellipsis",
    "SupportReference": "rc://*/ta/man/translate/figs-ellipsis",
    "BibleRef": "1 John 2:19",
    "BibleVerse": "They went out from us, but they were not from us. For if they had been from us, they would have remained with us, but so that they would be made apparent that they are all not from us.",
    "VerseSnippet": "but so that they would be made apparent",
    "translationNote": "John is leaving out some of the words that a sentence would need in many languages in order to be complete. These words can be supplied from the previous sentence. Alternate translation: “but they went out from us so that they would be made apparent”"
  },
  {
    "type_of_translation_issue": "formal or informal “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-youformal",
    "BibleRef": "Genesis 3:19",
    "BibleVerse": "So Yahweh God called to the man and said to him, “Where {are} you?”",
    "VerseSnippet": "you",
    "translationNote": "God is in authority over the man, so languages that have formal and informal forms of **you** would probably use the informal form here.",
    "alternateTranslations": [
      "you (informal)"
    ]
  },
  {
    "type_of_translation_issue": "formal or informal “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-youformal",
    "BibleRef": "Luke 1:3",
    "BibleVerse": "it seemed good to me also, having carefully investigated everything from the beginning, to write for you an orderly account, most excellent Theophilus,",
    "VerseSnippet": "for you",
    "translationNote": "Luke calls Theophilus **most excellent**. This shows that Theophilus is a high official to whom Luke is showing great respect. Speakers of languages that have a formal form of “you” would probably use that form here.",
    "alternateTranslations": [
      "for you (formal)"
    ]
  },
  {
    "type_of_translation_issue": "dual “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-youdual",
    "BibleRef": "Luke 19:33",
    "BibleVerse": "And {as} they were untying the colt, the owners of it said to them, “Why are you untying the colt?”",
    "VerseSnippet": "are you untying",
    "translationNote": "The owners of the colt are speaking to the two disciples, so **you** would be dual if your language uses that form. Otherwise, it would be plural.",
    "alternateTranslations": [
      "are you (dual or plural) untying"
    ]
  },
  {
    "type_of_translation_issue": "dual “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-youdual",
    "BibleRef": "Esther 5:8",
    "BibleVerse": "if I have found favor in the eyes of the king, and if it is good to the king to grant my petition and to perform my request, let the king come with Haman to the banquet that I will make for them, and tomorrow I will do according to the word of the king.”",
    "VerseSnippet": "for them",
    "translationNote": "If you decide to translate this as “the banquet that I will make for you,” then the word “you” should be dual if your language uses that form, since it refers to the king and Haman. Otherwise, it should be plural.",
    "alternateTranslations": [
      "for you (dual or plural)"
    ]
  },
  {
    "type_of_translation_issue": "singular vs. plural “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-yousingular",
    "BibleRef": "Judges 7:7",
    "BibleVerse": "Then Yahweh said to Gideon, “With the 300 men, the ones lapping, I will save you and I will give Midian into your hand. But all the people may go, a man to his place.”",
    "VerseSnippet": "you & into your hand",
    "translationNote": "The word **you** is plural because Yahweh means all of the Israelites. The word **your** is singular because Yahweh means Gideon. Use those forms in your translation if your language marks that distinction.",
    "alternateTranslations": [
      "you Israelites … into your hand"
    ]
  },
  {
    "type_of_translation_issue": "singular vs. plural “you”",
    "SupportReference": "rc://*/ta/man/translate/figs-yousingular",
    "BibleRef": "1 Timothy 6:21",
    "BibleVerse": "which some, professing, have missed the mark concerning the faith. Grace {be} with you.",
    "VerseSnippet": "you",
    "translationNote": "Because Paul is giving this blessing to Timothy and all the believers who are with him, this is the one place in the letter where **you** is plural.",
    "alternateTranslations": [
      "you (plural)"
    ]
  },
  {
    "type_of_translation_issue": "generic nouns",
    "SupportReference": "rc://*/ta/man/translate/figs-genericnoun",
    "BibleRef": "Job 20:6",
    "BibleVerse": "Though his height rises to the skies and his head reaches to the cloud,",
    "VerseSnippet": "to the cloud",
    "translationNote": "Zophar is not referring to a specific **cloud**. He means the many clouds that appear in the sky. It may be more natural in your language to express this meaning by using a plural form.",
    "alternateTranslations": [
      "to the clouds"
    ]
  },
  {
    "type_of_translation_issue": "generic nouns",
    "SupportReference": "rc://*/ta/man/translate/figs-genericnoun",
    "BibleRef": "Psalm 94:12",
    "BibleVerse": "Blessed is the man whom you instruct, Yahweh, and from your law you teach him.",
    "VerseSnippet": "the man & and from your law you teach him",
    "translationNote": "The psalmist is not referring to a particular **man** but to any person whom Yahweh instructs. It may be helpful to clarify this for your readers.",
    "alternateTranslations": [
      "anyone … yes, anyone whom you teach from your law"
    ]
  },
  {
    "type_of_translation_issue": "go and come",
    "SupportReference": "rc://*/ta/man/translate/figs-go",
    "BibleRef": "Judges 6:21",
    "BibleVerse": "Then the angel of Yahweh stretched out the end of the staff that {was} in his hand. And he touched upon the meat and upon the unleavened bread, and fire came up from the rock and consumed the meat and the unleavened bread. Then the angel of Yahweh went from his eyes.",
    "VerseSnippet": "and fire came up",
    "translationNote": "In a context such as this, your language might say “went” instead of **came**.",
    "alternateTranslations": [
      "and fire went up"
    ]
  },
  {
    "type_of_translation_issue": "go and come",
    "SupportReference": "rc://*/ta/man/translate/figs-go",
    "BibleRef": "Luke 9:3",
    "BibleVerse": "And he said to them, “Take nothing for the road—neither staff, nor bag, nor bread, nor silver—nor have two tunics.",
    "VerseSnippet": "Take",
    "translationNote": "In a context such as this, your language might say “Bring” instead of **Take**.",
    "alternateTranslations": [
      "Bring"
    ]
  },
  {
    "type_of_translation_issue": "nominal adjectives",
    "SupportReference": "rc://*/ta/man/translate/figs-nominaladj",
    "BibleRef": "Job 4:3",
    "BibleVerse": "Behold, you have instructed many, you have strengthened weak hands.",
    "VerseSnippet": "many",
    "translationNote": "Eliphaz is using the adjective **many** as a noun. Your language may use adjectives in the same way. If not, you can translate this word with an equivalent phrase.",
    "alternateTranslations": [
      "many people"
    ]
  },
  {
    "type_of_translation_issue": "nominal adjectives",
    "SupportReference": "rc://*/ta/man/translate/figs-nominaladj",
    "BibleRef": "Luke 5:32",
    "BibleVerse": "I did not come to call the righteous, but sinners to repentance.”",
    "VerseSnippet": "the righteous",
    "translationNote": "Jesus is using the adjective **righteous** as a noun to mean a certain kind of person. Your language may use adjectives in the same way. If not, you can translate this adjective with an equivalent phrase.",
    "alternateTranslations": [
      "righteous people"
    ]
  },
  {
    "type_of_translation_issue": "order of events",
    "SupportReference": "rc://*/ta/man/translate/figs-events",
    "BibleRef": "Job 29:18",
    "BibleVerse": "And I said, ‘I will expire in my nest, and I will multiply days like sand.",
    "VerseSnippet": "I will expire in my nest, and I will multiply days like sand",
    "translationNote": "Since Job would live a long life before expiring, it might be more natural to put the second phrase before the first one.",
    "alternateTranslations": [
      "I will multiply days like sand, and then I will expire in my nest"
    ]
  },
  {
    "type_of_translation_issue": "order of events",
    "SupportReference": "rc://*/ta/man/translate/figs-events",
    "BibleRef": "Revelation 5:2",
    "BibleVerse": "And I saw a mighty angel proclaiming in a loud voice, “Who {is} worthy to open the scroll and to break its seals?”",
    "VerseSnippet": "to open the scroll and to break its seals",
    "translationNote": "Since someone would need to break the **seals** in order to **open the scroll**, in your translation you may wish to relate these events in the order in which they would have to happen.",
    "alternateTranslations": [
      "to break the seals and open the scroll"
    ]
  },
  {
    "type_of_translation_issue": "possession",
    "SupportReference": "rc://*/ta/man/translate/figs-possession",
    "BibleRef": "Job 42:11",
    "BibleVerse": "And all of his brothers and all of his sisters and all of the ones knowing him before came to him, and they ate bread with him in his house. And they consoled him and comforted him for all of the troubles that Yahweh had brought upon him, and they each gave one kesitah to him and each {gave} one earring of gold.",
    "VerseSnippet": "earring of gold",
    "translationNote": "The author is using this possessive form to indicate that **gold** was the material used for making the **earring**. If it would be clearer in your language, you could use an adjective to show that one noun describes the other.",
    "alternateTranslations": [
      "golden earring"
    ]
  },
  {
    "type_of_translation_issue": "possession",
    "SupportReference": "rc://*/ta/man/translate/figs-possession",
    "BibleRef": "1 John 4:9",
    "BibleVerse": "In this the love of God appeared among us, that God sent his Son, the One and Only, into the world so that we might live through him.",
    "VerseSnippet": "the love of God",
    "translationNote": "John is using this possessive form to describe the **love** that **God** has for people rather than people’s love for God. It may be helpful to clarify this for your readers.",
    "alternateTranslations": [
      "God’s love for us"
    ]
  },
  {
    "type_of_translation_issue": "when masculine words include women (gender notations)",
    "SupportReference": "rc://*/ta/man/translate/figs-gendernotations",
    "BibleRef": "Job 14:21",
    "BibleVerse": "His sons achieve honor and he does not know, or they become insignificant and he does not perceive them.",
    "VerseSnippet": "His sons",
    "translationNote": "Here the masculine term **sons** has a generic sense that includes children of both genders. If it would be helpful to your readers, you could use language in your translation that would indicate this.",
    "alternateTranslations": [
      "His children",
      "His sons and daughters"
    ]
  },
  {
    "type_of_translation_issue": "when masculine words include women (gender notations)",
    "SupportReference": "rc://*/ta/man/translate/figs-gendernotations",
    "BibleRef": "Luke 6:31",
    "BibleVerse": "And as you desire that men would do to you, do the same to them.",
    "VerseSnippet": "men",
    "translationNote": "Here the masculine term **men** has a generic sense that includes both men and women. If it would be helpful to your readers, you could use language in your translation that is clearly inclusive of both men and women.",
    "alternateTranslations": [
      "people"
    ]
  },
  {
    "type_of_translation_issue": "first, second, or third person",
    "SupportReference": "rc://*/ta/man/translate/figs-123person",
    "BibleRef": "Esther 7:9",
    "BibleVerse": "And Harbona, one from the eunuchs before the face of the king, said, “Also, behold, the pole that Haman made for Mordecai, who spoke good for the king, is standing at the house of Haman 50 cubits high.” And the king said, “Hang him on it.”",
    "VerseSnippet": "the king",
    "translationNote": "Harbona is addressing the king in the third person as a way of showing respect. If it would be natural in your language, you could translate this with a respectful expression that uses the second person.",
    "alternateTranslations": [
      "you, O king"
    ]
  },
  {
    "type_of_translation_issue": "first, second, or third person",
    "SupportReference": "rc://*/ta/man/translate/figs-123person",
    "BibleRef": "Luke 5:24",
    "BibleVerse": "But in order that you may know that the Son of Man has authority on the earth to forgive sins,”—he said to the one that had been paralyzed—”I say to you, get up, and picking up your mat, go to your house.”",
    "VerseSnippet": "the Son of Man has",
    "translationNote": "Jesus is referring to himself in the third person. If it would be helpful in your language, you could translate this in the first person.",
    "alternateTranslations": [
      "I, the Son of Man, have"
    ]
  },
  {
    "type_of_translation_issue": "exclusive and inclusive “we”",
    "SupportReference": "rc://*/ta/man/translate/figs-exclusive",
    "BibleRef": "Judges 1:1",
    "BibleVerse": "And it happened, after the death of Joshua, that the sons of Israel asked of Yahweh, saying, “Who will go up for us against the Canaanite in the beginning, to fight against him?”",
    "VerseSnippet": "for us",
    "translationNote": "By **us**, the Israelites mean themselves but not Yahweh, to whom they are speaking, so use the exclusive form of that word in your translation if your language marks that distinction.",
    "alternateTranslations": [
      "for us (exclusive)"
    ]
  },
  {
    "type_of_translation_issue": "exclusive and inclusive “we”",
    "SupportReference": "rc://*/ta/man/translate/figs-exclusive",
    "BibleRef": "Acts 11:15",
    "BibleVerse": "But as I began to speak, the Holy Spirit fell on them, just as also on us in the beginning.",
    "VerseSnippet": "us",
    "translationNote": "Here Peter is using the word **us** to refer to all of the believers to whom he is speaking, not just to himself and the men who went to Caesarea with him, so use the inclusive form of that word if your language marks that distinction.",
    "alternateTranslations": [
      "us (inclusive)"
    ]
  },
  {
    "type_of_translation_issue": "singular pronouns that refer to groups",
    "SupportReference": "rc://*/ta/man/translate/figs-youcrowd",
    "BibleRef": "Matthew 5:39",
    "BibleVerse": "But I tell you not to resist the evil one. Instead, whoever strikes you on the right cheek, turn to him the other also.",
    "VerseSnippet": "you [2] & turn",
    "translationNote": "Jesus is speaking to many disciples and so the pronoun **you** is plural in the first sentence. But in the second sentence, he is addressing an individual situation, so the pronoun **you** and the imperative **turn** are singular. If those singular forms would not be natural in your language for someone who was speaking to a group of people, you could use plural forms in your translation.",
    "alternateTranslations": [
      "you (plural) … turn (plural)"
    ]
  },
  {
    "type_of_translation_issue": "singular pronouns that refer to groups",
    "SupportReference": "rc://*/ta/man/translate/figs-youcrowd",
    "BibleRef": "Exodus 20:2",
    "BibleVerse": "I am Yahweh your God, who brought you out from the land of Egypt, from the house of slavery.",
    "VerseSnippet": "your God & brought you out",
    "translationNote": "Here and throughout this section, Yahweh uses the singular form of **you**. However, the commandments applied to the whole Israelite community, so there is both a singular and a corporate aspect to them. You may need to choose between singular and plural if your language makes that distinction.",
    "alternateTranslations": [
      "your (plural) God … brought you (plural) out"
    ]
  },
  {
    "type_of_translation_issue": "reflexive pronouns",
    "SupportReference": "rc://*/ta/man/translate/figs-rpronouns",
    "BibleRef": "John 4:2",
    "BibleVerse": "although Jesus himself was not baptizing, but his disciples",
    "VerseSnippet": "Jesus himself was not baptizing",
    "translationNote": "John is using the pronoun **himself** to emphasize that Jesus was not the one who was baptizing. Use a way that is natural in your language to indicate this emphasis.",
    "alternateTranslations": [
      "Jesus was not the one who was baptizing"
    ]
  },
  {
    "type_of_translation_issue": "reflexive pronouns",
    "SupportReference": "rc://*/ta/man/translate/figs-rpronouns",
    "BibleRef": "Acts 8:13",
    "BibleVerse": "And Simon himself also believed and, having been baptized, he was continuing with Philip. And seeing great signs and works happening, he marveled.",
    "VerseSnippet": "Simon himself",
    "translationNote": "Luke uses the word **himself** to emphasize how significant it was that Simon, who had claimed to be an embodiment of God, had believed in Jesus as the Messiah whom God sent. Use a way that is natural in your language to indicate this significance.",
    "alternateTranslations": [
      "even Simon"
    ]
  },
  {
    "type_of_translation_issue": "pronouns - when to use them",
    "SupportReference": "rc://*/ta/man/translate/writing-pronouns",
    "BibleRef": "Acts 1:22",
    "BibleVerse": "beginning from the baptism of John until the day on which he was taken up from us—one of these {is} to become a witness with us of his resurrection.",
    "VerseSnippet": "he was taken up & of his resurrection",
    "translationNote": "The pronoun **he** refers to Jesus, not to John the Baptist. The pronoun **his** also refers to Jesus. For clarity, you may want to use the name Jesus instead of one or both of these pronouns.",
    "alternateTranslations": [
      "Jesus was taken up … of the resurrection of Jesus"
    ]
  },
  {
    "type_of_translation_issue": "pronouns - when to use them",
    "SupportReference": "rc://*/ta/man/translate/writing-pronouns",
    "BibleRef": "Judges 7:19",
    "BibleVerse": "So Gideon and the 100 men who {were} with him came to the edge of the camp, {at} the start of the middle watch. Stationing, they had just stationed the guards, and they blew on the shofars and they shattered the jars that {were} in their hand.",
    "VerseSnippet": "they had just stationed the guards, and they blew on the shofars",
    "translationNote": "The first instance of the pronoun **they** refers to the Midianites, while the second instance refers to Gideon and his men. It may be helpful to clarify this for your readers.",
    "alternateTranslations": [
      "the Midianites had just stationed the guards, and Gideon and his men blew on the shofars"
    ]
  }
]
"""
        )

        response1a = query_func(chapter_content, prompt=prompt1a, temp=0.8)
        print(f"\nResponse 1a: {response1a}")
        self.write_to_log()
        
        prompt2 = (
            f"You have been given a chapter from the Bible. Here is a list of some figures of speech from this chapter:\n{response1}\n\n"
            "I want you to double-check for each of the following specific figures of speech in the chapter: metaphor, simile, idiom, personification, metonymy, synecdoche, apostrophe, euphemism, hendiadys, litotes, merism, hyperbole.\n"
            "If you find more figures of speech, add them to the list.\n"
            "Also double-check the label provided for the figure of speech. Consider whether it is the best label for the text. Change it to another label if it is not the best label. You may still only use the labels provided to you.\n"
            "As your answer, provide the new list."
        )

        response2 = query_func(chapter_content, prompt=prompt2, temp=0.8)
        print(f"\nResponse 2: {response2}")
        self.write_to_log()

        prompt3 = (
            f"You have been given a chapter from the Bible. Here is a list of figures of speech in this chapter: {response2}\n\n"
            "\nFor each of these listed figures of speech, append a row of data to a TSV table. Each row must contain exactly 7 tab-separated values. Here is what a row should be like:"
            "chapter:verse\t\t\trc://*/ta/man/translate/figs-[figure_of_speech]\tquote from the verse that the alternate translation can replace\t1\tExplanation of the figure of speech along with an alternate translation that does not use the figure of speech\n\n"
            "Here are two examples:\n"
            "1:2			rc://*/ta/man/translate/figs-metaphor	 she will always stand to the face of the king	1	Here the servants speak of how the young woman will always serve the king as if she would **stand to the face of the king**. If it would be helpful in your language, you could use a comparable figure of speech or state the meaning plainly. Alternate translation: [she will always be ready to serve]\n"
            "1:37			rc://*/ta/man/translate/figs-metonymy   and may he make his throne greater than the throne of my lord the king David  1	Here, **throne** represents the rule or reign of the person who sits on the **throne**. If it would be helpful in your language, you could use an equivalent expression from your language or state the meaning plainly. Alternate translation: [and may he make his reign greater than the reign of my lord the king David] or [and may he make him a greater ruler than my lord the king David]\n"
            "Note - whenever you quote directly from the verse (in the Note column), you should enclose the quoted word or words in double asterisks, as in the above examples."
            "Important: be sure that your explanation fits the context as well as the label for the figure of speech."
        )

        response3 = query_func(chapter_content, prompt=prompt3, temp=0.3)
        print(f"\nResponse 3: {response3}")
        self.write_to_log()
        return response3

    def _read_tsv(self, file_path):
        verse_texts = []
        with open(file_path, 'r', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                verse_texts.append(row)
        return verse_texts

    def run(self):
        # Load verse texts from TSV
        verse_texts = self._read_tsv(self.verse_text)

        # Check the stage and limit verse_texts if in development stage
        if os.getenv('STAGE') == 'dev':
            max_verses = int(os.getenv('DEV_NUMBER_OF_VERSES'))
            verse_texts = verse_texts[:max_verses]

        # Organize verse texts by chapter
        chapters = {}
        for verse in verse_texts:
            reference = verse['Reference']
            if reference == '-':
                continue
            book_name, chapter_and_verse = reference.rsplit(' ', 1)
            chapter = f"{book_name} {chapter_and_verse.split(':')[0]}"
            if chapter not in chapters:
                chapters[chapter] = []
            chapters[chapter].append(verse)

        # Process each chapter for personification
        ai_data = []
        for chapter_key, verses in chapters.items():
            # Combine verses into chapter context
            chapter_content = "\n".join([f"{verse['Reference']} {verse['Verse']}" for verse in verses])
            response = self.__process_prompt(chapter_content)
            if response:
                ai_data.append(response.split('\n'))

        mod_ai_data = []
        for row_list in ai_data:
            for row in row_list:
                columns = row.split('\t')
                if len(columns) == 8:
                    row_dict = {
                        'Reference': columns[0],
                        'ID': columns[1],
                        'Tags': columns[2],
                        'SupportReference': columns[3],
                        'Quote': columns[4],
                        'Occurrence': columns[5],
                        'Note': columns[6],
                        'Snippet': columns[7]
                    }
                    row_dict['Snippet'] = row_dict['Snippet'].strip('.,:;“”‘’"!?')
                    row_dict['Reference'] = re.sub(r'\w+ ', '', row_dict['Reference'])
                    mod_ai_data.append(row_dict)

        rows = [[row['Reference'], row['ID'], row['Tags'], row['SupportReference'], row['Quote'], row['Occurrence'], row['Note'], row['Snippet']] for row in mod_ai_data]
        headers_transformed = ['Reference', 'ID', 'Tags', 'SupportReference', 'Quote', 'Occurrence', 'Note', 'Snippet']
        self._write_output(book_name, file='transformed_ai_figures_of_speech.tsv', headers=headers_transformed, data=rows)


if __name__ == "__main__":
    book_name = os.getenv("BOOK_NAME")

    figs_instance = Figs(book_name)
    figs_instance.run()
