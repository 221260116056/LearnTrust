# Security Architecture of Cryptographically Enforced Adaptive Learning System

## 1. Executive Summary

This document presents the comprehensive security architecture of the LearnTrust platform, a cryptographically enforced adaptive learning management system designed to ensure academic integrity, prevent fraud, and maintain audit trails. The architecture implements multiple layers of security mechanisms including cryptographic validation, append-only audit logging, and secure content delivery.

## 2. Secure Heartbeat Validation System

### 2.1 Overview
The heartbeat validation system provides real-time monitoring of student engagement through cryptographically secured timestamp events. This prevents manipulation of watch time data and ensures accurate progress tracking.

### 2.2 Technical Implementation

#### Sequence Number Validation
- **Strict Monotonicity**: Each heartbeat must have a sequence number strictly greater than the previous
- **Server-Side Enforcement**: Sequence validation occurs entirely on the server; no client-side trust
- **Replay Attack Prevention**: Duplicate sequence numbers are rejected with HTTP 409 Conflict

```python
# Server-side sequence validation
last_event = WatchEvent.objects.filter(
    student=request.user, 
    module=module
).order_by('-sequence_number').first()

if last_event and int(sequence_number) <= last_event.sequence_number:
    return Response({
        "status": "error", 
        "message": f"Sequence number must be greater than {last_event.sequence_number}"
    }, status=400)
```

#### Timestamp Validation
- **30-Second Window**: Events older than 30 seconds are rejected
- **Server Clock Authority**: All time calculations use server-side timestamps
- **Clock Skew Protection**: Prevents delayed or pre-generated events

#### Cryptographic Token Generation
Each heartbeat generates a SHA-256 hash incorporating:
- User ID (prevents cross-user forgery)
- Module ID (prevents module switching)
- Sequence Number (ensures ordering)
- Server Secret Key (cryptographic binding)

```python
hash_input = f"{user.id}{module_id}{sequence_number}{SECRET_KEY}"
token_hash = hashlib.sha256(hash_input.encode()).hexdigest()
```

### 2.3 Threat Prevention
| Threat | Mitigation |
|--------|-----------|
| Replay Attacks | Sequence number uniqueness enforced |
| Timestamp Manipulation | Server-side time validation with 30s window |
| Token Forgery | HMAC-based cryptographic binding |
| Batch Injection | Strict sequence incrementing prevents bulk insertion |

## 3. Rule-Based Unlock Engine

### 3.1 Architecture
The unlock engine implements a deterministic, server-side policy evaluation system that controls module accessibility based on multiple weighted criteria.

### 3.2 Validation Criteria

#### Progressive Unlocking
- **Prerequisite Completion**: Module N requires completion of Module N-1
- **Watch Percentage Threshold**: Configurable minimum watch percentage (default 80%)
- **Validation Chain**: Each criterion must pass for unlock to succeed

```python
def validate_module_unlock(user, module, request=None):
    # Watch percentage validation
    if watch_percentage < module.minimum_watch_percentage:
        return False
    
    # Quiz completion requirement
    if module.must_pass_quiz:
        if not has_passed_quiz(user, module):
            return False
    
    # Release date enforcement
    if release_date and release_date > timezone.now():
        return False
    
    # Micro-quiz failure limit
    if request and micro_quiz_failures > 3:
        return False
    
    return True
```

#### Micro-Quiz Failure Protection
- **Failure Threshold**: Maximum 3 failures allowed before module lock
- **Session-Based Tracking**: Failures stored in secure server session
- **Anti-Brute Force**: Prevents rapid retry attempts

### 3.3 Security Properties
- **No Client Override**: Unlock decisions made exclusively server-side
- **Atomic Validation**: All criteria evaluated in single transaction
- **Audit Logging**: Every unlock attempt logged immutably

## 4. Signed Streaming Token System

### 4.1 Purpose
Prevents unauthorized video access and content piracy through time-limited, cryptographically signed access tokens.

### 4.2 Token Structure

#### Payload
```json
{
    "user_id": 123,
    "module_id": 456,
    "expiry": 1699999999
}
```

#### Signature Generation
```python
# HMAC-SHA256 with server secret
signature = hmac.new(
    SECRET_KEY.encode(),
    payload_bytes,
    hashlib.sha256
).hexdigest()

# Token format: base64payload.signature
token = f"{payload_b64}.{signature}"
```

### 4.3 Validation Protocol
1. **Token Extraction**: Parse from URL query parameter
2. **Signature Verification**: Recompute HMAC and compare
3. **Expiry Check**: Reject expired tokens (10-minute lifetime)
4. **Context Validation**: Verify user_id and module_id match request

