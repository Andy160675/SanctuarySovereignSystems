import json
from agi.core.agency_metrics import compute_agency_vector
from agi.core.empathy_state_machine import EmpathyStateMachine


def main():
    a1 = {"grounded_options": 4, "counterfactual_quality": 0.7, "reality_contact": True}
    a2 = {"plan_detail": 0.8, "resources_available": 0.7, "capability_fit": 0.6, "timeline_realism": 0.6}
    a3 = {"internal_locus": 0.7, "values_alignment": 0.8, "narrative_coherence": 0.7, "non_substitution": 0.6}
    a4 = {"window_of_tolerance": 0.8, "coping_access": 0.7, "meaning_frame": 0.8, "volatility_risk": 0.2}

    vec = compute_agency_vector(a1,a2,a3,a4)
    sm = EmpathyStateMachine()
    state = sm.step(vec)
    print(json.dumps({"A": vec.__dict__, "Aggregate": vec.aggregate, "State": state}, indent=2))


if __name__ == "__main__":
    main()
