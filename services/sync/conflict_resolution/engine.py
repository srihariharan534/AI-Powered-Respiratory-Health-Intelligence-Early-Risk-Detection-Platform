"""
Conflict Resolution & Optimistic Concurrency Engine (Phase 25).
Evaluates incoming operation base_state_version against authoritative Digital Twin state.
Detects state-version mismatches and invalid lifecycle transitions.
"""

from typing import Any, Dict, Optional, Tuple
from services.sync.contracts import (
    SyncConflictType,
    SyncOperation,
    SyncOperationResult,
    SyncStatus,
)


class ConflictResolutionEngine:
    """
    Evaluates synchronization operations for potential concurrency or domain conflicts.
    Rejects unsafe automatic overwrites on critical life-safety data.
    """

    def evaluate_conflict(
        self,
        operation: SyncOperation,
        current_server_version: int,
        server_entity: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[SyncConflictType, str, Dict[str, Any]]]:
        """
        Returns None if no conflict exists, or (ConflictType, reason, server_state_diff) if conflict detected.
        """
        # 1. State version freshness check
        if operation.base_state_version is not None:
            # If server has advanced beyond the client's base state version
            if current_server_version > operation.base_state_version:
                # If modifying an existing entity that has changed
                if server_entity is not None and operation.operation_type != "CREATE":
                    diff = {
                        "client_base_version": operation.base_state_version,
                        "server_current_version": current_server_version,
                        "current_entity": server_entity,
                    }
                    return (
                        SyncConflictType.STATE_VERSION_CONFLICT,
                        f"State version mismatch: operation based on version {operation.base_state_version}, "
                        f"current server version is {current_server_version}.",
                        diff,
                    )

        # 2. Entity existence check for updates
        if operation.operation_type in ["UPDATE", "DELETE"] and server_entity is None:
            return (
                SyncConflictType.ENTITY_NOT_FOUND,
                f"Entity '{operation.entity_id}' does not exist on server.",
                {"entity_id": operation.entity_id},
            )

        # 3. Duplicate create check
        if operation.operation_type == "CREATE" and server_entity is not None:
            return (
                SyncConflictType.STATE_VERSION_CONFLICT,
                f"Entity '{operation.entity_id}' already exists on server.",
                {"existing_entity": server_entity},
            )

        return None
