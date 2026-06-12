LANGUAGES = [
    {
        "code": "hi",
        "short": "IN",
        "name": "Hindi",
        "native": "हिन्दी",
        "script": "Devanagari",
        "description": "Learn Hindi from English with script support, pronunciation hints, and beginner-friendly explanations.",
        "accent": "#61d400",
    },
    {
        "code": "de",
        "short": "DE",
        "name": "German",
        "native": "Deutsch",
        "script": "Latin",
        "description": "Build confident German with article guidance, sentence structure coaching, and practical dialogue.",
        "accent": "#ffd846",
    },
    {
        "code": "ja",
        "short": "JP",
        "name": "Japanese",
        "native": "日本語",
        "script": "Hiragana, Katakana and Kanji",
        "description": "Learn Japanese through native scripts, romaji support, cultural context, and everyday conversation.",
        "accent": "#65c9ef",
    },
]


def lesson(lesson_id, kind, title, xp, tags, objective, explanation, examples, vocabulary, prerequisite=None):
    return {
        "id": lesson_id,
        "kind": kind,
        "title": title,
        "xp": xp,
        "tags": tags,
        "objective": objective,
        "explanation": explanation,
        "examples": examples,
        "vocabulary": vocabulary,
        "review_terms": [{"term": item["term"], "translation": item["meaning"]} for item in vocabulary],
        "prerequisite": prerequisite,
        "complexity": "basic" if prerequisite is None else "intermediate",
    }


