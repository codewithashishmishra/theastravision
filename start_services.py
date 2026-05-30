"""
Bootstrap local dev: migrate, seed_env_config, then start API / Celery / AI / frontend.

Windows: opens one Windows Terminal window with a tab per service (if wt.exe is installed).
Set START_SERVICES_SEPARATE_WINDOWS=true to use separate CMD windows instead.
"""
import os
import shutil
import subprocess
import sys


def get_venv_python(base_dir):
    if sys.platform == "win32":
        return os.path.join(base_dir, "venv", "Scripts", "python.exe")
    return os.path.join(base_dir, "venv", "bin", "python")


def get_venv_celery(base_dir):
    if sys.platform == "win32":
        return os.path.join(base_dir, "venv", "Scripts", "celery.exe")
    return os.path.join(base_dir, "venv", "bin", "celery")


def get_venv_uvicorn(base_dir):
    if sys.platform == "win32":
        return os.path.join(base_dir, "venv", "Scripts", "uvicorn.exe")
    return os.path.join(base_dir, "venv", "bin", "uvicorn")


def _find_windows_terminal():
    wt = shutil.which("wt")
    if wt:
        return wt
    local = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "Microsoft",
        "Windows Apps",
        "wt.exe",
    )
    if os.path.isfile(local):
        return local
    return None


def run_in_new_terminal(command, cwd, name):
    print(f"Starting {name}...")
    if sys.platform == "win32":
        subprocess.Popen(f'start "{name}" cmd /k "{command}"', cwd=cwd, shell=True)
    elif sys.platform == "darwin":
        escaped_cmd = command.replace('"', '\\"')
        apple_script = f'tell application "Terminal" to do script "cd {cwd} && {escaped_cmd}"'
        subprocess.Popen(["osascript", "-e", apple_script])
    else:
        try:
            subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", f"cd {cwd} && {command}; exec bash"]
            )
        except FileNotFoundError:
            subprocess.Popen(["xterm", "-e", f"cd {cwd} && {command}; bash"])


def run_services_windows_terminal(tabs):
    """
    Open one Windows Terminal window with a tab per service.
    tabs: list of (title, cwd, command) where command is already quoted for cmd.
    """
    wt = _find_windows_terminal()
    if not wt:
        return False

    segments = []
    for i, (title, cwd, command) in enumerate(tabs):
        cwd_abs = os.path.abspath(cwd)
        # Keep tab open on exit; show service name in console title bar.
        inner = f'cmd /k "title {title} & {command}"'
        if i == 0:
            segments.append(f'-d "{cwd_abs}" --title "{title}" {inner}')
        else:
            segments.append(f'new-tab -d "{cwd_abs}" --title "{title}" {inner}')

    # wt path has no spaces; avoid extra quotes (breaks cmd /c on some setups).
    wt_line = f"{wt} " + " ; ".join(segments)
    try:
        # shell=True so one string is parsed correctly whether parent is cmd or PowerShell.
        proc = subprocess.Popen(wt_line, shell=True)
        return proc.poll() is None or proc.returncode == 0
    except OSError:
        return False


def launch_dev_services(api_dir, ai_dir, web_dir, api_python, api_celery, ai_uvicorn):
    tabs = [
        ("Django_API", api_dir, f'"{api_python}" manage.py runserver 8000'),
        ("Celery_Worker", api_dir, f'"{api_celery}" -A config worker -l info --pool=solo'),
        ("Celery_Beat", api_dir, f'"{api_celery}" -A config beat -l info'),
        ("AI_Service", ai_dir, f'"{ai_uvicorn}" main:app --reload --port 8001'),
        ("Frontend_AdminWeb", web_dir, "npm run dev"),
    ]

    force_separate = os.environ.get("START_SERVICES_SEPARATE_WINDOWS", "").lower() in (
        "true",
        "1",
        "yes",
    )
    if sys.platform == "win32" and not force_separate:
        if run_services_windows_terminal(tabs):
            print("Opened Windows Terminal with one tab per service.")
            print("Close the terminal window to stop all services (or Ctrl+C in each tab).")
            return

    print("Launching services in separate terminal windows...")
    if sys.platform == "win32" and not _find_windows_terminal():
        print(
            "(Install Windows Terminal from the Microsoft Store for a single tabbed window next time.)"
        )
    for title, cwd, command in tabs:
        run_in_new_terminal(command, cwd, title)
    if sys.platform == "win32":
        print("You can view logs in each CMD window.")


def main():
    print("=" * 50)
    print("   AastraaHR Development Bootstrapper   ")
    print("=" * 50)

    root_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(root_dir, "apps", "api")
    ai_dir = os.path.join(root_dir, "apps", "ai-service")
    web_dir = os.path.join(root_dir, "apps", "admin-web")

    api_python = get_venv_python(api_dir)
    api_celery = get_venv_celery(api_dir)
    ai_uvicorn = get_venv_uvicorn(ai_dir)

    print("\n[1/3] Running database migrations...")
    migrate_cmd = f'"{api_python}" manage.py migrate'
    result = subprocess.run(migrate_cmd, cwd=api_dir, shell=True)
    if result.returncode != 0:
        print("Warning: Database migrations returned a non-zero exit code.")
        print("If this is a fresh setup, please make sure PostgreSQL is running.")

    print("\n[2/3] Seeding platform env config (SMTP/IMAP from apps/api/.env)...")
    seed_cmd = f'"{api_python}" manage.py seed_env_config'
    seed_result = subprocess.run(seed_cmd, cwd=api_dir, shell=True)
    if seed_result.returncode != 0:
        print("Warning: seed_env_config returned a non-zero exit code.")
        print("Check PLATFORM_SMTP_PASSWORD in apps/api/.env and re-run.")

    print("\n[3/3] Launching dev services...")
    launch_dev_services(api_dir, ai_dir, web_dir, api_python, api_celery, ai_uvicorn)

    print("\nAll services have been launched!")


if __name__ == "__main__":
    main()
