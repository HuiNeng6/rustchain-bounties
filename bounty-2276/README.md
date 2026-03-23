# RustChain Bounty #2276 - Fingerprint Replay Attack Defense

**Bounty**: 150 RTC (Attack + Defense)  
**Difficulty**: HARD  
**Type**: Red Team  

**Wallet Address**: `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`

---

## Overview

This submission addresses the fingerprint replay attack vulnerability in RustChain's attestation system. The attack scenario involves an attacker capturing legitimate G4 PowerBook fingerprint data and replaying it from a modern x86 machine to claim the 2.5x antiquity bonus.

## Files

### 1. `replay_attack_poc.py` - Attack Proof of Concept

Demonstrates three attack vectors:

1. **Direct Replay** - Resending the exact captured payload without modification
2. **Fresh Nonce Replay** - Getting a new challenge but using old captured fingerprint data
3. **Cross-Architecture Replay** - Replaying PowerPC fingerprint from x86 machine

```bash
python replay_attack_poc.py --node https://rustchain.local --wallet YOUR_WALLET --save-report report.json
```

### 2. `replay_defense.py` - Defense Implementation

Implements comprehensive defense mechanisms:

- **Server-side Nonce Binding** - Each nonce is bound to client IP and TLS fingerprint
- **Nonce Expiry** - Nonces expire after 10 minutes (configurable)
- **Single-Use Nonces** - Each nonce can only be used once
- **Fingerprint Freshness Validation** - `validate_fingerprint_freshness()` function checks:
  - Timing data is recent and consistent
  - Cache geometry matches claimed architecture
  - SIMD type matches claimed architecture
  - Thermal data shows realistic readings
  - Instruction jitter has valid patterns
  - No VM/emulation indicators
- **Entropy Analysis** - Cross-checks fingerprint metrics against expected ranges for claimed architecture
- **Connection Metadata Validation** - Checks for cloud IPs, VM indicators, TLS inconsistencies
- **Fingerprint Uniqueness Tracking** - Detects reuse of the same fingerprint data

### 3. `test_replay_defense.py` - Test Suite

Comprehensive tests proving the defense works:

| Test | Expected Result | Description |
|------|-----------------|-------------|
| Replayed Fingerprint | REJECTED | Same fingerprint data submitted twice |
| Fresh Fingerprint | ACCEPTED | Valid new fingerprint data |
| Modified Replay | REJECTED | Fresh nonce but old fingerprint data |
| Nonce Reuse | REJECTED | Same nonce used twice |
| Expired Nonce | REJECTED | Nonce past expiry time |
| VM Detection | REJECTED | Hypervisor detected in fingerprint |
| Architecture Mismatch | REJECTED | x86 data claiming to be PowerPC |

```bash
python test_replay_defense.py
```

---

## Defense Mechanism Details

### Nonce Management

```python
# Issue challenge with client binding
challenge = defense.issue_challenge(client_ip, tls_fingerprint)

# Nonce is bound to:
# - Client IP address
# - TLS fingerprint (JA3)
# - Expiry time (10 minutes)
# - Single-use constraint
```

### Fingerprint Freshness Validation

The `validate_fingerprint_freshness()` function validates:

1. **Clock Drift Check**
   - Sufficient samples (>100)
   - Mean timing within expected range for architecture
   - Variance consistent with real hardware

2. **Cache Timing Check**
   - Unique pattern hash present
   - Cache geometry matches claimed architecture
   - Latency values within expected range

3. **SIMD Identity Check**
   - SIMD type matches architecture (AltiVec for G4)
   - Implementation hash present

4. **Thermal Drift Check**
   - Temperature reading realistic (20-90°C)
   - Unique thermal signature present

5. **Instruction Jitter Check**
   - Pattern hash present
   - Jitter distribution realistic

6. **Anti-Emulation Check**
   - No hypervisor detected
   - No VM artifacts

### Entropy Analysis

Cross-checks fingerprint metrics against known-good ranges:

```python
# PowerPC G4 Expected Ranges
POWERPC_G4_EXPECTED = {
    "clock_drift": {
        "drift_ppm": (5, 50),
        "mean_ns": (20000, 30000),
        "variance_ns": (200, 600)
    },
    "cache_timing": {
        "l1_latency_ns": (2, 5),
        "l2_latency_ns": (8, 20),
        "cache_line_size": (32, 32)  # Exact for G4
    },
    # ...
}
```

### Connection Metadata Validation

- Checks for known cloud provider IP ranges
- Detects VM TLS fingerprint indicators
- Validates TLS version consistency with claimed hardware age

---

## Integration

The defense system integrates with the existing RustChain attestation flow:

```python
from replay_defense import ReplayDefenseSystem

defense = ReplayDefenseSystem()

# POST /attest/challenge
@app.route('/attest/challenge', methods=['POST'])
def attest_challenge():
    client_ip = request.remote_addr
    tls_fingerprint = request.headers.get('X-TLS-Fingerprint', '')
    challenge = defense.issue_challenge(client_ip, tls_fingerprint)
    return jsonify(challenge)

# POST /attest/submit
@app.route('/attest/submit', methods=['POST'])
def attest_submit():
    payload = request.get_json()
    client_ip = request.remote_addr
    tls_fingerprint = request.headers.get('X-TLS-Fingerprint', '')
    
    accepted, reason, details = defense.validate_attestation(
        payload, client_ip, tls_fingerprint
    )
    
    if accepted:
        return jsonify({"status": "accepted"}), 200
    else:
        return jsonify({"status": "rejected", "reason": reason}), 400
```

---

## Test Results

All tests pass, demonstrating:

```
✓ TEST PASSED: Direct replay correctly rejected
✓ TEST PASSED: Old fingerprint data correctly rejected
✓ TEST PASSED: Fresh valid fingerprint correctly accepted
✓ TEST PASSED: Multiple unique fingerprints correctly accepted
✓ TEST PASSED: Fresh nonce with old fingerprint correctly rejected
✓ TEST PASSED: Nonce reuse correctly rejected
✓ TEST PASSED: PowerPC entropy validation works
✓ TEST PASSED: x86 claiming PowerPC correctly rejected
✓ TEST PASSED: Hypervisor detection works
✓ TEST PASSED: Expired nonce correctly rejected
```

---

## Security Considerations

1. **No Breaking Changes** - The defense does not break existing legitimate miners. Fresh, valid fingerprints continue to be accepted.

2. **No DoS** - The validation is efficient and does not create denial-of-service conditions.

3. **Surgical Testing** - The attack POC tests specific replay vectors, not load testing.

4. **Backward Compatible** - Existing attestation payloads work with the defense system.

---

## Bounty Claim

- **Bounty ID**: #2276
- **Type**: Red Team (Attack + Defense)
- **Reward**: 150 RTC
- **Wallet**: `9dRRMiHiJwjF3VW8pXtKDtpmmxAPFy3zWgV2JY5H6eeT`

This submission includes:
- ✅ Attack POC (`replay_attack_poc.py`)
- ✅ Defense implementation (`replay_defense.py`)
- ✅ Tests proving defense works (`test_replay_defense.py`)
- ✅ Documentation (this README)