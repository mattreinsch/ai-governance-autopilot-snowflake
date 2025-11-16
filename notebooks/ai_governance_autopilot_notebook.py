from snowflake.snowpark import Session
import snowflake.cortex as cortex

session = get_active_session()

def classify_column_sensitivity(col_name, values):
    prompt = f"""Classify this column's sensitivity.
Column: {col_name}
Values: {values[:5]}
Labels: PII, CONFIDENTIAL, INTERNAL, PUBLIC
Return only the label."""
    model = "llama3.1-8b"
    result = cortex.complete(model=model, prompt=prompt, session=session)
    label = str(result).strip().upper()
    allowed = {"PII","CONFIDENTIAL","INTERNAL","PUBLIC"}
    return label if label in allowed else "INTERNAL"

def classify_and_protect_table(full_table_name):
    df = session.table(full_table_name)
    sample = df.limit(10).to_pandas()

    has_pii = False

    for col_name in sample.columns:
        values = sample[col_name].astype(str).tolist()
        label = classify_column_sensitivity(col_name, values)

        session.sql(f"""ALTER TABLE {full_table_name}
        MODIFY COLUMN {col_name}
        SET TAG DATA_SENSITIVITY='{label}';""").collect()

        session.sql(f"""INSERT INTO GOVERNANCE_AUTOPILOT_LOG
        (OBJECT_TYPE,OBJECT_NAME,COLUMN_NAME,ACTION,DETAILS)
        VALUES('TABLE','{full_table_name}','{col_name}','TAG_APPLIED','{label}');""").collect()

        if label == "PII":
            has_pii = True

    if has_pii:
        session.sql(f"""ALTER TABLE {full_table_name}
        SET ROW ACCESS POLICY PII_ROW_POLICY;""").collect()

        session.sql(f"""INSERT INTO GOVERNANCE_AUTOPILOT_LOG
        (OBJECT_TYPE,OBJECT_NAME,ACTION,DETAILS)
        VALUES('TABLE','{full_table_name}','POLICY_ATTACHED','PII_ROW_POLICY');""").collect()

    print("Autopilot classification complete.")

classify_and_protect_table("PUBLIC.CUSTOMERS_DEMO")
