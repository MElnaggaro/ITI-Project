"""Permission evaluation service and row-filter DSL validation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.column_permission import ColumnPermission
from models.database_column import DatabaseColumn
from models.table_permission import TablePermission
from repositories.permission_repository import PermissionRepository
from repositories.role_repository import RoleRepository

ALLOWED_FILTER_OPERATORS = frozenset(
    {"eq", "ne", "gt", "gte", "lt", "lte", "in", "like", "is_null", "and", "or"}
)
ALLOWED_MASK_TYPES = frozenset({"redact", "last4", "hash"})


@dataclass(frozen=True, slots=True)
class EffectiveColumnPermission:
    """Resolved column access rule and masking policy."""

    column_id: UUID
    column_name: str
    can_read: bool
    can_filter: bool
    can_aggregate: bool
    mask_type: str | None


@dataclass(frozen=True, slots=True)
class EffectiveTablePermission:
    """Resolved table access rule and combined row-filter policy."""

    can_read: bool
    can_insert: bool
    can_update: bool
    can_delete: bool
    effective_row_filters: list[dict[str, Any]] = field(default_factory=list)
    column_rules: dict[str, EffectiveColumnPermission] = field(default_factory=dict)


def validate_row_filter_dsl(row_filter: dict[str, Any], max_depth: int = 5) -> None:
    """Validate structure and operators of a row_filter JSON DSL object."""
    if not isinstance(row_filter, dict):
        raise ValueError("row_filter must be a dictionary object.")
    if not row_filter:
        return  # Empty dict is valid unrestricted filter for an authorized grant

    def _validate_node(node: Any, depth: int) -> None:
        if depth > max_depth:
            raise ValueError(f"row_filter exceeds maximum nesting depth of {max_depth}.")
        if not isinstance(node, dict):
            raise ValueError("Filter nodes must be JSON objects.")

        for key, val in node.items():
            key_str = str(key).lower()
            if key_str in {"and", "or"}:
                if not isinstance(val, list):
                    raise ValueError(f"'{key_str}' operator value must be a list of filter conditions.")
                for sub_node in val:
                    _validate_node(sub_node, depth + 1)
            elif key_str in ALLOWED_FILTER_OPERATORS:
                if not isinstance(val, dict) or "column" not in val:
                    raise ValueError(f"Operator '{key_str}' requires a target 'column' property.")
            else:
                # Direct column clause check e.g. {"field_name": {"eq": "val"}}
                if isinstance(val, dict):
                    for op_key in val.keys():
                        if str(op_key).lower() not in ALLOWED_FILTER_OPERATORS:
                            raise ValueError(f"Unsupported row_filter operator: '{op_key}'")
                else:
                    raise ValueError(f"Invalid row_filter clause key: '{key}'")

    _validate_node(row_filter, depth=1)


class PermissionService:
    """Permission resolution service enforcing fail-closed security invariants."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.perm_repo = PermissionRepository(session)
        self.role_repo = RoleRepository(session)

    def resolve_effective_table_permission(
        self,
        tenant_id: UUID | str,
        user_id: UUID | str,
        connection_id: UUID | str,
        table_id: UUID | str,
    ) -> EffectiveTablePermission:
        """Resolve unambiguous effective table & column permissions using direct-grant precedence and additive roles."""
        # 1. Check direct user grant
        direct_grant = self.perm_repo.get_direct_user_grant(
            tenant_id=tenant_id,
            user_id=user_id,
            connection_id=connection_id,
            table_id=table_id,
        )

        effective_grants: list[TablePermission] = []
        if direct_grant is not None:
            # Direct user grant is sole authority if present
            if direct_grant.can_read:
                effective_grants.append(direct_grant)
            else:
                # Explicit denial
                return EffectiveTablePermission(can_read=False, can_insert=False, can_update=False, can_delete=False)
        else:
            # Additive role grants
            user_roles = self.role_repo.get_user_roles(tenant_id, user_id)
            role_ids = [r.id for r in user_roles]
            role_grants = self.perm_repo.get_role_grants_for_user(
                tenant_id=tenant_id,
                role_ids=role_ids,
                connection_id=connection_id,
                table_id=table_id,
            )
            effective_grants = [g for g in role_grants if g.can_read]

        if not effective_grants:
            from models.user import User
            user_obj = self.session.scalar(
                select(User).where(User.id == user_id).where(User.tenant_id == tenant_id)
            )
            if user_obj and user_obj.is_tenant_admin:
                cols = list(
                    self.session.scalars(
                        select(DatabaseColumn).where(DatabaseColumn.table_id == table_id)
                    ).all()
                )
                col_rules = {
                    c.column_name: EffectiveColumnPermission(
                        column_id=c.id,
                        column_name=c.column_name,
                        can_read=True,
                        can_filter=True,
                        can_aggregate=True,
                        mask_type=None,
                    )
                    for c in cols
                }
                return EffectiveTablePermission(
                    can_read=True,
                    can_insert=True,
                    can_update=True,
                    can_delete=True,
                    effective_row_filters=[],
                    column_rules=col_rules,
                )

            return EffectiveTablePermission(can_read=False, can_insert=False, can_update=False, can_delete=False)

        # Combine row filters from effective read grants
        filters = [g.row_filter for g in effective_grants if g.row_filter]

        # Resolve column rules
        column_rules = self._resolve_column_rules(table_id, effective_grants)

        return EffectiveTablePermission(
            can_read=True,
            can_insert=any(g.can_insert for g in effective_grants),
            can_update=any(g.can_update for g in effective_grants),
            can_delete=any(g.can_delete for g in effective_grants),
            effective_row_filters=filters,
            column_rules=column_rules,
        )

    def _resolve_column_rules(
        self,
        table_id: UUID | str,
        grants: list[TablePermission],
    ) -> dict[str, EffectiveColumnPermission]:
        """Fetch columns and merge column permission rules across effective grants."""
        columns = list(
            self.session.scalars(
                select(DatabaseColumn).where(DatabaseColumn.table_id == table_id)
            ).all()
        )

        grant_ids = [g.id for g in grants]
        col_perms = list(
            self.session.scalars(
                select(ColumnPermission).where(ColumnPermission.table_permission_id.in_(grant_ids))
            ).all()
        ) if grant_ids else []

        col_perm_map: dict[UUID, list[ColumnPermission]] = {}
        for cp in col_perms:
            col_perm_map.setdefault(cp.column_id, []).append(cp)

        result: dict[str, EffectiveColumnPermission] = {}
        for col in columns:
            cp_list = col_perm_map.get(col.id, [])
            if not cp_list:
                can_read = True
                can_filter = True
                can_aggregate = True
                mask_type = "redact" if col.is_sensitive else None
            else:
                can_read = any(cp.can_read for cp in cp_list)
                can_filter = any(cp.can_filter for cp in cp_list)
                can_aggregate = any(cp.can_aggregate for cp in cp_list)
                # First non-null mask_type or default to redact if sensitive
                specified_masks = [cp.mask_type for cp in cp_list if cp.mask_type]
                mask_type = specified_masks[0] if specified_masks else ("redact" if col.is_sensitive else None)

            result[col.column_name] = EffectiveColumnPermission(
                column_id=col.id,
                column_name=col.column_name,
                can_read=can_read,
                can_filter=can_filter,
                can_aggregate=can_aggregate,
                mask_type=mask_type,
            )

        return result
