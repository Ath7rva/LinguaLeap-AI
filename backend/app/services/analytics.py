from collections import defaultdict
from statistics import mean

from app.models import Interaction, ReviewItem, User


def mean_or_zero(values):
    return round(mean(values), 1) if values else 0


def interaction_metrics(interactions):
    total = len(interactions)
    correct = sum(1 for item in interactions if item.correct)
    return {
        "n": total,
        "mean_score": mean_or_zero([item.score for item in interactions]),
        "accuracy": round(correct / total * 100, 1) if total else 0,
        "mean_engagement_seconds": mean_or_zero([item.engagement_seconds for item in interactions]),
        "mean_learning_gain": mean_or_zero([
            item.post_test_score - item.pre_test_score
            for item in interactions
            if item.pre_test_score is not None and item.post_test_score is not None
        ]),
    }


def grouped_metrics(interactions, field, allowed_values):
    return {
        value: interaction_metrics([item for item in interactions if getattr(item, field) == value])
        for value in allowed_values
    }


def observed_retention(interactions, review_items):
    review_scores = [
        item.last_quality * 20 for item in review_items if item.last_quality is not None
    ]
    exercise_scores = [
        item.score for item in interactions if item.interaction_type in {"exercise", "review"}
    ]
    observations = exercise_scores + review_scores
    if not observations:
        return []
    bucket_size = max(1, (len(observations) + 4) // 5)
    return [
        round(mean(observations[index:index + bucket_size]))
        for index in range(0, len(observations), bucket_size)
    ][:5]


def skill_metrics(interactions):
    grouped = defaultdict(list)
    for item in interactions:
        grouped[item.skill].append(item.score)
    return [{"skill": skill, "score": round(mean(scores)), "n": len(scores)} for skill, scores in grouped.items()]


def research_summary(users: list[User], interactions: list[Interaction]):
    consented = [user for user in users if user.research_consent]
    observed = [item for item in interactions if not item.is_simulated]
    simulated = [item for item in interactions if item.is_simulated]
    return {
        "total_users": len(users),
        "consented_participants": len(consented),
        "observed_interactions": len(observed),
        "simulated_interactions": len(simulated),
        "average_xp": round(mean([user.xp for user in users])) if users else 0,
    }
