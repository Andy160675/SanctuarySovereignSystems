import random
from agi.core.agency_metrics import compute_agency_vector
from agi.core.empathy_state_machine import EmpathyStateMachine, StateContext

random.seed(123)


def main(n=200):
    for i in range(n):
        # Drive negative trends and toggles
        delta7 = random.uniform(-0.2, 0.2)
        delta30 = random.uniform(-0.3, 0.3)
        truth_violation = (random.random() < 0.05)

        # Near-boundary vectors
        a1 = {"grounded_options": random.randint(0,5), "counterfactual_quality": random.uniform(0,1), "reality_contact": random.random()>0.5}
        a2 = {"plan_detail": random.uniform(0,1), "resources_available": random.uniform(0,1), "capability_fit": random.uniform(0,1), "timeline_realism": random.uniform(0,1)}
        a3 = {"internal_locus": random.uniform(0,1), "values_alignment": random.uniform(0,1), "narrative_coherence": random.uniform(0,1), "non_substitution": random.uniform(0,1)}
        a4 = {"window_of_tolerance": random.uniform(0,1), "coping_access": random.uniform(0,1), "meaning_frame": random.uniform(0,1), "volatility_risk": random.uniform(0,1)}

        vec = compute_agency_vector(a1,a2,a3,a4)
        sm = EmpathyStateMachine()
        s = sm.step(vec, StateContext(AgencyDelta_7d=delta7, AgencyDelta_30d=delta30, truth_violation=truth_violation))
        if truth_violation and s != "VAULT":
            print("Violation: truth_violation expected VAULT, got", s)
        if vec.A3 < 0.30 and s != "REDIRECT":
            print("Violation: low A3 expected REDIRECT, got", s)
        if vec.A4 < 0.30 and s != "REDIRECT":
            print("Violation: low A4 expected REDIRECT, got", s)

if __name__ == "__main__":
    main()
