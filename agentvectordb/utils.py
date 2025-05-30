# For MVP, this file can be minimal if AgentMemoryCollection emphasizes filter_sql.
# The advanced build_filter_sql is complex to get right for all cases.
# If not used by Collection.query, it can be removed or kept as an optional utility.
# For now, keeping it as it was developed, but it's not critical for MVP Collection.query.

from typing import Any, Dict


def _format_sql_value(value: Any) -> str:
    if isinstance(value, str):
        return "'{}'".format(str(value).replace("'", "''"))
    elif isinstance(value, bool):
        return str(value).lower()
    elif value is None:
        return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    raise ValueError(f"Unsupported value type for direct SQL formatting: {type(value)}")


def _parse_condition(key: str, value: Any) -> str:
    safe_key = key
    if isinstance(value, dict):
        if len(value) != 1:
            raise ValueError(f"Operator sub-dictionary for key '{safe_key}' must have one operator: {value}")
        op, op_val = list(value.items())[0]

        if isinstance(op_val, list):
            if not op_val:
                if op in ("$in", "$has_any", "$has_all"):
                    return "1 = 0"  # False
                if op == "$nin":
                    return "1 = 1"  # True
            list_vals_sql = ", ".join([_format_sql_value(v) for v in op_val])
        else:
            op_val_sql = _format_sql_value(op_val)

        op_map = {"$gt": ">", "$gte": ">=", "$lt": "<", "$lte": "<=", "$ne": "!=", "$like": "LIKE"}
        if op in op_map:
            return f"{safe_key} {op_map[op]} {op_val_sql}"
        if op == "$in":
            return f"{safe_key} IN ({list_vals_sql})"
        if op == "$nin":
            return f"{safe_key} NOT IN ({list_vals_sql})"
        if op == "$startswith":
            return f"STARTSWITH({safe_key}, {op_val_sql})"
        if op == "$endswith":
            return f"ENDSWITH({safe_key}, {op_val_sql})"
        if op == "$contains":
            return f"list_contains({safe_key}, {op_val_sql})"
        if op == "$has_any":
            return f"array_has_any({safe_key}, [{list_vals_sql}])"
        if op == "$has_all":
            return f"array_has_all({safe_key}, [{list_vals_sql}])"
        raise ValueError(f"Unsupported operator '{op}' for key '{safe_key}'")
    else:
        val_sql = _format_sql_value(value)
        return f"{safe_key} IS NULL" if val_sql == "NULL" else f"{safe_key} = {val_sql}"


def build_filter_sql(filters: Dict[str, Any]) -> str:
    if not filters:
        return ""
    conditions, logical_ops_clauses = [], []
    for key, value in filters.items():
        op_key_lower = key.lower()
        if op_key_lower == "$and":
            if not isinstance(value, list):
                raise ValueError("$and requires a list.")
            sub_clauses = [build_filter_sql(cond) for cond in value if cond]
            if sub_clauses_filtered := [sc for sc in sub_clauses if sc]:
                logical_ops_clauses.append(f"({ ' AND '.join(sub_clauses_filtered) })")
        elif op_key_lower == "$or":
            if not isinstance(value, list):
                raise ValueError("$or requires a list.")
            sub_clauses = [build_filter_sql(cond) for cond in value if cond]
            if sub_clauses_filtered := [sc for sc in sub_clauses if sc]:
                logical_ops_clauses.append(f"({ ' OR '.join(sub_clauses_filtered) })")
        elif op_key_lower == "$not":
            if not isinstance(value, dict) or not value:
                raise ValueError("$not requires a non-empty dict.")
            if not_clause := build_filter_sql(value):
                logical_ops_clauses.append(f"NOT ({not_clause})")
        else:
            try:
                conditions.append(_parse_condition(key, value))
            except ValueError as e:
                print(f"Warning: Skipping filter for key '{key}': {e}")

    field_conditions_sql = " AND ".join(filter(None, conditions))
    all_clauses = [cl for cl in [field_conditions_sql] + list(filter(None, logical_ops_clauses)) if cl]
    return " AND ".join(all_clauses)
