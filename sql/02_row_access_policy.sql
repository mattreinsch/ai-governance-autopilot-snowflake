-- 02_row_access_policy.sql
-- Defines a simple PII row access policy for demo purposes.
-- NOTE: Adapt this policy logic and roles for your real environment.

USE DATABASE GOVERNANCE_DB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE ROW ACCESS POLICY PII_ROW_POLICY AS
(FULL_NAME STRING, EMAIL STRING, PHONE STRING, CUSTOMER_TIER STRING)
RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() ILIKE '%DATA_ADMIN%' THEN TRUE
        ELSE TRUE  -- For demo, allow all; tighten this for real-world use
    END;
