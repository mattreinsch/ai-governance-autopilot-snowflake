-- 03_alerts_and_tasks.sql
-- Example of an alerting + task pattern for untagged tables.
-- This demo uses a simulated Slack notifier function.

USE DATABASE GOVERNANCE_DB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE FUNCTION NOTIFY_SLACK(payload VARIANT)
RETURNS STRING
LANGUAGE SQL
AS
$$
    SELECT 'Simulated Slack: ' || payload::string;
$$;

CREATE OR REPLACE PROCEDURE AUTOPILOT_ALERT_UNTAGGED()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE v_count INTEGER := 0;
BEGIN
  FOR rec IN (
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
      AND NOT EXISTS (
        SELECT 1
        FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_TAGS ot
        WHERE ot.OBJECT_NAME = TABLE_NAME
          AND ot.TAG_NAME = 'DATA_SENSITIVITY'
      )
  )
  DO
    -- Simulated Slack notification
    SELECT NOTIFY_SLACK(
      OBJECT_CONSTRUCT('text', 'New untagged table: ' || rec.TABLE_SCHEMA || '.' || rec.TABLE_NAME)
    );

    INSERT INTO GOVERNANCE_AUTOPILOT_LOG(OBJECT_TYPE, OBJECT_NAME, COLUMN_NAME, ACTION, DETAILS)
    VALUES('TABLE', rec.TABLE_SCHEMA || '.' || rec.TABLE_NAME, NULL, 'ALERT_UNTAGGED_TABLE', 'Missing DATA_SENSITIVITY tags');

    v_count := v_count + 1;
  END FOR;

  RETURN 'Processed ' || v_count || ' untagged tables.';
END;
$$;

CREATE OR REPLACE TASK AUTOPILOT_GOVERNANCE_TASK
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'USING CRON 0 */1 * * * UTC'  -- every hour
AS
  CALL AUTOPILOT_ALERT_UNTAGGED();
