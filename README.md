# open
Open Architecture, Open Data, and Open Practices for Nuclear Development and Deployment

## Running the GUI (`interfaced_functionsfile_updated (3).py`)

Each computer should use its **own** `.venv` (already in `.gitignore`). If the folder was synced from another machine (OneDrive, zip, etc.) and startup fails, delete `.venv` and run the script again — it will recreate the environment automatically.

Manual setup (optional):

```powershell
cd path\to\open
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe "interfaced_functionsfile_updated (3).py"
```