CURRICULUM = {
    "hi": [
        {
            "level": 1,
            "title": "Hindi Foundations",
            "description": "Meet Devanagari, greetings, and polite beginner expressions.",
            "lessons": [
                lesson(
                    "hi-foundations", "lesson", "Script and Greetings", 35,
                    ["Devanagari", "Greetings", "Pronunciation"],
                    "Recognize key vowel sounds and greet someone politely.",
                    "Hindi is commonly written in Devanagari. Each character maps closely to a sound. Namaste is a flexible respectful greeting.",
                    [
                        {"target": "नमस्ते", "romanization": "namaste", "meaning": "hello"},
                        {"target": "मैं ठीक हूँ।", "romanization": "main theek hoon", "meaning": "I am fine."},
                    ],
                    [
                        {"term": "नमस्ते", "romanization": "namaste", "meaning": "hello"},
                        {"term": "धन्यवाद", "romanization": "dhanyavaad", "meaning": "thank you"},
                    ],
                ),
                lesson(
                    "hi-foundations-practice", "practice", "Foundation Recall", 45,
                    ["Listening", "Speaking", "Recall"],
                    "Recall greetings without looking and answer a simple wellbeing question.",
                    "Use short retrieval attempts. Recall first, then compare with the example and correct pronunciation.",
                    [{"target": "आप कैसे हैं?", "romanization": "aap kaise hain?", "meaning": "How are you?"}],
                    [{"term": "ठीक", "romanization": "theek", "meaning": "fine"}],
                    "hi-foundations",
                ),
            ],
        },
        {
            "level": 2,
            "title": "Everyday Vocabulary",
            "description": "Build a practical word bank for food, objects, numbers, and places.",
            "lessons": [
                lesson(
                    "hi-vocabulary", "lesson", "Useful Everyday Words", 40,
                    ["Food", "Objects", "Recall"],
                    "Use high-frequency nouns in short identification sentences.",
                    "Hindi nouns have grammatical gender. Learn a noun together with a useful phrase instead of memorizing it alone.",
                    [{"target": "यह पानी है।", "romanization": "yah paani hai", "meaning": "This is water."}],
                    [
                        {"term": "पानी", "romanization": "paani", "meaning": "water"},
                        {"term": "रोटी", "romanization": "roti", "meaning": "bread"},
                        {"term": "किताब", "romanization": "kitaab", "meaning": "book"},
                    ],
                    "hi-foundations-practice",
                ),
                lesson(
                    "hi-vocabulary-practice", "practice", "Vocabulary Retrieval", 50,
                    ["Translation", "Matching", "Spaced review"],
                    "Translate and retrieve the level vocabulary from memory.",
                    "Mix recognition and free recall. Difficult words are added to the spaced-review queue.",
                    [{"target": "यह मेरी किताब है।", "romanization": "yah meri kitaab hai", "meaning": "This is my book."}],
                    [{"term": "मेरा / मेरी", "romanization": "mera / meri", "meaning": "my"}],
                    "hi-vocabulary",
                ),
            ],
        },
        {
            "level": 3,
            "title": "Conversation",
            "description": "Form useful sentences for introductions, travel, shopping, and food.",
            "lessons": [
                lesson(
                    "hi-conversation", "lesson", "Sentence Builder", 50,
                    ["Word order", "Questions", "Requests"],
                    "Build subject-object-verb sentences and polite requests.",
                    "Hindi typically places the verb near the end. Polite requests often use kripaya and a respectful verb form.",
                    [{"target": "कृपया मुझे पानी दीजिए।", "romanization": "kripaya mujhe paani dijiye", "meaning": "Please give me water."}],
                    [{"term": "कृपया", "romanization": "kripaya", "meaning": "please"}],
                    "hi-vocabulary-practice",
                ),
                lesson(
                    "hi-conversation-practice", "practice", "Real-world Dialogue", 60,
                    ["Roleplay", "Speaking", "Culture"],
                    "Complete a short introduction and cafe roleplay.",
                    "Practice one turn at a time. Prefer clear, polite language over translating English word-for-word.",
                    [{"target": "मेरा नाम आरव है।", "romanization": "mera naam Aarav hai", "meaning": "My name is Aarav."}],
                    [{"term": "नाम", "romanization": "naam", "meaning": "name"}],
                    "hi-conversation",
                ),
            ],
        },
    ],
    "de": [
        {
            "level": 1,
            "title": "German Foundations",
            "description": "Greetings, pronunciation, articles, and essential sentence patterns.",
            "lessons": [
                lesson(
                    "de-foundations", "lesson", "Greetings and Articles", 35,
                    ["Greetings", "Articles", "Sounds"],
                    "Greet someone and recognize der, die, and das.",
                    "German nouns are capitalized and learned with a grammatical article. Formal and informal greetings depend on context.",
                    [{"target": "Guten Tag!", "romanization": "GOO-ten tahk", "meaning": "Good day!"}],
                    [{"term": "Danke", "romanization": "DAHN-kuh", "meaning": "thank you"}],
                ),
                lesson(
                    "de-foundations-practice", "practice", "Foundation Recall", 45,
                    ["Listening", "Articles", "Recall"],
                    "Retrieve greetings and match common nouns with articles.",
                    "Say the complete noun phrase aloud, such as das Buch, to build article memory.",
                    [{"target": "Das ist ein Buch.", "romanization": "dahs ist ine bookh", "meaning": "That is a book."}],
                    [{"term": "das Buch", "romanization": "dahs bookh", "meaning": "the book"}],
                    "de-foundations",
                ),
            ],
        },
        {
            "level": 2,
            "title": "Daily Life",
            "description": "Talk about routines, people, places, and everyday needs.",
            "lessons": [
                lesson(
                    "de-daily", "lesson", "Daily Routine", 40,
                    ["Verbs", "Time", "Word order"],
                    "Describe a simple daily routine using present-tense verbs.",
                    "In a main clause, the conjugated verb normally occupies the second position, even when time comes first.",
                    [{"target": "Morgens lerne ich Deutsch.", "romanization": "MOR-gens LAIR-nuh ikh doytch", "meaning": "In the morning I study German."}],
                    [{"term": "lernen", "romanization": "LAIR-nen", "meaning": "to learn"}],
                    "de-foundations-practice",
                ),
                lesson(
                    "de-daily-practice", "practice", "Routine Dialogue", 50,
                    ["Dialogue", "Writing", "Recall"],
                    "Ask and answer two questions about a daily routine.",
                    "Keep the conjugated verb second and check subject-verb agreement after each answer.",
                    [{"target": "Wann arbeitest du?", "romanization": "vahn AR-bye-test doo", "meaning": "When do you work?"}],
                    [{"term": "wann", "romanization": "vahn", "meaning": "when"}],
                    "de-daily",
                ),
            ],
        },
        {
            "level": 3,
            "title": "Travel and Services",
            "description": "Ask for directions, order food, and handle simple travel situations.",
            "lessons": [
                lesson(
                    "de-travel", "lesson", "Travel Essentials", 50,
                    ["Directions", "Requests", "Culture"],
                    "Make polite requests and ask where something is.",
                    "Use ich möchte for a polite order and wo ist for a direct location question.",
                    [{"target": "Ich möchte einen Kaffee.", "romanization": "ikh MERKH-tuh EYE-nen KAH-fay", "meaning": "I would like a coffee."}],
                    [{"term": "Wo ist...?", "romanization": "voh ist", "meaning": "Where is...?"}],
                    "de-daily-practice",
                ),
                lesson(
                    "de-travel-practice", "practice", "Travel Roleplay", 60,
                    ["Roleplay", "Speaking", "Listening"],
                    "Complete a cafe order and station-direction roleplay.",
                    "Use complete polite phrases and listen for nouns that identify places.",
                    [{"target": "Wo ist der Bahnhof?", "romanization": "voh ist dair BAHN-hof", "meaning": "Where is the train station?"}],
                    [{"term": "der Bahnhof", "romanization": "dair BAHN-hof", "meaning": "the train station"}],
                    "de-travel",
                ),
            ],
        },
    ],
    "ja": [
        {
            "level": 1,
            "title": "Japanese Foundations",
            "description": "Begin with greetings, hiragana sounds, and respectful expressions.",
            "lessons": [
                lesson(
                    "ja-foundations", "lesson", "Greetings and Hiragana", 35,
                    ["Hiragana", "Greetings", "Culture"],
                    "Recognize basic hiragana sounds and use a daytime greeting.",
                    "Japanese uses multiple scripts. Hiragana represents syllable sounds; polite greetings change with time and social context.",
                    [{"target": "こんにちは", "romanization": "konnichiwa", "meaning": "hello / good afternoon"}],
                    [{"term": "ありがとう", "romanization": "arigatou", "meaning": "thank you"}],
                ),
                lesson(
                    "ja-foundations-practice", "practice", "Sound and Greeting Recall", 45,
                    ["Listening", "Romaji", "Recall"],
                    "Match greetings with context and recall them without romaji.",
                    "Use romaji as temporary support, then cover it and retrieve the Japanese script.",
                    [{"target": "おはようございます", "romanization": "ohayou gozaimasu", "meaning": "good morning"}],
                    [{"term": "こんばんは", "romanization": "konbanwa", "meaning": "good evening"}],
                    "ja-foundations",
                ),
            ],
        },
        {
            "level": 2,
            "title": "Useful Phrases",
            "description": "Build short sentences for introductions, food, and directions.",
            "lessons": [
                lesson(
                    "ja-phrases", "lesson", "Particles and Introductions", 40,
                    ["Particles", "Introductions", "Word order"],
                    "Introduce yourself using wa and desu.",
                    "The particle は marks the topic and is pronounced wa in this use. Desu gives the sentence a polite neutral ending.",
                    [{"target": "私はユキです。", "romanization": "watashi wa Yuki desu", "meaning": "I am Yuki."}],
                    [{"term": "私", "romanization": "watashi", "meaning": "I / me"}],
                    "ja-foundations-practice",
                ),
                lesson(
                    "ja-phrases-practice", "practice", "Introduction Dialogue", 50,
                    ["Dialogue", "Speaking", "Culture"],
                    "Exchange names and one simple personal detail.",
                    "Japanese often omits a subject when context is clear. Keep your first practice sentences explicit and polite.",
                    [{"target": "学生です。", "romanization": "gakusei desu", "meaning": "I am a student."}],
                    [{"term": "学生", "romanization": "gakusei", "meaning": "student"}],
                    "ja-phrases",
                ),
            ],
        },
        {
            "level": 3,
            "title": "Everyday Travel",
            "description": "Order food, ask locations, and understand common service phrases.",
            "lessons": [
                lesson(
                    "ja-travel", "lesson", "Requests and Locations", 50,
                    ["Requests", "Locations", "Politeness"],
                    "Ask where something is and make a simple request.",
                    "Use wa doko desu ka for locations and kudasai when requesting an item politely.",
                    [{"target": "駅はどこですか。", "romanization": "eki wa doko desu ka", "meaning": "Where is the station?"}],
                    [{"term": "ください", "romanization": "kudasai", "meaning": "please give me"}],
                    "ja-phrases-practice",
                ),
                lesson(
                    "ja-travel-practice", "practice", "Service Roleplay", 60,
                    ["Roleplay", "Listening", "Culture"],
                    "Complete a restaurant order and directions exchange.",
                    "Use polite endings and listen for location words before attempting a full translation.",
                    [{"target": "水をください。", "romanization": "mizu o kudasai", "meaning": "Water, please."}],
                    [{"term": "水", "romanization": "mizu", "meaning": "water"}],
                    "ja-travel",
                ),
            ],
        },
    ],
}


