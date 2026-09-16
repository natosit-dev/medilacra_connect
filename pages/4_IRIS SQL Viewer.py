import os
import platform
import sys

import streamlit as st
from dotenv import load_dotenv

try:
    from iris import dbapi as iris_dbapi
    IRIS_IMPORT_ERROR = None
except ImportError as exc:
    iris_dbapi = None
    IRIS_IMPORT_ERROR = exc


# Load local connection settings. Unlike the old ODBC path, these values are
# sufficient to recreate the connection on a new machine without a DSN.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

IRIS_HOST = os.getenv("IRIS_HOST", "127.0.0.1")
IRIS_PORT_RAW = os.getenv("IRIS_PORT", "1972")
IRIS_NAMESPACE = os.getenv("IRIS_NAMESPACE", "PIQITT")
IRIS_USER = os.getenv("IRIS_USER", "_SYSTEM")
IRIS_PASSWORD = os.getenv("IRIS_PASSWORD", "")

st.subheader("IRIS SQL Viewer")
st.write(
    f"Python: {sys.version.split()[0]}  |  "
    f"Arch: {platform.architecture()[0]}  |  "
    f"OS: {platform.system()}"
)

if iris_dbapi is None:
    st.error("The InterSystems Python DB-API client is not installed.")
    st.code(str(IRIS_IMPORT_ERROR))
    st.code("pip install -r requirements.txt", language="bash")
    st.stop()

try:
    IRIS_PORT = int(IRIS_PORT_RAW)
except ValueError:
    st.error(f"IRIS_PORT must be an integer; got {IRIS_PORT_RAW!r}.")
    st.stop()

if not IRIS_PASSWORD:
    st.error("IRIS_PASSWORD is not set in the repo-root .env file.")
    st.stop()

st.write(
    "IRIS target: "
    f"`{IRIS_HOST}:{IRIS_PORT}/{IRIS_NAMESPACE}` | User: `{IRIS_USER}`"
)
st.caption("Direct InterSystems DB-API connection — no ODBC driver or DSN required.")


@st.cache_resource
def get_conn():
    return iris_dbapi.connect(
        hostname=IRIS_HOST,
        port=IRIS_PORT,
        namespace=IRIS_NAMESPACE,
        username=IRIS_USER,
        password=IRIS_PASSWORD,
    )


def run_sql(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        if cur.description is None:
            return [], []

        rows = cur.fetchall()
        cols = [column[0] for column in cur.description]
        return cols, rows
    finally:
        cur.close()


def show_query(title, sql):
    st.subheader(title)
    try:
        cols, rows = run_sql(sql)
    except Exception as exc:
        st.error(str(exc))
        return

    st.write(f"Rows returned: {len(rows)}")
    if rows:
        st.dataframe(
            [{cols[i]: row[i] for i in range(len(cols))} for row in rows],
            use_container_width=True,
        )


status_col, reconnect_col = st.columns([4, 1])
with status_col:
    try:
        get_conn()
        st.success("Connected to IRIS.")
    except Exception as exc:
        st.error("IRIS connection failed.")
        st.code(str(exc))
        st.info(
            "Check IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, IRIS_USER, and "
            "IRIS_PASSWORD in the repo-root .env file."
        )
        st.stop()

with reconnect_col:
    if st.button("Reconnect"):
        get_conn.clear()
        st.rerun()

show_query("IRIS Demo.PatientMsg", "SELECT TOP 5 * FROM Demo.PatientMsg")
show_query("IRIS Demo.Observation", "SELECT TOP 5 * FROM Demo.Observation")
