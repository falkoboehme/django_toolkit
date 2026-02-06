CREATE OR REPLACE FUNCTION public.write_history()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$

/*
        Purpose: Make a history of changes to most fields in the table calling this trigger function.
        This kind of history tracking is also known as an "audit trail".
        This function works by detecting each change in value for important fields in a certain table.
        This trigger function then calls another function to create a row in the "history_" table.

        If you want audition on table foo, you can create a trigger on that table like this:
        CREATE TRIGGER foo_trigger_history
        AFTER INSERT OR UPDATE OR DELETE
        ON foo
        FOR EACH ROW
        EXECUTE PROCEDURE write_history();

        If you do not want to track changes to a column, you can add '!history' to the column comment. For example:
        COMMENT ON COLUMN foo.bar IS 'This is an unimportant column. !history';

        === with Partitioning (hist_table_name) ===
        CREATE TABLE public.history
        (
                hist_datetime timestamp with time zone,
                hist_table_name text,
                hist_table_oid oid,
                hist_table_pk text,
                hist_table_old_pk text,
                hist_table_new_pk text,
                hist_column_name text,
                hist_old_value text,
                hist_new_value text,
                hist_txid bigint,
                hist_operation text
        ) PARTITION BY RANGE (hist_datetime)
                WITH (
                OIDS=FALSE
        );

        CREATE TRIGGER TABLE_trigger_history
        AFTER INSERT OR UPDATE OR DELETE
        ON TABLE_trigger_history
        FOR EACH ROW
        EXECUTE PROCEDURE write_history();


        === without Partitioning ===
        CREATE TABLE public.history
        (
                hist_datetime timestamp with time zone,
                hist_table_name text,
                hist_table_oid oid,
                hist_table_pk text,
                hist_table_old_pk text,
                hist_table_new_pk text,
                hist_column_name text,
                hist_old_value text,
                hist_new_value text,
                hist_txid bigint,
                hist_operation text
        )
                WITH (
                OIDS=FALSE
        );

        CREATE INDEX "I.HistTableName_HistTableNewPk_HistTimestamp"
        ON public.history
        USING btree
        (hist_table_name COLLATE pg_catalog."default", hist_table_new_pk COLLATE pg_catalog."default", hist_timestamp);

*/

/*
        Notes:

        The 'OLD' and 'NEW' variables represent the entire row whose INSERT/UPDATE/DELETE caused this trigger to run.
        The 'TG_xxx' variables are special variables created automatically by Postgres for the trigger function.
        For example, TG_OP indicates which modification operation is happening: INSERT, UPDATE, or DELETE.
        http://www.postgresql.org/docs/current/static/plpgsql-trigger.html
        "clock_timestamp()" gets the actual time at the moment of execution. In contrast, most other timestamp
        functions return the time when the current transaction began.
        For more information, see: http://www.postgresql.org/docs/current/static/functions-datetime.html
*/

DECLARE
        ri RECORD; -- About this data type "RECORD": http://www.postgresql.org/docs/current/static/plpgsql-declarations.html#PLPGSQL-DECLARATION-RECORDS
        oldValue TEXT;
        newValue TEXT;
        PkArray TEXT[]; -- Columns of PK
        oldPkArray TEXT[]; -- Content of old PK
        newPkArray TEXT[]; -- Content of new PK
        change_datetime timestamp without time zone;
        isHistoryColumn BOOLEAN;
        isValueModified BOOLEAN;
