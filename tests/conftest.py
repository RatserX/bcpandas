# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 23:36:07 2019

@author: ydima
"""

import subprocess
import time
import urllib
import sys

import numpy as np
import pandas as pd
import pytest
import pyodbc
import sqlalchemy as sa

from bcpandas import SqlCreds, sqlcmd


IS_WIN = sys.platform == "win32"


if IS_WIN:
    server = "127.0.0.1,1433"
else:
    server = "db"  # the name in docker-compose

_pwd = "MyBigSQLPassword!!!"
_db_name = "db_bcpandas"
_docker_startup = 10  # seconds to wait to give the container time to start


@pytest.fixture(scope="session")
def docker_db():
    if not IS_WIN:
        yield
    else:
        _name = "bcpandas-container"
        cmd_start_container = [
            "docker",
            "run",
            "-d",
            "-e",
            "ACCEPT_EULA=Y",
            "-e",
            f"SA_PASSWORD={_pwd}",
            "-e",
            "MSSQL_PID=Express",
            "-p",
            "1433:1433",
            "--name",
            _name,
            "mcr.microsoft.com/mssql/server:2017-latest",
        ]
        subprocess.run(cmd_start_container)
        time.sleep(_docker_startup)
        print("successfully started DB in docker...")
        yield
        print("Stopping container")
        subprocess.run(["docker", "stop", _name])
        print("Deleting container")
        subprocess.run(["docker", "rm", _name])
        print("all done!")


@pytest.fixture(scope="session")
def database(docker_db):
    creds_master = SqlCreds(server=server, database="master", username="sa", password=_pwd)
    sqlcmd(creds_master, f"CREATE DATABASE {_db_name};")
    yield
    if not IS_WIN:
        sqlcmd(creds_master, f"DROP DATABASE {_db_name};")
    else:
        print("all done")


@pytest.fixture(scope="session")
def sql_creds():
    creds = SqlCreds(server=server, database=_db_name, username="sa", password=_pwd)
    return creds


@pytest.fixture(scope="session")
def pyodbc_creds(database):
    db_url = (
        "Driver={ODBC Driver 17 for SQL Server};"
        + f"Server={server};"
        + f"Database={_db_name};UID=sa;PWD={_pwd};"
    )
    engine = sa.engine.create_engine(
        f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(db_url)}"
    )
    return engine