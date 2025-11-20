import sys
import os

# Ensure we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.governance import Proposal, ActionType
from src.scout.scout import Scout
from src.executor.executor import Executor
from src.boardroom.boardroom import Boardroom

def main():
    print('---   INITIALIZING BOARDROOM-13 CONSTITUTION v0.1 ---')
    
    # 1. Initialize Core Organs
    boardroom = Boardroom()
    executor = Executor(boardroom)
    scout = Scout()

    print(f' Organs Online. Ledger Head: {boardroom.last_hash[:8]}...')

    # 2. Scout Generates Idea
    print('\n---  SCOUT PHASE ---')
    proposal = scout.propose_log_cleanup()
    print(f'Proposal Generated: {proposal.id} | Cost: ')

    # 3. Executor runs Trial (Sandbox)
    print('\n---  EXECUTOR PHASE (TRIAL) ---')
    trial_result = executor.run_trial(proposal)
    print(f'Trial Result: Success={trial_result['success']} | Metrics={trial_result.get('metrics')}')

    # 4. Boardroom Decides
    print('\n---  BOARDROOM PHASE ---')
    decision = boardroom.evaluate_proposal(proposal, trial_result)
    print(f'Decision: {decision.decision_type}')
    
    if decision.violation:
        print(f' VIOLATION: {decision.violation.rule_id}')
    else:
        print(f'Reasoning: {decision.reasoning}')

    print('\n---  LEDGER AUDIT ---')
    print(f'Written to: {boardroom.ledger_path}')
    
if __name__ == '__main__':
    main()
