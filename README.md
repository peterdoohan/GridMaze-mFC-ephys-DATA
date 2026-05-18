<div align="center">

### Data repository for *Doohan et al., 2026* [electrophysiology experiment]

![License](https://img.shields.io/badge/license-BSD--style-green)

<pre>
●     ●─────●     ●     ●─────●─────●
│     │     │     │     │     │      
●─────●     ●     ●─────●     ●     ●
│           │     │           │     │
●─────●─────●─────●     ●─────●─────●
│           │     │     │     │     │
●     ●─────●    🐭     ●     ●     ●
│           │     │           │      
●─────●     ●     ●─────●─────●─────●
│           │           │     │     │
●     ●─────●─────●     ●     ●     ●
│     │                 │     │     │
●─────●─────●─────●─────●     ●     ●
</pre>

</div>

---

**This repo contains:**
- 🧠 **Single-unit + LFP recordings** from mouse medial frontal cortex (mFC) during a goal-directed navigation task
- 🐭 **Behaviour & tracking** — task events (pyControl), video-derived behavioural trajectories
- 🗺️ **Experiment info** – including maze configurations, experiment timelines, etc.
- 📓 **Lightweight loader package and example notebook** for getting started

> 📦 **Where does the actual data live?** This repo describes the dataset and ships loader code — the recordings themselves live on an external archive [(link TBD)](). After cloning, run `bash code/download_data.sh` to pull them into `data/`.

---

> 📜 **Companion paper** lives on [biorxiv]() - check out what we know about the data so far. <br>
> 💻 **Code for paper analyses** lives in the companion [`analysis repo`]() — for analyses in the paper. <br>
> ⚡ **Opto experiment data** lives in the sibling [`goalNav_mFC_opto`]() data repo.

---

## 📊 What's in the dataset

| | |
|---|---|
| **Subjects** | 6 (m2, m3, m4, m6, m7, m8) |
| **Sessions per subject** | 35 maze sessions across 3 mazes — `maze_1` (13 days), `maze_2` (11 days), `rooms_maze` (11 days) — naive to expert on each |
| **Probes** | 6-shank 64-channel Cambridge NeuroTech probes in mFC (prelimbic, anterior cingulate) |
| **Behavioural task** | Goal-directed navigation on an elevated 7×7 grid maze |
| **Per session** | spike times + clusters, LFP signal + times, QC'd trajectories, raw bodypart tracking, task trial events |

---

## 📁 Repository layout

```
goalNav_mFC_ephys/
├── 💻 code/                     <- loader package + tutorial notebooks
│   ├── GridMaze/                <- minimal loader + maze graph code
│   │   ├── core/get_sessions.py        <- session lookup + MazeSession + load()
│   │   └── maze/representations.py     <- networkx maze builders
│   ├── processed_data_intro.ipynb      <- tour the per-session files
│   ├── maze_intro.ipynb                <- work with the maze graphs
│   ├── example_analysis.ipynb          <- worked end-to-end analysis
│   └── download_data.sh
├── 📦 data/                     <- placeholder for data to be downloaded from repository
│   ├── processed_data/          <- subject/session/ in a standardised format (human readable)
│   └── experiment_info/         <- subject IDs, maze configs, probe depths, etc. (fixed across the experiment)
└── 📈 results/                  <- placeholder for your figures + outputs
```

---

## 📦 Processed data

One folder per subject. Each subject folder has a `probe.htsv` (per-channel anatomy from the Allen CCF) plus one folder per session, named `YYYY-MM-DD.maze`. Files follow IBL-like naming conventions `object.attribute.filetype`, where files sharing the same `object` share their first dimension (where possible).

```
processed_data/m2/
├── probe.htsv                   <- per-channel Allen region + probe contact geometry (shared across sessions)
└── 2022-06-23.maze/
    ├── session_info.json            <- subject, date, maze name + structure, day on maze, goals, probe depth, …
    ├── trials.htsv                  <- per-trial: goal, error pokes, event times
    ├── events.htsv                  <- all pyControl events (cues, rewards, port pokes)
    ├── spikes.times.npy             <- spike times (s)                      }  same first dim
    ├── spikes.clusters.npy          <- cluster IDs                          }
    ├── clusters.metrics.htsv        <- per-cluster QC + Allen region + probe contact
    ├── lfp.signal.npy               <- (n_channels, n_samples) LFP in µV    }  same first dim
    ├── lfp.times.npy                <- LFP timestamps                       }
    ├── lfp.metrics.htsv             <- per-channel QC + region + sampling rate
    ├── frames.tracking.htsv         <- raw SLEAP/DLC bodypart positions     }  shared row index
    ├── frames.trajectories.htsv     <- QC'd centroid + head_direction       }
    ├── frames.trialInfo.htsv        <- per-frame trial / trial_phase / goal }
    └── UnitMatch/                   <- inputs needed for running UnitMatch (matching cells across recordings)
```

**Conventions**
- ⏱️ All times in **seconds from start of behavioural session** (cross-stream alignment is done at preprocessing time).
- 📏 All other quantities in **SI units** where applicable.
- 🧾 Tables are `.htsv` (tab-separated, header row, human-readable). Arrays are `.npy`. Metadata is `.json`.

Full per-field tour: [`code/processed_data_intro.ipynb`](code/processed_data_intro.ipynb). End-to-end worked example: [`code/example_analysis.ipynb`](code/example_analysis.ipynb).

---

## 🗺️ Maze representations

Each maze is stored as a human-readable edge list (e.g. `"A1-A2"`) in `experiment_info/maze_configs.json`. From that edge list, `GridMaze.maze.representations` builds three `networkx` views:

- **`simple_maze`** — towers as nodes, bridges as edges. Primary form.
- **`extended_simple_maze`** — towers AND bridges as nodes.
- **`skeleton_maze`** — 5 nodes/tower, 3 nodes/bridge for sub-tower spatial resolution.

A `MazeSession` exposes the first and third directly via `.simple_maze()` and `.skeleton_maze()`. See [`code/maze_intro.ipynb`](code/maze_intro.ipynb) for the full tour.

---

## 🐍 Environment

The notebooks and loader package depend on a small set of standard scientific-Python libraries (`numpy`, `pandas`, `networkx`, `matplotlib`, `scipy`, `scikit-learn`) plus `jupyterlab` / `ipykernel` to run the tutorials. The pinned set lives in [`code/environment.yml`](code/environment.yml).

```bash
conda env create -f code/environment.yml   
conda activate GridMaze_mFC_ephys
```

---

## 🚀 Quick start

```bash
conda activate GridMaze_mFC_ephys
git clone <repo-url> goalNav_mFC_ephys
cd goalNav_mFC_ephys
bash code/download_data.sh                  # populates data/processed_data/
conda env create -f code/environment.yml    # creates the GridMaze_mFC_data env
conda activate GridMaze_mFC_data
jupyter lab code/
```

Loader code lives in `code/GridMaze/` and assumes you launch from `code/` (paths are relative to that directory). Then dive into the tutorials below 👇


---

## 📓 Tutorials

Three short notebooks live in [`code/`](code/) to get you up and running:

- [`processed_data_intro.ipynb`](code/processed_data_intro.ipynb) — load a session with `get_maze_sessions(...)` and tour each per-session file: `trials_df`, `events_df`, spikes, cluster metrics, raw tracking, QC'd trajectories, per-frame trial info, LFP, and `session_info`.
- [`maze_intro.ipynb`](code/maze_intro.ipynb) — build and inspect the three `networkx` maze views (`simple_maze`, `extended_simple_maze`, `skeleton_maze`) from `maze_configs.json`.
- [`example_analysis.ipynb`](code/example_analysis.ipynb) — worked example: frame-aligned firing rates, per-location summaries, single-cell visualisation, aggregation across sessions, and a low-dimensional spatial basis.

---

## 📜 Citation

```bibtex
@article{placeholder,
  title  = {Structured and flexible representations in medial-frontal cortex
            support goal-directed navigation},
  author = {Doohan, Peter T. and colleagues},
  year   = {2026}
}
```
