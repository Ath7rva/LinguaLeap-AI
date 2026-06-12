from datetime import datetime, timedelta


def schedule_sm2(repetition: int, interval_days: int, difficulty: float, quality: int):
    quality = max(0, min(5, quality))
    difficulty = max(1.3, difficulty + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    if quality < 3:
        repetition = 0
        interval_days = 1
    else:
        repetition += 1
        if repetition == 1:
            interval_days = 1
        elif repetition == 2:
            interval_days = 6
        else:
            interval_days = max(1, round(interval_days * difficulty))

    reviewed_at = datetime.utcnow()
    return {
        "repetition": repetition,
        "interval_days": interval_days,
        "difficulty": round(difficulty, 2),
        "last_quality": quality,
        "last_reviewed_at": reviewed_at,
        "next_review_at": reviewed_at + timedelta(days=interval_days),
    }
