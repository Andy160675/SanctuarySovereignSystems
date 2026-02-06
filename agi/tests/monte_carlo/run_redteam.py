import random
import statistics as stats
from agi.core.agency_metrics import compute_agency_vector
from agi.core.empathy_state_machine import EmpathyStateMachine

random.seed(42)


def rand01():
    return max(0.0, min(1.0, random.random()))


def sample_vec():
    a1 = {"grounded_options": int(random.random()*6), "counterfactual_quality": rand01(), "reality_contact": random.random()>0.2}
    a2 = {"plan_detail": rand01(), "resources_available": rand01(), "capability_fit": rand01(), "timeline_realism": rand01()}
    a3 = {"internal_locus": rand01(), "values_alignment": rand01(), "narrative_coherence": rand01(), "non_substitution": rand01()}
    a4 = {"window_of_tolerance": rand01(), "coping_access": rand01(), "meaning_frame": rand01(), "volatility_risk": rand01()}
    return compute_agency_vector(a1,a2,a3,a4)


def main(n=1000):
    states = []
    for _ in range(n):
        vec = sample_vec()
        sm = EmpathyStateMachine()
        s = sm.step(vec)
        states.append(s)
    from collections import Counter
    c = Counter(states)
    print("State distribution:", c)

if __name__ == "__main__":
    main()
