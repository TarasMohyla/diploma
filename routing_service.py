from collections import defaultdict
from models import DiagnosisRule, Specialty, Symptom

DEFAULT_SPECIALTY_NAME = "Сімейний лікар"


def recommend_specialty(symptom_ids):
    """Return a tuple: (recommended Specialty, scores dict, selected symptom names).

    The algorithm does not make a medical diagnosis. It only chooses the most
    relevant specialty using transparent weighted rules.
    """
    symptom_ids = [int(s) for s in symptom_ids if str(s).isdigit()]
    symptoms = Symptom.query.filter(Symptom.id.in_(symptom_ids)).all() if symptom_ids else []
    symptom_names = [s.name for s in symptoms]

    scores = defaultdict(int)
    rules = DiagnosisRule.query.filter(DiagnosisRule.symptom_id.in_(symptom_ids)).all() if symptom_ids else []

    for rule in rules:
        scores[rule.specialty_id] += rule.weight

    if not scores:
        specialty = Specialty.query.filter_by(name=DEFAULT_SPECIALTY_NAME).first()
        return specialty, {}, symptom_names

    best_specialty_id = max(scores, key=scores.get)
    specialty = Specialty.query.get(best_specialty_id)

    named_scores = {}
    for specialty_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        item = Specialty.query.get(specialty_id)
        if item:
            named_scores[item.name] = score

    return specialty, named_scores, symptom_names