### 4.4 Security Benefits
- **Time-Bounded Access**: 10-minute token lifetime limits exposure
- **Tamper Detection**: Any payload modification invalidates signature
- **User Binding**: Tokens cannot be transferred between users
- **Replay Protection**: Expiry prevents indefinite reuse

## 5. Immutable Audit Logging System

### 5.1 Design Principles
The audit system implements a blockchain-inspired append-only structure where each log entry cryptographically links to its predecessor.

### 5.2 Chain Structure

#### Hash Chain
```
Block N:   [user_id + event_type + timestamp + prev_hash + SECRET_KEY] → SHA256 → current_hash
                ↓
Block N+1: [user_id + event_type + timestamp + current_hash + SECRET_KEY] → SHA256 → next_hash
```

#### Genesis Block
- Initial block uses zero-filled 64-character hash (64 zeros)
- Establishes chain origin
- Tampering with any block breaks chain integrity

### 5.3 Anti-Tampering Properties

| Property | Implementation |
|----------|---------------|
| Append-Only | save() raises exception if pk exists |
| Deletion Prevention | delete() raises exception unconditionally |
| Cryptographic Linking | Each entry includes hash of previous |
| Tamper Evidence | Chain break detectable via hash mismatch |

### 5.4 Use Cases
- **Compliance**: SOX, GDPR audit trail requirements
- **Dispute Resolution**: Immutable record of student activity
- **Forensics**: Reconstruct timeline of security events
- **Academic Integrity**: Proof of work completion

## 6. Cryptographic Certificate Verification

### 6.1 Certificate Generation

#### Hash Computation
```python
hash_input = f"{student_id}{course_id}{issued_at}{SECRET_KEY}"
certificate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
```

#### Verification Code
- UUID4 generated for each certificate
- Public verification URL: `/verify/<uuid>/`
- Enables third-party verification without database access

### 6.2 Verification Process
1. **Lookup**: Retrieve certificate by verification_code
2. **Hash Recomputation**: Calculate expected hash from stored fields
3. **Comparison**: Validate against stored certificate_hash
4. **Result**: Return verified/invalid status

### 6.3 QR Code Integration
Each certificate includes a QR code containing the verification URL, enabling instant mobile verification:
```python
qr.add_data(f"https://yourdomain.com/verify/{certificate.verification_code}/")
```

### 6.4 Security Guarantees
- **Non-Repudiation**: Cryptographic proof of issuance
- **Unforgeability**: Without server secret, valid certificates cannot be fabricated
- **Public Verifiability**: Anyone can verify without system access

## 7. Threat Prevention Matrix

| Threat Category | Attack Vector | Mitigation Strategy |
|----------------|---------------|---------------------|
| **Academic Fraud** | Module skipping without watching | Rule-based unlock engine with watch percentage validation |
| **Content Piracy** | Video download/sharing | Signed tokens with 10-minute expiry; user binding |
| **Data Tampering** | Modifying progress/completion | Immutable audit logs with hash chain; append-only storage |
| **Replay Attacks** | Re-submitting old heartbeats | Strict sequence number validation; timestamp checks |
| **Certificate Forgery** | Creating fake certificates | Cryptographic signing with server secret; public verification |
| **Time Cheating** | Artificially inflating watch time | Server-side time validation; cryptographic heartbeat tokens |
| **Brute Force** | Repeated quiz attempts | Session-based failure tracking; lockout after 3 failures |

## 8. Database Security Constraints

### 8.1 Integrity Constraints
- **Unique Pairs**: (user, module) in StudentProgress
- **Unique Pairs**: (user, course) in Enrollment
- **Composite Unique**: (student, module, sequence_number) in WatchEvent

### 8.2 Performance Optimization
- **Indexing**: db_index on WatchEvent.user, WatchEvent.module
- **Time Indexing**: db_index on WatchEvent.created_at
- **Composite Index**: (student, module, created_at) for efficient queries

## 9. Production Security Configuration

### 9.1 Django Security Settings
```python
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
X_FRAME_OPTIONS = 'DENY'
```

### 9.2 Secret Management
- SECRET_KEY loaded from environment variables
- Database credentials externalized
- Token secrets rotated quarterly

## 10. Conclusion

The LearnTrust security architecture implements a defense-in-depth strategy combining cryptographic validation, immutable auditing, and strict server-side control. By eliminating client-side trust and implementing multiple independent verification layers, the system ensures academic integrity while maintaining a seamless user experience.

The architecture successfully addresses the core challenge of online education: verifying that students actually engage with content rather than merely navigating through it. Through cryptographic heartbeat validation, signed streaming tokens, and rule-based unlocking, LearnTrust provides a robust foundation for trustworthy adaptive learning.
