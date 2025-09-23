
## `Pyenv` Setup Guide

---

### 🍎 macOS (via Homebrew)

#### 1. Install `pyenv` using Homebrew:

```bash
brew update
brew install pyenv
```

#### 2. Add the following lines to the end of your `~/.zshrc` (or `~/.bashrc`, depending on your shell):

```zsh
# Pyenv Setup
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

#### 3. Apply the changes:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

---

### 🐧 Linux (Ubuntu/Debian-based)

#### 1. Install required dependencies:

```bash
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev curl \
  llvm libncursesw5-dev xz-utils tk-dev libxml2-dev \
  libxmlsec1-dev libffi-dev liblzma-dev
```

#### 2. Install `pyenv` via the installer script:

```bash
curl https://pyenv.run | bash
```

#### 3. Add the following lines to the end of your `~/.bashrc`, `~/.zshrc`, or appropriate shell config file:

```bash
# Pyenv Setup
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

#### 4. Apply the changes:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

### 🪟 Windows (via `pyenv-win`)

On Windows, you’ll use [`pyenv-win`](https://github.com/pyenv-win/pyenv-win), a compatible version of `pyenv`.

#### 1. Install via PowerShell (Recommended)

```powershell
Invoke-WebRequest -UseBasicParsing -Uri https://pyenv.run | Invoke-Expression
```

> This installs `pyenv`, `pyenv-doctor`, and other helpers into `%USERPROFILE%\.pyenv`.

#### 2. Add the following to your user environment variables:

- Add to `PATH`:
    
    - `%USERPROFILE%\.pyenv\pyenv-win\bin`
        
    - `%USERPROFILE%\.pyenv\pyenv-win\shims`
        

#### 3. Restart PowerShell or Command Prompt.

#### 4. Verify installation:

```powershell
pyenv --version
```

---

### 📋 **`pyenv` Command Reference Table**

|Command|Description|Example|
|---|---|---|
|`pyenv install --list`|Lists all available Python versions that can be installed|`pyenv install --list`|
|`pyenv install <version>`|Installs a specific Python version|`pyenv install 3.11.6`|
|`pyenv uninstall <version>`|Uninstalls a specific Python version|`pyenv uninstall 3.11.6`|
|`pyenv versions`|Lists all installed Python versions|`pyenv versions`|
|`pyenv global <version>`|Sets the global (default) Python version|`pyenv global 3.11.6`|
|`pyenv local <version>`|Sets the local Python version for the current directory (writes `.python-version`)|`pyenv local 3.10.8`|
|`pyenv shell <version>`|Sets a temporary Python version for the current shell session only|`pyenv shell 3.9.13`|
|`pyenv which <command>`|Shows the full path to the executable that would be run (e.g. `python`, `pip`)|`pyenv which python`|
|`pyenv exec <command>`|Runs a command using the selected Python version|`pyenv exec python --version`|
|`pyenv doctor`|Checks for common issues in your `pyenv` installation (requires plugin)|`pyenv doctor`|
|`pyenv rehash`|Rebuilds the shim binaries (usually automatic)|`pyenv rehash`|
|`pyenv update`|Updates `pyenv` to the latest version (if installed via Git)|`pyenv update`|

---

#### 📌 Notes:

- `pyenv local` overrides `pyenv global` **within that directory**.
    
- Use `.python-version` to lock a Python version per project.
    
- `pyenv shell` is temporary and only lasts for the current terminal session.
    

---
### Explanation

- The root directory of `pyenv` is set to `$HOME/.pyenv`. This also creates the `.pyenv` folder.    
- To make `pyenv` usable in the shell, we add the `$PYENV_ROOT/bin` directory to the `$PATH` variable:
    
    ```bash
    export PATH="$PYENV_ROOT/bin:$PATH"
    ```
    
- `eval "$(pyenv init --path)"`    
    - Initializes `pyenv`'s **shims** during the shell's startup process (e.g., `.profile` or `.zprofile`).        
    - **Shim**:        
        - A lightweight proxy or wrapper around a real program.            
        - `pyenv` creates shim files (e.g., in `~/.pyenv/shims/`) for Python-related commands like `python`, `pip`, etc.            
        - Shims do **not** contain a Python interpreter themselves — they **redirect** commands to the appropriate Python version selected by `pyenv`.            
        - Allows seamless switching between Python versions per project:            
            - You don’t need to manually modify `$PATH` for each version.                
    - Adjusts `$PATH` so that the correct Python version is found and executed according to the `.python-version` file.        
    - Without this, commands like `python` or `pip` might resolve to the system Python instead of the one selected via `pyenv`.        
- `eval "$(pyenv init -)"`    
    - Initializes shell integration.        
    - Enables `pyenv` to **automatically switch Python versions** when you `cd` into directories that contain a `.python-version` file.        
- Additionally, we add the directory used by **Poetry** to the shell's `$PATH`, so the shell can recognize and run Poetry:
    
    ```bash
    export PATH="$HOME/.local/bin:$PATH"
    ```


---


## Poetry Setup Guide

---

### 🍎 macOS & 🐧 Linux

#### 1. Install Poetry using the official installer:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### 2. Add Poetry to your `PATH` (if it's not already):

Add this line to your shell config file (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then apply the change:

```bash
source ~/.zshrc  # or ~/.bashrc
```

---

### 🪟 Windows

#### 1. Run the official installer:

Open PowerShell and run:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### 2. Ensure Poetry is in your system `PATH`:

- By default, it installs to `%USERPROFILE%\AppData\Roaming\Python\Scripts`.
- Make sure that directory is in your **User Environment Variables → PATH**.    

---

### 🧪 Verify installation

```bash
poetry --version
```

You should see the installed version printed. Let me know if you want Poetry integrated with `pyenv` as well.

## How to Use Poetry + Pyenv

---

### 🍎 macOS & 🐧 Linux

#### 1. Install the Python versions you need

Use `pyenv` to install the required Python versions:

```bash
pyenv install 3.9.19
pyenv install 3.11.9
pyenv install 3.12.2
```

Check for installed versions

```shell
pyenv versions
```


#### 2. Set up the local project environment

> Run the following commands **in the same directory as your `pyproject.toml`**.

```bash
pyenv local 3.12.2                # Creates a .python-version file and activates 3.12.2 locally
poetry env use 3.12.2               # Tells Poetry to use the local Python version/venv
poetry install                    # Installs project dependencies from pyproject.toml
```

> 💡 If you want to switch to an existing virtual environment later, simply run:

```bash
poetry env use <version>
```

#### 3. Install dependencies

By default, `poetry install` installs only the main dependencies:

- `[tool.poetry.dependencies]`    
- `[tool.poetry.dev-dependencies]`    

To install optional groups like `lint`, `doc`, `test`, `rag`, etc., use the `--with` flag:

```bash
poetry install --with lint
# or multiple groups
poetry install --with lint,test,doc
```

---

### 🪟 Windows

> On Windows, use **`pyenv-win`** instead of the standard Unix `pyenv`.

#### 1. Install Python versions

In PowerShell or Command Prompt:

```powershell
pyenv install 3.9.19
pyenv install 3.11.9
pyenv install 3.12.2
```

#### 2. Set up local Python version and Poetry environment

> Navigate to the folder containing your `pyproject.toml`.

```powershell
pyenv local 3.12.2
poetry env use 3.12
poetry install
```

> To switch environments later:

```powershell
poetry env use <version>
```

#### 3. Install dependencies (including optional groups)

```powershell
poetry install --with lint,test
```

---

### 📄 Summary

|Task|Command|
|---|---|
|Install Python version|`pyenv install <version>`|
|Set local Python version|`pyenv local <version>`|
|Set Poetry to use Python version|`poetry env use <version>`|
|Install dependencies|`poetry install`|
|Install with optional groups|`poetry install --with lint,test,...`|

