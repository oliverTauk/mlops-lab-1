# Lab 1 – git/dvc and data preparation

## Remote solution adopted

**Solution 1 – local DVC remote.** Instead of DagsHub, the DVC remote is a folder on my laptop, `dvc-storage`, placed next to the repository (outside it):

```
Machile Learning Operation -\
├── mlops-lab-1\     ← git + dvc repository
└── dvc-storage\     ← DVC local remote (the data itself)
```

```bash
mkdir "..\dvc-storage"
dvc remote add -d localremote "..\dvc-storage"
git add .dvc/config
git commit -m "Configure local dvc remote"
git push
```

`-d` makes it the default remote, so `dvc push` / `dvc pull` use it without naming it. The folder must stay outside the repo, otherwise git (or DVC itself) would try to track the stored data. Because the path is relative, any clone placed in the same parent folder finds the storage too.

---

## Question 1 – Files created by `uv init`

- `pyproject.toml` – project metadata (name, version, required Python) and the list of dependencies. `uv add pillow` writes into it.
- `.python-version` – the Python version uv uses for this project.
- `src/mlops_lab_1/` – a package folder named after the project, with an `__init__.py` example entry point (newer uv versions create this src layout; older ones create a `main.py` instead).
- `README.md` – empty project description.
- `.gitignore` – may be added (ignores `.venv`, `__pycache__`, etc.).

After the first `uv add` / `uv run`, two more appear: `uv.lock` (exact pinned versions of every dependency, for reproducible installs; it should be committed) and `.venv/` (the virtual environment; never committed).

## Question 2 – Files created by `dvc init`

- `.dvc/config` – DVC project configuration (remotes, default remote, options). **Pushed to git.**
- `.dvc/.gitignore` – tells git to ignore DVC's internal folders (`cache`, `tmp`). **Pushed to git.**
- `.dvc/tmp/` – temporary files, locks, state database. **Not pushed.**
- `.dvc/cache/` (created on first `dvc add`) – the local content-addressed copy of the data. **Not pushed to git** (it goes to the DVC remote with `dvc push`).
- `.dvcignore` – like `.gitignore`, patterns DVC should skip when hashing/tracking. **Pushed to git.**

## Question 3 – Where are the credentials stored?

With `--global`, the settings are written to the user-level DVC config, outside the repo (Linux: `~/.config/dvc/config`, macOS: `~/Library/Application Support/dvc/config`, Windows: `%LOCALAPPDATA%\iterative\dvc\config`).

Config levels:

| Option | File | Committed to git? |
|---|---|---|
| *(none)* / `--project` | `.dvc/config` | Yes |
| `--local` | `.dvc/config.local` | No (git-ignored) |
| `--global` | user config | No (outside repo) |
| `--system` | machine-wide config | No (outside repo) |

Credentials must **never** be pushed to GitHub; they belong in `--local` or `--global`. With my local-folder remote no credentials are needed at all – only the path is stored in `.dvc/config`.

## Question 4 – `.gitignore` after `dvc add data`

DVC appended `/data` to the root `.gitignore`. The actual files are now managed by DVC (copied into `.dvc/cache` and linked into the workspace), so git must ignore them to avoid committing gigabytes of images. Git only versions the small pointer file instead.

## Question 5 – The `.dvc` file

Yes, `data.dvc` was created. It is a small YAML pointer, e.g.:

```yaml
outs:
- md5: 39f0acac94304ed234c9a682eed511e3.dir
  size: 1383529306
  nfiles: 36578
  hash: md5
  path: data

```

`md5` is the hash of the whole directory (the `.dir` suffix means it points to a manifest listing every file's hash), plus total size, file count and the tracked path. Committing this file to git is how a code commit is tied to an exact version of the data.

## Question 6 – What is on GitHub and on the remote?

- GitHub: the code (`pyproject.toml`, `src/…`), `.dvc/config`, `.dvcignore`, `.gitignore` and `data.dvc` are there. **The images are not.**
- `data.dvc` is the file that points to the data (by hash); `.dvc/config` says which remote to fetch it from.
- Since I use a local remote, there is no DagsHub UI. The data is in the `dvc-storage` folder next to my repo, stored by hash (`files/md5/xx/yyyy…`), not by original file name – the same layout DagsHub would hold.

## Question 7 – Fresh clone

```bash
cd ..
git clone https://github.com/oliverTauk/mlops-lab-1.git mlops-lab-1-test
cd mlops-lab-1-test
```

(The test clone is placed next to the real repo so the relative storage path `..\dvc-storage` still resolves.)

There is no `data/` folder, only `data.dvc`. To get it:

```bash
dvc pull      # = dvc fetch (remote -> cache) + dvc checkout (cache -> workspace)
```

This works because the local remote path in `.dvc/config` exists on the same machine. On another machine it would fail – the limitation of a local remote compared with DagsHub.

## Data preparation

`src/food11/data.py` builds `food11_processed` (128×128 images arranged as `split/Category/image.jpg`, the `torchvision.datasets.ImageFolder` layout used to train ResNet) and `food11_processed_mini` (at most 100 images per category per split). Run with:

```bash
uv add pillow
uv run python ./src/food11/data.py
dvc add data
git add data.dvc src pyproject.toml uv.lock
git commit -m "Add food11_processed and food11_processed_mini"
git push
dvc push
```

## Question 8 – Checking out the older commit

```bash
git log --oneline -- data.dvc
# ee9eacf Add food11_processed and food11_processed_mini
# 9a30310 Track data folder with dvc
git checkout 9a30310
dvc checkout
```

No – `food11_processed` and `food11_processed_mini` disappear; only `food11_raw` remains, because the old `data.dvc` points to the earlier version of the folder. They are not lost: they stay in `.dvc/cache` and on the remote. After `git checkout main` and `dvc checkout` they come back immediately, without re-running the script.
