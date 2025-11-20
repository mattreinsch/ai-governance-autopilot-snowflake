# 🛡️ AI Governance Autopilot (Snowflake + Cortex)

### AI-powered, self-driving data governance built entirely inside Snowflake.

This project turns Snowflake into an autonomous governance engine that monitors new data, classifies sensitivity with **Snowflake Cortex**, applies policies, and logs every action — automatically.

It accompanies my full breakdown on Medium:

📄 **[“The AI Governance Autopilot: How I Turned Snowflake Into a Self-Driving Policy Engine”](https://medium.com/@mattsreinsch/the-ai-governance-autopilot-how-i-turned-snowflake-into-a-self-driving-policy-engine-000f8971e3c5)**

---

## 🚀 What This System Does

This Autopilot converts Snowflake into an intelligent, proactive governance system that performs the following workflows:

### 🧠 1. AI Sensitivity Classification (Cortex)
For every column in a table, the system:
* Samples a subset of values.
* Sends a classification prompt to **Snowflake Cortex**.
* Returns one of the following labels:
    * `PII`
    * `CONFIDENTIAL`
    * `INTERNAL`
    * `PUBLIC`

> **Note:** All inference happens inside Snowflake — no external vector stores, no data movement.

### 🏷️ 2. Automated Tagging
Once classified, the Autopilot automatically applies a metadata tag.

```sql
ALTER TABLE <table_name>
MODIFY COLUMN <column_name> SET TAG DATA_SENSITIVITY = '<LABEL>';
```

This makes sensitivity queryable across:
* Lineage
* Impact analysis
* Access audits
* Catalog tools

### 🛡️ 3. Row Access Policy Enforcement
If any column is classified as **PII**, the system automatically attaches the defined row policy:

```sql
ALTER TABLE <table_name>
  SET ROW ACCESS POLICY PII_ROW_POLICY ON (id); -- Example mapping
```

* If the table already has a policy, the system logs a `POLICY_SKIPPED` event.
* This closes the gap between *"We detected PII"* and *"PII is now protected."*

### 💬 4. Real-Time Alerts (Optional)
You can integrate Slack, Teams, Email, or custom webhooks to receive alerts containing:
* Table name
* Sensitivity results
* Policies applied vs. skipped

### 📝 5. Full Governance Audit Logging
Actions are logged to a dedicated table (`GOVERNANCE_AUTOPILOT_LOG`) for a complete audit trail.

```sql
CREATE TABLE GOVERNANCE_AUTOPILOT_LOG (
  event_time   TIMESTAMP,
  object_type  STRING,
  object_name  STRING,
  column_name  STRING,
  action       STRING,
  details      STRING
);
```

---

## 🧩 Architecture Overview

```text
                ┌─────────────────────────────┐
                │     New / Existing Table     │
                │      (e.g., CUSTOMERS_DEMO)  │
                └──────────────┬──────────────┘
                               │
                               ▼
                 ┌────────────────────────┐
                 │  Cortex LLM Classifier │
                 │  (Column Sensitivity)  │
                 └───────────┬────────────┘
                             │ label
                             ▼
             ┌──────────────────────────────────┐
             │   Autotagging Engine (Snowpark)  │
             │ • Applies DATA_SENSITIVITY tags  │
             │ • Updates metadata               │
             └───────────────────┬──────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │   Policy Enforcement Layer     │
                  │ • Attaches PII_ROW_POLICY      │
                  │ • Skips if already applied     │
                  └────────────────────┬──────────┘
                                      │
                                      ▼
                      ┌────────────────────────────┐
                      │   Governance Audit Log      │
                      │  GOVERNANCE_AUTOPILOT_LOG   │
                      └────────────────────────────┘
```

---

## 📦 Repository Structure

```text
ai-governance-autopilot-snowflake/
│
├── notebooks/
│   └── ai_governance_autopilot_notebook.py  # Main Snowflake Notebook
│
├── sql/
│   ├── 01_setup_tags_and_log.sql            # DATA_SENSITIVITY tag
│   ├── 02_row_access_policy.sql.sql         # PII_ROW_POLICY
│   ├── 03_alerts_and_tasks.sql              # Audit log
│   
│
└── README.md
```

---

## ⚙️ Getting Started

### 1️⃣ Clone the Repository

```bash
git clone [https://github.com/mattreinsch/ai-governance-autopilot-snowflake.git](https://github.com/mattreinsch/ai-governance-autopilot-snowflake.git)
cd ai-governance-autopilot-snowflake
```

### 2️⃣ Open the Notebook in Snowflake
Upload `ai_governance_autopilot_notebook.py` to your Snowflake Notebooks environment.
* **Requirement:** Snowpark Python runtime.
* **Requirement:** Cortex enabled in your region.

### 3️⃣ Create Required Governance Objects
Run the following SQL commands in a worksheet or within the notebook setup cells.

**Sensitivity Tag:**
```sql
CREATE TAG IF NOT EXISTS DATA_SENSITIVITY
  COMMENT = 'Column sensitivity classification tag (PII, CONFIDENTIAL, INTERNAL, PUBLIC)';
```

**Row Access Policy:**
```sql
CREATE OR REPLACE ROW ACCESS POLICY PII_ROW_POLICY AS
  (id STRING) RETURNS BOOLEAN ->
    CURRENT_ROLE() IN ('DATA_PRIVACY', 'ACCOUNTADMIN');
```

**Audit Log Table:**
```sql
CREATE OR REPLACE TABLE GOVERNANCE_AUTOPILOT_LOG (
  event_time   TIMESTAMP,
  object_type  STRING,
  object_name  STRING,
  column_name  STRING,
  action       STRING,
  details      STRING
);
```

**Demo Data:**
```sql
CREATE OR REPLACE TABLE PUBLIC.CUSTOMERS_DEMO AS
SELECT 1 AS ID, 'John Doe' AS FULL_NAME, 'john@example.com' AS EMAIL,
       '+1-555-123-4567' AS PHONE, 'Gold' AS CUSTOMER_TIER
UNION ALL
SELECT 2, 'Jane Smith', 'jane@example.com', '+1-555-987-6543', 'Platinum';
```

### 4️⃣ Run the Autopilot
Execute the Python function in the notebook:

```python
classify_and_protect_table("PUBLIC.CUSTOMERS_DEMO")
```

**Expected actions:**
1.  Cortex classifies each column.
2.  `DATA_SENSITIVITY` tags are applied.
3.  Row policy is attached (if PII is detected).
4.  All actions are logged.

### 5️⃣ Inspect Results

**Check Tags:**
```sql
SELECT * FROM TABLE(
  INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('GOVERNANCE_DB.PUBLIC.DATA_SENSITIVITY')
);
```

**Check Logs:**
```sql
SELECT * FROM GOVERNANCE_AUTOPILOT_LOG
ORDER BY event_time DESC;
```

---

## 🧠 Why This Matters

Enterprises cannot scale AI safely without:
* Knowing where sensitive data lives.
* Applying consistent automated controls.
* Preventing unauthorized access.
* Maintaining transparent audit logs.

**This Autopilot provides the missing link for:**
* AI governance & LLM-safe data exposure.
* Enterprise MLOps.
* Self-service analytics with guardrails.
* Regulatory compliance automation.

---

## 🤝 Contributing

Ideas to extend this project:
* Region-based policies.
* Purpose-based access control.
* Snowflake Tasks for scheduled checking.
* Governance dashboards (Streamlit).

PRs and suggestions are welcome!

---

## 📬 Stay Connected

* 📰 **[Data Drift Newsletter](https://mattreinsch.github.io/DataDrift)**
* 🔗 **[LinkedIn](https://www.linkedin.com/in/mattreinsch)**
* 🌐 **[Website](https://mattreinsch.com)**
* ✍️ **[Medium](https://medium.com/@mattsreinsch)**

**⭐ Support:**
If this repo helped you, please star the repository, fork it, and tag me on LinkedIn if you build on top of it!
