import os
import platform
import sys

import streamlit as st
from dotenv import load_dotenv

try:
    import pyodbc
    PYODBC_IMPORT_ERROR = None
except ImportError as exc:
    pyodbc = None
    PYODBC_IMPORT_ERROR = exc


# Load variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

st.subheader("IRIS SQL Viewer")
st.write(
    f"Python: {sys.version.split()[0]}  |  "
    f"Arch: {platform.architecture()[0]}  |  "
    f"OS: {platform.system()}"
)

if pyodbc is None:
    st.error("pyodbc could not load its native ODBC dependency.")
    st.code(str(PYODBC_IMPORT_ERROR))
    if sys.platform.startswith("linux"):
        st.markdown(
            "On Debian/Ubuntu/WSL, install the unixODBC runtime first. "
            "The `libodbc.so.2` error is below the IRIS DSN layer: Python cannot load the ODBC driver manager yet."
        )
        st.code(
            "sudo apt update\n"
            "sudo apt install -y unixodbc unixodbc-dev\n"
            "python -c \"import pyodbc; print(pyodbc.version); print(pyodbc.drivers())\"",
            language="bash",
        )
    else:
        st.markdown(
            "Install a system ODBC driver manager for this operating system, then restart Streamlit."
        )
    st.stop()

odbc_drivers = pyodbc.drivers()
odbc_sources = pyodbc.dataSources()
dsn = os.getenv("IRIS_DSN", "iris")
user = os.getenv("IRIS_USER", "demoapp")

st.write("ODBC drivers:", odbc_drivers)
st.write("ODBC data sources:", odbc_sources)
st.write(f"Configured IRIS DSN: `{dsn}` | User: `{user}`")

if not odbc_drivers:
    st.warning(
        "unixODBC is available, but no ODBC drivers are registered. "
        "Install/register the InterSystems IRIS ODBC client driver next."
    )

if dsn not in odbc_sources:
    st.warning(
        f"The configured DSN `{dsn}` is not currently visible to unixODBC. "
        "Check ODBCINI / ~/.odbc.ini and the InterSystems driver path."
    )
    if sys.platform.startswith("linux"):
        st.code(
            "odbcinst -j\n"
            "odbcinst -q -d\n"
            "odbcinst -q -s",
            language="bash",
        )


@st.cache_resource
def get_conn():
    password = os.getenv("IRIS_PASSWORD", "demo")
    conn_str = f"DSN={dsn};UID={user};PWD={password};"
    return pyodbc.connect(conn_str, autocommit=True)


def run_sql(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params or [])
    try:
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return cols, rows
    except pyodbc.ProgrammingError:
        return [], []


try:
    get_conn()
    st.success(f"Connected to IRIS through DSN `{dsn}`.")
except pyodbc.Error as exc:
    st.error(f"IRIS ODBC connection failed for DSN `{dsn}`.")
    st.code(str(exc))
    st.info(
        "If this appears after pyodbc loads successfully, the remaining problem is in the "
        "InterSystems driver / DSN / credentials / host / port / namespace layer."
    )
    st.stop()

st.subheader("IRIS Demo.PatientMsg")
cols, rows = run_sql("SELECT TOP 5 * FROM Demo.PatientMsg")
st.write(f"Rows returned: {len(rows)}")
if rows:
    st.dataframe([{cols[i]: r[i] for i in range(len(cols))} for r in rows])

st.subheader("IRIS Demo.Observation")
cols, rows = run_sql("SELECT TOP 5 * FROM Demo.Observation")
st.write(f"Rows returned: {len(rows)}")
if rows:
    st.dataframe([{cols[i]: r[i] for i in range(len(cols))} for r in rows])
