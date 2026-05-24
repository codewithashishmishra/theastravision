import os
import subprocess
import sys
import platform

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

def run_in_new_terminal(command, cwd, name):
    print(f"Starting {name}...")
    if sys.platform == "win32":
        # Opens a new cmd window on Windows
        subprocess.Popen(f'start "{name}" cmd /k "{command}"', cwd=cwd, shell=True)
    elif sys.platform == "darwin":
        # Opens a new Terminal window on MacOS
        escaped_cmd = command.replace('"', '\\"')
        apple_script = f'tell application "Terminal" to do script "cd {cwd} && {escaped_cmd}"'
        subprocess.Popen(['osascript', '-e', apple_script])
    else:
        # Opens a new terminal on Linux (attempts gnome-terminal, falls back to xterm)
        try:
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd {cwd} && {command}; exec bash'])
        except FileNotFoundError:
            subprocess.Popen(['xterm', '-e', f'cd {cwd} && {command}; bash'])

def main():
    print("="*50)
    print("   AastraaHR Development Bootstrapper   ")
    print("="*50)

    root_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(root_dir, "apps", "api")
    ai_dir = os.path.join(root_dir, "apps", "ai-service")
    web_dir = os.path.join(root_dir, "apps", "admin-web")
    
    api_python = get_venv_python(api_dir)
    api_celery = get_venv_celery(api_dir)
    ai_uvicorn = get_venv_uvicorn(ai_dir)
    
    # 1. Migrate Database
    print("\n[1/2] Running database migrations...")
    migrate_cmd = f'"{api_python}" manage.py migrate'
    result = subprocess.run(migrate_cmd, cwd=api_dir, shell=True)
    if result.returncode != 0:
        print("Warning: Database migrations returned a non-zero exit code.")
        print("If this is a fresh setup, please make sure PostgreSQL is running.")
    
    # 2. Start Services
    print("\n[2/2] Launching Background Services in separate windows...")
    run_in_new_terminal(f'"{api_python}" manage.py runserver 8000', cwd=api_dir, name="Django_API")
    run_in_new_terminal(f'"{api_celery}" -A config worker -l info --pool=solo', cwd=api_dir, name="Celery_Worker")
    run_in_new_terminal(f'"{api_celery}" -A config beat -l info', cwd=api_dir, name="Celery_Beat")
    run_in_new_terminal(f'"{ai_uvicorn}" main:app --reload --port 8001', cwd=ai_dir, name="AI_Service")
    run_in_new_terminal('npm run dev', cwd=web_dir, name="Frontend_AdminWeb")
    
    print("\n✅ All services have been successfully launched!")
    print("You can view the logs for each service in their respective terminal windows.")

if __name__ == "__main__":
    main()
