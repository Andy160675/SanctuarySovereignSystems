import pytest
from sovereign_engine.extensions.autonomous_build_command.executor import Executor
from sovereign_engine.extensions.autonomous_build_command.decision_log import DecisionLogger

def test_executor_dry_run(tmp_path):
    log_file = tmp_path / "decisions.jsonl"
    logger = DecisionLogger(str(log_file))
    executor = Executor(logger, dry_run=True)
    
    def dummy_action():
        return "Done"
        
    result = executor.execute("test_1", dummy_action)
    assert result == "DRY_RUN_SUCCESS"

def test_executor_success(tmp_path):
    log_file = tmp_path / "decisions.jsonl"
    logger = DecisionLogger(str(log_file))
    executor = Executor(logger, dry_run=False)
    
    def dummy_action(val):
        return val
        
    result = executor.execute("test_2", dummy_action, "actual_done")
    assert result == "actual_done"

def test_executor_retry_and_fail(tmp_path):
    log_file = tmp_path / "decisions.jsonl"
    logger = DecisionLogger(str(log_file))
    executor = Executor(logger, dry_run=False, max_retries=2)
    
    state = {"count": 0}
    def failing_action():
        state["count"] += 1
        raise ValueError("Fail")
        
    with pytest.raises(ValueError):
        executor.execute("test_3", failing_action)
    
    assert state["count"] == 2

def test_executor_rollback(tmp_path):
    log_file = tmp_path / "decisions.jsonl"
    logger = DecisionLogger(str(log_file))
    executor = Executor(logger, dry_run=False, max_retries=1)
    
    rollback_state = {"done": False}
    def rollback_hook():
        rollback_state["done"] = True
        
    executor.register_rollback("test_4", rollback_hook)
    
    def failing_action():
        raise ValueError("Fail")
        
    with pytest.raises(ValueError):
        executor.execute("test_4", failing_action)
        
    assert rollback_state["done"] is True
