import os
import sys
import urllib.request
import zipfile
import subprocess
import time

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
PG_DIR = os.path.join(SCRATCH_DIR, "pgsql")
ZIP_PATH = os.path.join(SCRATCH_DIR, "postgresql.zip")
DATA_DIR = os.path.join(PG_DIR, "data")
PORT = 5432
URL = "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64-binaries.zip"

def get_bin_dir():
    # Check if nested in pgsql/pgsql/bin or pgsql/bin
    nested = os.path.join(PG_DIR, "pgsql", "bin")
    direct = os.path.join(PG_DIR, "bin")
    if os.path.exists(nested):
        return nested
    if os.path.exists(direct):
        return direct
    return nested

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    start_time = time.time()
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Downloaded in {time.time() - start_time:.2f} seconds.")
        return True
    except Exception as e:
        print(f"Failed to download from {url}: {e}")
        return False

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path} to {extract_to}...")
    start_time = time.time()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted in {time.time() - start_time:.2f} seconds.")
        return True
    except Exception as e:
        print(f"Failed to extract: {e}")
        return False

def init_db():
    bin_dir = get_bin_dir()
    initdb_path = os.path.join(bin_dir, "initdb.exe")
    if not os.path.exists(initdb_path):
        print(f"Error: initdb.exe not found at {initdb_path}")
        return False
    if not os.path.exists(DATA_DIR):
        print("Initializing database cluster...")
        cmd = [initdb_path, "-D", DATA_DIR, "-U", "postgres", "-A", "trust"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("initdb failed:", res.stderr)
            return False
        print("Database initialized successfully.")
    else:
        print("Database directory already exists.")
    return True

def start_server():
    bin_dir = get_bin_dir()
    pg_ctl_path = os.path.join(bin_dir, "pg_ctl.exe")
    log_file = os.path.join(PG_DIR, "postgres.log")
    pid_file = os.path.join(DATA_DIR, "postmaster.pid")

    if not os.path.exists(DATA_DIR):
        if not init_db():
            return False

    # Check status first
    status_cmd = [pg_ctl_path, "status", "-D", DATA_DIR]
    res = subprocess.run(status_cmd, capture_output=True, text=True)
    if "is running" in res.stdout or "server is running" in res.stdout:
        print("PostgreSQL is already running.")
        return True

    # If stale pid exists and not running, clean it
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except Exception:
            pass

    print("Starting PostgreSQL server on port 5432...")
    cmd = [pg_ctl_path, "start", "-D", DATA_DIR, "-o", f"-p {PORT}", "-l", log_file]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Failed to start PostgreSQL server:", res.stderr)
        return False
    print("PostgreSQL server started successfully.")
    return True

def stop_server():
    bin_dir = get_bin_dir()
    pg_ctl_path = os.path.join(bin_dir, "pg_ctl.exe")
    print("Stopping PostgreSQL server...")
    cmd = [pg_ctl_path, "stop", "-D", DATA_DIR, "-m", "fast"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout or res.stderr)
    return res.returncode == 0

def status_server():
    bin_dir = get_bin_dir()
    pg_ctl_path = os.path.join(bin_dir, "pg_ctl.exe")
    cmd = [pg_ctl_path, "status", "-D", DATA_DIR]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout if res.stdout else res.stderr)
    return res.returncode == 0

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    if action == "stop":
        stop_server()
    elif action == "status":
        status_server()
    elif action == "init":
        init_db()
    else:
        if not os.path.exists(PG_DIR):
            if not os.path.exists(ZIP_PATH):
                if not download_file(URL, ZIP_PATH):
                    sys.exit(1)
            if not extract_zip(ZIP_PATH, PG_DIR):
                sys.exit(1)
            try:
                os.remove(ZIP_PATH)
            except Exception:
                pass
        start_server()
