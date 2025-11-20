
"""AI Governance Autopilot core module for Snowflake + Cortex.

This module provides:
  - Column sensitivity classification using Snowflake Cortex
  - Automatic DATA_SENSITIVITY tagging
  - Optional PII row access policy enforcement
  - Governance audit logging

Typical usage inside a Snowflake Notebook:

    from autopilot import classify_and_protect_table

    classify_and_protect_table("PUBLIC.CUSTOMERS_DEMO")

Requirements:
  - Snowpark Python enabled
  - Cortex enabled in the Snowflake account
  - DATA_SENSITIVITY tag and GOVERNANCE_AUTOPILOT_LOG table created
  - PII_ROW_POLICY row access policy defined
"""

from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
import snowflake.cortex as cortex


def _get_session() -> Session:
    """Return the active Snowflake session.

    In a Snowflake Notebook, get_active_session() is available.
    This helper keeps the module flexible if imported elsewhere.
    """
    try:
        return get_active_session()
    except Exception as exc:  # pragma: no cover - fallback for local testing
        raise RuntimeError(
            "No active Snowflake session found. "
            "This module is intended to run inside a Snowflake Notebook."
        ) from exc


def classify_column_sensitivity(col_name: str, values: list[str], model: str = "llama3.1-8b") -> str:
    """Classify a column's sensitivity using a Cortex model.

    Parameters
    ----------
    col_name : str
        Name of the column.
    values : list[str]
        Sampled values from the column.
    model : str
        Cortex model name to use for classification.

    Returns
    -------
    str
        One of: PII, CONFIDENTIAL, INTERNAL, PUBLIC
    """
    session = _get_session()

    # Limit values in the prompt for safety / size
    sample_values = values[:5]

    prompt = f"""Classify this column's sensitivity.
Column: {col_name}
Values: {sample_values}
Labels: PII, CONFIDENTIAL, INTERNAL, PUBLIC
Return only the label."""

    result = cortex.complete(model=model, prompt=prompt, session=session)
    label = str(result).strip().upper()
    allowed = {"PII", "CONFIDENTIAL", "INTERNAL", "PUBLIC"}
    return label if label in allowed else "INTERNAL"


def classify_and_protect_table(full_table_name: str) -> None:
    """Run the full governance Autopilot on a Snowflake table.

    Steps:
      1. Sample rows from the table
      2. Use Cortex to classify each column's sensitivity
      3. Apply DATA_SENSITIVITY tag per column
      4. Attach PII_ROW_POLICY if any column is PII
      5. Write all actions to GOVERNANCE_AUTOPILOT_LOG

    Parameters
    ----------
    full_table_name : str
        Fully qualified table name (e.g. 'PUBLIC.CUSTOMERS_DEMO').
    """
    session = _get_session()

    print(f"=== Running AI Governance Autopilot for {full_table_name} ===")

    df = session.table(full_table_name)
    sample_pdf = df.limit(10).to_pandas()

    has_pii = False

    # Ensure the log table exists (optional safety)
    session.sql("""CREATE TABLE IF NOT EXISTS GOVERNANCE_AUTOPILOT_LOG (
            EVENT_TIME   TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            OBJECT_TYPE  STRING,
            OBJECT_NAME  STRING,
            COLUMN_NAME  STRING,
            ACTION       STRING,
            DETAILS      STRING
        );
    """).collect()

    for col_name in sample_pdf.columns:
        values = sample_pdf[col_name].astype(str).tolist()
        raw_label = classify_column_sensitivity(col_name, values)
        label = raw_label.upper()

        print(f"  → Cortex classified {col_name} as: {label} (raw: {raw_label})")

        # Apply DATA_SENSITIVITY tag
        tag_sql = f"""ALTER TABLE {full_table_name}
        MODIFY COLUMN {col_name}
        SET TAG DATA_SENSITIVITY = '{label}'"""
        session.sql(tag_sql).collect()

        log_sql = f"""INSERT INTO GOVERNANCE_AUTOPILOT_LOG
        (OBJECT_TYPE, OBJECT_NAME, COLUMN_NAME, ACTION, DETAILS)
        VALUES('TABLE', '{full_table_name}', '{col_name}', 'TAG_APPLIED', 'DATA_SENSITIVITY={label}')"""
        session.sql(log_sql).collect()

        if label == "PII":
            has_pii = True

    if has_pii:
        print(f"PII detected in {full_table_name} → ensuring PII_ROW_POLICY is attached...")
        # Try to attach policy; if already present, log and continue
        try:
            policy_sql = f"""ALTER TABLE {full_table_name}
            SET ROW ACCESS POLICY PII_ROW_POLICY"""
            session.sql(policy_sql).collect()

            log_policy = f"""INSERT INTO GOVERNANCE_AUTOPILOT_LOG
            (OBJECT_TYPE, OBJECT_NAME, COLUMN_NAME, ACTION, DETAILS)
            VALUES('TABLE', '{full_table_name}', NULL, 'POLICY_ATTACHED', 'PII_ROW_POLICY')"""
            session.sql(log_policy).collect()
        except Exception as e:
            print(f"  Table already has a ROW ACCESS POLICY or attach failed: {e}")
            log_skip = f"""INSERT INTO GOVERNANCE_AUTOPILOT_LOG
            (OBJECT_TYPE, OBJECT_NAME, COLUMN_NAME, ACTION, DETAILS)
            VALUES('TABLE', '{full_table_name}', NULL, 'POLICY_SKIPPED', 'ROW_ACCESS_POLICY already present or attach failed')"""
            session.sql(log_skip).collect()
    else:
        print(f"No PII detected in {full_table_name} → no row policy attached.")

    print("=== Autopilot classification complete ===")
