#!/usr/bin/env python3
"""HMAC Audit Chain -- tamper-evident event logging for AIShield collector.

Inspired by CyberGuard's hash-bound approvals and HMAC audit chain design.
Each event is signed with HMAC-SHA256 using a rotating key, creating a
tamper-evident chain where any modification breaks the chain.

Design:
- Each event gets a sequence number and HMAC signature
- Signatures are chained: each event's HMAC includes the previous signature
- Verification can detect any tampering, deletion, or reordering
- Key rotation supported via key_id in event metadata

Usage:
    from audit_chain import AuditChain

    chain = AuditChain(secret_key="your-secret-key")
    event = chain.sign({"type": "ScanCompleted", "ts": "..."})
    chain.append(event)

    # Later, verify the chain
    chain.verify()  # raises if tampered
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AuditChainError(Exception):
    """Raised when audit chain verification fails."""
    pass


class AuditChain:
    """Tamper-evident event chain with HMAC signatures.

    Events are appended in order, each with:
    - seq: sequential event number
    - ts: timestamp (ISO 8601)
    - payload: the original event data
    - prev_hash: hash of previous event (for chaining)
    - hmac: HMAC-SHA256 signature of (seq + ts + payload + prev_hash)
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        key_id: str = "default",
        algorithm: str = "sha256",
    ):
        """Initialize audit chain.

        Args:
            secret_key: HMAC secret key. If None, generates a random one.
            key_id: Identifier for key rotation tracking.
            algorithm: HMAC algorithm (sha256, sha384, sha512).
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.key_id = key_id
        self.algorithm = algorithm
        self.events: List[Dict[str, Any]] = []
        self._prev_hash = "0" * (int(algorithm.replace("sha", "")) // 4)

    def _compute_hmac(self, data: str) -> str:
        """Compute HMAC signature for given data."""
        return hmac.new(
            self.secret_key.encode("utf-8"),
            data.encode("utf-8"),
            getattr(hashlib, self.algorithm),
        ).hexdigest()

    def _compute_hash(self, data: str) -> str:
        """Compute plain hash for chaining."""
        return hashlib.new(self.algorithm, data.encode("utf-8")).hexdigest()

    def sign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a payload and create a signed event.

        Args:
            payload: The event data to sign.

        Returns:
            Signed event with seq, ts, hmac, prev_hash.
        """
        seq = len(self.events)
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Create canonical string for signing
        canonical = json.dumps(
            {"seq": seq, "ts": ts, "payload": payload, "prev_hash": self._prev_hash},
            sort_keys=True,
            separators=(",", ":"),
        )

        # Compute HMAC
        event_hmac = self._compute_hmac(canonical)

        # Compute event hash for chaining
        event_hash = self._compute_hash(canonical + event_hmac)

        event = {
            "seq": seq,
            "ts": ts,
            "key_id": self.key_id,
            "payload": payload,
            "prev_hash": self._prev_hash,
            "hmac": event_hmac,
            "hash": event_hash,
        }

        return event

    def append(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Append a signed event to the chain.

        Args:
            event: A signed event (from sign() method).

        Returns:
            The appended event.

        Raises:
            AuditChainError: If event is invalid or chain is broken.
        """
        # Verify the event is valid
        self._verify_event(event)

        # Check sequence continuity
        expected_seq = len(self.events)
        if event.get("seq") != expected_seq:
            raise AuditChainError(
                f"Sequence mismatch: expected {expected_seq}, got {event.get('seq')}"
            )

        # Check prev_hash matches
        if event.get("prev_hash") != self._prev_hash:
            raise AuditChainError(
                f"Chain broken: prev_hash mismatch at seq {event['seq']}"
            )

        self.events.append(event)
        self._prev_hash = event["hash"]
        return event

    def _verify_event(self, event: Dict[str, Any]) -> bool:
        """Verify a single event's HMAC signature.

        Args:
            event: Event to verify.

        Returns:
            True if valid.

        Raises:
            AuditChainError: If verification fails.
        """
        seq = event.get("seq")
        ts = event.get("ts")
        payload = event.get("payload")
        prev_hash = event.get("prev_hash")
        expected_hmac = event.get("hmac")

        if not all([seq is not None, ts, payload is not None, prev_hash, expected_hmac]):
            raise AuditChainError("Event missing required fields")

        # Recompute canonical string
        canonical = json.dumps(
            {"seq": seq, "ts": ts, "payload": payload, "prev_hash": prev_hash},
            sort_keys=True,
            separators=(",", ":"),
        )

        # Verify HMAC
        computed_hmac = self._compute_hmac(canonical)
        if not hmac.compare_digest(computed_hmac, expected_hmac):
            raise AuditChainError(
                f"HMAC verification failed at seq {seq}: "
                f"expected {computed_hmac[:16]}..., got {expected_hmac[:16]}..."
            )

        return True

    def verify(self) -> bool:
        """Verify the entire chain integrity.

        Returns:
            True if chain is valid.

        Raises:
            AuditChainError: If any event fails verification.
        """
        for i, event in enumerate(self.events):
            try:
                self._verify_event(event)
            except AuditChainError as e:
                raise AuditChainError(f"Chain verification failed at event {i}: {e}")

        # Verify chain continuity
        for i in range(1, len(self.events)):
            if self.events[i]["prev_hash"] != self.events[i - 1]["hash"]:
                raise AuditChainError(
                    f"Chain broken between events {i-1} and {i}"
                )

        return True

    def export(self) -> str:
        """Export the chain as JSONL (one event per line).

        Returns:
            JSONL string with all events.
        """
        return "\n".join(json.dumps(e, separators=(",", ":")) for e in self.events)

    def load(self, jsonl: str) -> None:
        """Load events from JSONL string.

        Args:
            jsonl: JSONL string with events.
        """
        self.events = []
        self._prev_hash = "0" * (int(self.algorithm.replace("sha", "")) // 4)

        for line in jsonl.strip().split("\n"):
            if not line:
                continue
            event = json.loads(line)
            # Don't re-verify on load, just append
            self.events.append(event)
            self._prev_hash = event.get("hash", self._prev_hash)

    def save(self, filepath: str) -> None:
        """Save the chain to a JSONL file.

        Args:
            filepath: Path to save the chain.
        """
        with open(filepath, "w") as f:
            f.write(self.export())

    def load_file(self, filepath: str) -> None:
        """Load the chain from a JSONL file.

        Args:
            filepath: Path to load the chain from.
        """
        with open(filepath, "r") as f:
            self.load(f.read())

    def stats(self) -> Dict[str, Any]:
        """Get chain statistics.

        Returns:
            Dict with chain stats.
        """
        return {
            "event_count": len(self.events),
            "first_ts": self.events[0]["ts"] if self.events else None,
            "last_ts": self.events[-1]["ts"] if self.events else None,
            "key_id": self.key_id,
            "algorithm": self.algorithm,
            "chain_intact": self.verify() if self.events else True,
        }


def create_chain(
    secret_key: Optional[str] = None,
    key_id: str = "default",
) -> AuditChain:
    """Factory function to create an AuditChain.

    Args:
        secret_key: HMAC secret key (optional, generates if None).
        key_id: Key identifier.

    Returns:
        Configured AuditChain instance.
    """
    return AuditChain(secret_key=secret_key, key_id=key_id)


if __name__ == "__main__":
    # Demo usage
    print("=== AIShield HMAC Audit Chain Demo ===")
    print()

    # Create chain with a test key
    chain = create_chain(secret_key="demo-key-12345", key_id="demo-001")

    # Sign and append events
    events = [
        {"type": "CollectorStarted", "collector": "aishield-collector"},
        {"type": "ConfigDiscovered", "config_path": "/etc/mcp.json", "servers": 3},
        {"type": "FindingRaised", "severity": "high", "rule": "OWASP-A03", "server": "github"},
        {"type": "ScanCompleted", "duration_ms": 1523, "findings_count": 1},
    ]

    for payload in events:
        signed = chain.sign(payload)
        chain.append(signed)
        print(f"[{signed['seq']:03d}] {payload['type']:20s} hmac={signed['hmac'][:16]}...")

    print()

    # Verify chain
    print(f"Chain verification: {'PASSED' if chain.verify() else 'FAILED'}")
    print(f"Stats: {json.dumps(chain.stats(), indent=2)}")

    # Test tamper detection
    print("\n=== Tamper Detection Test ===")
    
    # Method 1: Modify payload directly
    tampered_chain1 = create_chain(secret_key="demo-key-12345", key_id="demo-001")
    for payload in events:
        signed = tampered_chain1.sign(payload)
        tampered_chain1.append(signed)
    
    # Tamper with event 2's payload
    tampered_chain1.events[2]["payload"]["severity"] = "info"
    
    try:
        tampered_chain1.verify()
        print("ERROR: Tamper not detected!")
    except AuditChainError as e:
        print(f"Tamper detected (payload): {e}")
    
    # Method 2: Modify HMAC signature
    tampered_chain2 = create_chain(secret_key="demo-key-12345", key_id="demo-001")
    for payload in events:
        signed = tampered_chain2.sign(payload)
        tampered_chain2.append(signed)
    
    # Tamper with HMAC
    tampered_chain2.events[1]["hmac"] = "0" * 64
    
    try:
        tampered_chain2.verify()
        print("ERROR: Tamper not detected!")
    except AuditChainError as e:
        print(f"Tamper detected (hmac): {e}")
    
    # Method 3: Reorder events
    tampered_chain3 = create_chain(secret_key="demo-key-12345", key_id="demo-001")
    for payload in events:
        signed = tampered_chain3.sign(payload)
        tampered_chain3.append(signed)
    
    # Reorder events
    tampered_chain3.events[1], tampered_chain3.events[2] = tampered_chain3.events[2], tampered_chain3.events[1]
    
    try:
        tampered_chain3.verify()
        print("ERROR: Reorder not detected!")
    except AuditChainError as e:
        print(f"Reorder detected: {e}")