EXERCISES = {
    "hi": [
        {"id": "hi-mcq-hello", "type": "mcq", "prompt": "How do you say 'Hello'?", "options": ["नमस्ते", "धन्यवाद", "नहीं"], "answer": "नमस्ते", "skill": "vocabulary", "complexity": "basic"},
        {"id": "hi-fill-thanks", "type": "fill", "prompt": "Type the Hindi word for 'Thank you'.", "answer": "धन्यवाद", "skill": "writing", "complexity": "basic"},
        {"id": "hi-match-water", "type": "mcq", "prompt": "Which word means 'water'?", "options": ["रोटी", "पानी", "किताब"], "answer": "पानी", "skill": "vocabulary", "complexity": "basic"},
    ],
    "de": [
        {"id": "de-mcq-hello", "type": "mcq", "prompt": "How do you say 'Good day'?", "options": ["Guten Tag", "Danke", "Nein"], "answer": "Guten Tag", "skill": "vocabulary", "complexity": "basic"},
        {"id": "de-fill-thanks", "type": "fill", "prompt": "Type the German word for 'Thank you'.", "answer": "danke", "skill": "writing", "complexity": "basic"},
        {"id": "de-mcq-water", "type": "mcq", "prompt": "Which word means 'water'?", "options": ["Brot", "Wasser", "Buch"], "answer": "Wasser", "skill": "vocabulary", "complexity": "basic"},
    ],
    "ja": [
        {"id": "ja-mcq-hello", "type": "mcq", "prompt": "How do you say 'Hello'?", "options": ["こんにちは", "ありがとう", "いいえ"], "answer": "こんにちは", "skill": "vocabulary", "complexity": "basic"},
        {"id": "ja-fill-thanks", "type": "fill", "prompt": "Type the Japanese expression for 'Thank you'.", "answer": "ありがとう", "skill": "writing", "complexity": "basic"},
        {"id": "ja-mcq-water", "type": "mcq", "prompt": "Which word means 'water'?", "options": ["水", "本", "パン"], "answer": "水", "skill": "vocabulary", "complexity": "basic"},
    ],
}


def language_by_code(code):
    return next((language for language in LANGUAGES if language["code"] == code), LANGUAGES[0])


def find_lesson(lesson_id):
    for language_code, levels in CURRICULUM.items():
        for level in levels:
            for item in level["lessons"]:
                if item["id"] == lesson_id:
                    return language_code, level, item
    return None


def find_exercise(exercise_id):
    for language_code, exercises in EXERCISES.items():
        for exercise in exercises:
            if exercise["id"] == exercise_id:
                return language_code, exercise
    return None
