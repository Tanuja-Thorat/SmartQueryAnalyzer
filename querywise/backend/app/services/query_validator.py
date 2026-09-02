"""
Query Validator

Responsible for making sure only safe, read-only SELECT queries ever reach
the database. This is the most important safety layer in the whole app.
"""
import re
import sqlparse

# Keywords that must never appear as the leading statement type, and are
# also blocked anywhere as a safety net against SQL injection tricks like
# stacked queries ("SELECT 1; DROP TABLE users;").
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "CALL", "COPY",
    "VACUUM", "REINDEX", "MERGE", "REPLACE",
]

# A very small allow-list of characters/patterns we consider suspicious
# stacked-query attempts (multiple statements separated by `;`).
STACKED_QUERY_PATTERN = re.compile(r";\s*\S")


class QueryValidationError(Exception):
    """Raised when a query fails validation. Message is safe to show to users."""
    pass


def validate_query(raw_query: str) -> str:
    """
    Validates a raw SQL string submitted by the user.

    Returns the cleaned query (whitespace trimmed, trailing semicolon removed)
    if valid, otherwise raises QueryValidationError with a friendly message.
    """
    if raw_query is None or not raw_query.strip():
        raise QueryValidationError("Please enter a SQL query to analyze.")

    query = raw_query.strip()

    # Strip a single trailing semicolon (common and harmless)
    query_no_trailing = query.rstrip(";").strip()

    # Detect stacked queries (more than one statement)
    parsed_statements = [
        s for s in sqlparse.parse(query_no_trailing) if s.token_first(skip_cm=True)
    ]
    if len(parsed_statements) != 1:
        raise QueryValidationError(
            "Only a single SELECT statement is allowed per request."
        )

    statement = parsed_statements[0]
    statement_type = statement.get_type()  # e.g. "SELECT", "INSERT", "UNKNOWN"

    if statement_type != "SELECT":
        raise QueryValidationError(
            "Only SELECT queries are allowed for security reasons."
        )

    # Defense in depth: scan the raw text for forbidden keywords as whole words
    upper_query = query_no_trailing.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_query):
            raise QueryValidationError(
                "Only SELECT queries are allowed for security reasons."
            )

    # Basic syntax sanity check via sqlparse (catches badly malformed SQL)
    if not query_no_trailing.lower().lstrip().startswith("select"):
        raise QueryValidationError(
            "Only SELECT queries are allowed for security reasons."
        )

    return query_no_trailing
