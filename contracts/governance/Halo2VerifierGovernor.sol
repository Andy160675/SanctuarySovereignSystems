// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Halo2VerifierGovernor
 * @notice Phase 8 — The Code as Governor
 *
 * This contract is the ONLY canonical gate for proof verification.
 * It does ONE thing: decide VALID or INVALID — final, recorded, binding.
 *
 * Constitutional Requirements:
 * 1. Immutable verifying keys (vkHash cannot change once set)
 * 2. Single canonical entrypoint (verifyAndRecord)
 * 3. Event trail for ledger/KG ingestion
 * 4. C-level gating (containment level enforcement)
 * 5. NO human override path (governance cannot flip failed proofs)
 *
 * "The Code is the only Governor."
 */

/// @notice Interface each generated Halo2 verifier must implement
interface IHalo2CircuitVerifier {
    function verifyProof(bytes calldata proof, uint256[] calldata publicInputs)
        external
        view
        returns (bool);
}

/// @notice Governance-level verifier router — the ONLY canonical gate
contract Halo2VerifierGovernor {
    // =========================================================================
    // State Variables
    // =========================================================================

    /// @notice Current containment level (C-1 through C-10)
    /// Can only be changed via constitutional process (multi-sig + proofs)
    uint8 public currentContainmentLevel;

    /// @notice Governance address (multi-sig / MPC adapter)
    address public immutable governance;

    /// @notice Circuit information structure
    struct CircuitInfo {
        IHalo2CircuitVerifier verifier;  // Generated Halo2 verifier contract
        bytes32 vkHash;                   // Hash of verifying key (immutable once set)
        uint8 minContainmentLevel;        // Minimum C-level required to use this circuit
        bool enabled;                     // Whether circuit is active
        uint256 registeredAt;             // Block number when registered
    }

    /// @notice Circuit registry: circuitId => CircuitInfo
    mapping(bytes32 => CircuitInfo) public circuits;

    /// @notice Proof acceptance counter per circuit (for analytics)
    mapping(bytes32 => uint256) public acceptedCount;

    /// @notice Proof rejection counter per circuit (for analytics)
    mapping(bytes32 => uint256) public rejectedCount;

    /// @notice 100-block consecutive pass counter per circuit
    mapping(bytes32 => uint256) public consecutivePasses;

    /// @notice Last block a proof was accepted for each circuit
    mapping(bytes32 => uint256) public lastAcceptedBlock;

    // =========================================================================
    // Constants — Reason Codes for Rejection
    // =========================================================================

    uint8 public constant REASON_CIRCUIT_NOT_FOUND = 0;
    uint8 public constant REASON_CIRCUIT_DISABLED = 1;
    uint8 public constant REASON_CONTAINMENT_LEVEL = 2;
    uint8 public constant REASON_VERIFIER_FAIL = 3;
    uint8 public constant REASON_INVALID_INPUTS = 4;

    // =========================================================================
    // Events — Canonical Trail for Ledger/KG
    // =========================================================================

    event CircuitRegistered(
        bytes32 indexed circuitId,
        address verifier,
        bytes32 vkHash,
        uint8 minContainmentLevel,
        uint256 blockNumber
    );

    event CircuitDisabled(
        bytes32 indexed circuitId,
        uint256 blockNumber
    );

    event ContainmentLevelUpdated(
        uint8 oldLevel,
        uint8 newLevel,
        uint256 blockNumber
    );

    event ProofAccepted(
        bytes32 indexed circuitId,
        bytes32 publicInputsHash,
        address indexed caller,
        uint256 blockNumber,
        uint256 consecutiveCount
    );

    event ProofRejected(
        bytes32 indexed circuitId,
        bytes32 publicInputsHash,
        address indexed caller,
        uint256 blockNumber,
        uint8 reasonCode
    );

    event ConsecutivePassReset(
        bytes32 indexed circuitId,
        uint256 previousCount,
        uint256 blockNumber
    );

    event HundredBlockMilestone(
        bytes32 indexed circuitId,
        uint256 blockNumber
    );

    // =========================================================================
    // Modifiers
    // =========================================================================

    modifier onlyGovernance() {
        require(msg.sender == governance, "Halo2Gov: not governance");
        _;
    }

    // =========================================================================
    // Constructor
    // =========================================================================

    constructor(address _governance, uint8 _initialContainmentLevel) {
        require(_governance != address(0), "Halo2Gov: zero governance");
        require(_initialContainmentLevel >= 1 && _initialContainmentLevel <= 10, "Halo2Gov: invalid C-level");

        governance = _governance;
        currentContainmentLevel = _initialContainmentLevel;
    }

    // =========================================================================
    // Governance Functions (called rarely, heavily audited)
    // =========================================================================

    /**
     * @notice Register a new circuit with its verifier
     * @dev Once registered, vkHash is IMMUTABLE. To change, register new circuitId.
     * @param circuitId Unique identifier for the circuit
     * @param verifierAddr Address of the generated Halo2 verifier contract
     * @param vkHash Hash of the verifying key bytes
     * @param minContainmentLevel Minimum C-level required to use this circuit
     */
    function registerCircuit(
        bytes32 circuitId,
        address verifierAddr,
        bytes32 vkHash,
        uint8 minContainmentLevel
    ) external onlyGovernance {
        require(
            address(circuits[circuitId].verifier) == address(0),
            "Halo2Gov: circuit exists"
        );
        require(verifierAddr != address(0), "Halo2Gov: zero verifier");
        require(vkHash != bytes32(0), "Halo2Gov: zero vkHash");
        require(
            minContainmentLevel >= 1 && minContainmentLevel <= 10,
            "Halo2Gov: invalid min C-level"
        );

        circuits[circuitId] = CircuitInfo({
            verifier: IHalo2CircuitVerifier(verifierAddr),
            vkHash: vkHash,
            minContainmentLevel: minContainmentLevel,
            enabled: true,
            registeredAt: block.number
        });

        emit CircuitRegistered(
            circuitId,
            verifierAddr,
            vkHash,
            minContainmentLevel,
            block.number
        );
    }

    /**
     * @notice Disable a circuit (cannot re-enable — register new one instead)
     * @dev This is a one-way operation. Disabled circuits cannot verify proofs.
     * @param circuitId The circuit to disable
     */
    function disableCircuit(bytes32 circuitId) external onlyGovernance {
        require(circuits[circuitId].enabled, "Halo2Gov: already disabled");

        circuits[circuitId].enabled = false;

        emit CircuitDisabled(circuitId, block.number);
    }

    /**
     * @notice Update the current containment level
     * @dev Can only increment by 1 at a time (no jumps)
     * @param newLevel The new containment level
     */
    function setContainmentLevel(uint8 newLevel) external onlyGovernance {
        require(
            newLevel >= 1 && newLevel <= 10,
            "Halo2Gov: invalid C-level"
        );
        require(
            newLevel == currentContainmentLevel + 1 || newLevel == currentContainmentLevel - 1,
            "Halo2Gov: can only change by 1"
        );

        uint8 oldLevel = currentContainmentLevel;
        currentContainmentLevel = newLevel;

        emit ContainmentLevelUpdated(oldLevel, newLevel, block.number);
    }

    // =========================================================================
    // Core Function — Canonical Verification Entrypoint
    // =========================================================================

    /**
     * @notice Verify a proof and record the result
     * @dev This is the ONLY path for governance-relevant proof verification.
     *      No helper functions bypass logging. No convenience shortcuts.
     * @param circuitId The circuit to verify against
     * @param publicInputs The public inputs to the circuit
     * @param proof The Halo2 proof bytes
     * @return valid Whether the proof was accepted
     */
    function verifyAndRecord(
        bytes32 circuitId,
        uint256[] calldata publicInputs,
        bytes calldata proof
    ) external returns (bool valid) {
        CircuitInfo storage info = circuits[circuitId];
        bytes32 piHash = keccak256(abi.encodePacked(publicInputs));

        // Check 1: Circuit exists
        if (address(info.verifier) == address(0)) {
            _recordRejection(circuitId, piHash, REASON_CIRCUIT_NOT_FOUND);
            return false;
        }

        // Check 2: Circuit is enabled
        if (!info.enabled) {
            _recordRejection(circuitId, piHash, REASON_CIRCUIT_DISABLED);
            return false;
        }

        // Check 3: Containment level sufficient
        if (currentContainmentLevel < info.minContainmentLevel) {
            _recordRejection(circuitId, piHash, REASON_CONTAINMENT_LEVEL);
            return false;
        }

        // Check 4: Verify the proof
        bool ok;
        try info.verifier.verifyProof(proof, publicInputs) returns (bool result) {
            ok = result;
        } catch {
            ok = false;
        }

        if (!ok) {
            _recordRejection(circuitId, piHash, REASON_VERIFIER_FAIL);
            // Reset consecutive pass counter on any failure
            uint256 previousCount = consecutivePasses[circuitId];
            if (previousCount > 0) {
                consecutivePasses[circuitId] = 0;
                emit ConsecutivePassReset(circuitId, previousCount, block.number);
            }
            return false;
        }

        // Proof accepted — record success
        _recordAcceptance(circuitId, piHash);
        return true;
    }

    // =========================================================================
    // Internal Functions
    // =========================================================================

    function _recordRejection(
        bytes32 circuitId,
        bytes32 piHash,
        uint8 reasonCode
    ) internal {
        rejectedCount[circuitId]++;

        emit ProofRejected(
            circuitId,
            piHash,
            msg.sender,
            block.number,
            reasonCode
        );
    }

    function _recordAcceptance(
        bytes32 circuitId,
        bytes32 piHash
    ) internal {
        acceptedCount[circuitId]++;

        // Update consecutive pass counter
        uint256 lastBlock = lastAcceptedBlock[circuitId];
        if (lastBlock == block.number - 1 || lastBlock == 0) {
            // Consecutive block or first acceptance
            consecutivePasses[circuitId]++;
        } else {
            // Gap in blocks — reset counter
            uint256 previousCount = consecutivePasses[circuitId];
            if (previousCount > 0) {
                emit ConsecutivePassReset(circuitId, previousCount, block.number);
            }
            consecutivePasses[circuitId] = 1;
        }

        lastAcceptedBlock[circuitId] = block.number;
        uint256 currentConsecutive = consecutivePasses[circuitId];

        emit ProofAccepted(
            circuitId,
            piHash,
            msg.sender,
            block.number,
            currentConsecutive
        );

        // Check for 100-block milestone
        if (currentConsecutive == 100) {
            emit HundredBlockMilestone(circuitId, block.number);
        }
    }

    // =========================================================================
    // View Functions
    // =========================================================================

    /**
     * @notice Get circuit information
     * @param circuitId The circuit to query
     * @return verifier The verifier contract address
     * @return vkHash The verifying key hash
     * @return minContainmentLevel Minimum required C-level
     * @return enabled Whether circuit is active
     * @return registeredAt Block number when registered
     */
    function getCircuitInfo(bytes32 circuitId)
        external
        view
        returns (
            address verifier,
            bytes32 vkHash,
            uint8 minContainmentLevel,
            bool enabled,
            uint256 registeredAt
        )
    {
        CircuitInfo storage info = circuits[circuitId];
        return (
            address(info.verifier),
            info.vkHash,
            info.minContainmentLevel,
            info.enabled,
            info.registeredAt
        );
    }

    /**
     * @notice Get circuit statistics
     * @param circuitId The circuit to query
     * @return accepted Total accepted proofs
     * @return rejected Total rejected proofs
     * @return consecutive Current consecutive pass count
     * @return lastBlock Last block with accepted proof
     */
    function getCircuitStats(bytes32 circuitId)
        external
        view
        returns (
            uint256 accepted,
            uint256 rejected,
            uint256 consecutive,
            uint256 lastBlock
        )
    {
        return (
            acceptedCount[circuitId],
            rejectedCount[circuitId],
            consecutivePasses[circuitId],
            lastAcceptedBlock[circuitId]
        );
    }

    /**
     * @notice Check if a circuit has achieved 100-block closure
     * @param circuitId The circuit to check
     * @return closed Whether 100 consecutive passes achieved
     */
    function isCircuitClosed(bytes32 circuitId) external view returns (bool closed) {
        return consecutivePasses[circuitId] >= 100;
    }
}
