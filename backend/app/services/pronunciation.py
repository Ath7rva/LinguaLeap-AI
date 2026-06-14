import re
from difflib import SequenceMatcher


def _tokens(text: str):
    return re.findall(r"[\w\u0900-\u097f\u3040-\u30ff\u4e00-\u9faf]+", text.casefold(), re.UNICODE)


def compare_words(target: str, transcript: str):
    expected = _tokens(target)
    heard = _tokens(transcript)
    matcher = SequenceMatcher(None, expected, heard)
    segments = []
    matched = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            matched += i2 - i1
            segments.extend({"word": word, "status": "matched"} for word in expected[i1:i2])
        elif tag == "replace":
            replacement = heard[j1:j2]
            for index, word in enumerate(expected[i1:i2]):
                segments.append({"word": word, "status": "substituted", "heard": replacement[index] if index < len(replacement) else ""})
            for word in replacement[len(expected[i1:i2]):]:
                segments.append({"word": word, "status": "extra"})
        elif tag == "delete":
            segments.extend({"word": word, "status": "missed"} for word in expected[i1:i2])
        else:
            segments.extend({"word": word, "status": "extra"} for word in heard[j1:j2])
    score = round((matched / max(len(expected), 1)) * 100)
    return {
        "score": score,
        "words": segments,
        "matched_words": matched,
        "expected_words": len(expected),
        "disclaimer": "This compares Whisper transcripts word by word; it is not a phoneme-level acoustic assessment.",
    }