BEGIN
-- RAISE NOTICE E'Start: %',clock_timestamp();
-- Debug
/*
RAISE NOTICE E'\n    Running function: make_history_ ----------------\n\n    Operation: %\n    Schema: %\n    Table: %\n',
TG_OP,
TG_TABLE_SCHEMA,
TG_TABLE_NAME;
*/

        change_datetime = now();

        -- Get the primary key
        FOR ri IN
                SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
                FROM   pg_index i
                JOIN   pg_attribute a ON (a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey))
                WHERE  i.indrelid = quote_ident(TG_TABLE_NAME)::regclass
                AND    i.indisprimary
        LOOP
                -- save primary key in array
                -- NEW value
                IF (TG_OP = 'DELETE')
                THEN
                        newValue := '';
                ELSE
                        EXECUTE 'SELECT ($1).' || ri.attname || '::text' INTO newValue USING NEW;
                END IF;
                -- OLD value
                IF (TG_OP = 'INSERT')
                THEN
                        oldValue := '';
                ELSE
                        EXECUTE 'SELECT ($1).' || ri.attname || '::text' INTO oldValue USING OLD;
                END IF;

                PkArray = array_append(PkArray, ri.attname::text);
                oldPkArray = array_append(oldPkArray, oldValue);
                newPkArray = array_append(newPkArray, newValue);
        END LOOP;
-- Debug
/*
RAISE NOTICE E'\n  PkArray:%\n  oldPkArray:%\n  newPkArray:%\n',
PkArray,
oldPkArray,
newPkArray;
*/

        FOR ri IN
                -- Fetch a ResultSet listing columns defined for this trigger's table.
                SELECT t.relid, c.table_name, c.column_name, c.ordinal_position, d.description FROM information_schema.columns c
                LEFT JOIN pg_catalog.pg_statio_all_tables t ON (c.table_schema=t.schemaname AND c.table_name=relname)
                LEFT JOIN pg_catalog.pg_description d ON (t.relid=d.objoid AND c.ordinal_position=d.objsubid)
                WHERE table_schema = quote_ident(TG_TABLE_SCHEMA)
                        AND table_name = quote_ident(TG_TABLE_NAME)
                ORDER BY c.table_name, c.ordinal_position
        LOOP
                -- For each column in this trigger's table, copy the OLD & NEW values into respective variables.
                EXECUTE 'SELECT ($1).' || ri.column_name || '::text' INTO newValue USING NEW;
                EXECUTE 'SELECT ($1).' || ri.column_name || '::text' INTO oldValue USING OLD;

                IF (TG_OP = 'INSERT')    -- If operation is an INSERT, we have no OLD value, so use an empty string.
                THEN
                        oldValue := ''::varchar;
                END IF;
                IF (TG_OP = 'DELETE')    -- If operation is an DELETE, we have no NEW value, so use an empty string.
                THEN
                        newValue := ''::varchar;
                END IF;

                -- is the column a history column (without '!history' in column comment)
                IF (position( '!history' in ri.description ) = 0 IS FALSE)
                THEN
                        isHistoryColumn := FALSE;
                ELSE
                        isHistoryColumn := TRUE;
                END IF;

                IF isHistoryColumn
                THEN
                        -- Be careful if one value is NULL
                        IF ((oldValue IS NULL and newValue IS NOT NULL) OR
                                (oldValue IS NOT NULL and newValue IS NULL) OR
                                (oldValue != newValue)
                        ) THEN
                                isValueModified := TRUE;
                        ELSE
                                isValueModified := FALSE;
                        END IF;

                        IF isValueModified
                        THEN
                                INSERT INTO history (hist_datetime, hist_table_name, hist_table_oid, hist_table_pk, hist_table_old_pk, hist_table_new_pk, hist_column_name, hist_old_value, hist_new_value, hist_txid, hist_operation)
                                VALUES (change_datetime, TG_TABLE_NAME, TG_RELID, PkArray, oldPkArray, newPkArray, ri.column_name::text, oldValue::text, newValue::text, txid_current(), TG_OP);
                        END IF;
                END IF;
        END LOOP;

        IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE')
        THEN
                RETURN NEW;
        ELSIF (TG_OP = 'DELETE')
        THEN
                RETURN OLD;
        END IF;
        /* Should never reach this point. Branching in code above should always reach a call to RETURN. */
        RAISE EXCEPTION 'Unexpectedly reached the bottom of this function without calling RETURN.';
END;


$function$