"""Session lookup and file loading for the goalNav_mFC_ephys dataset.

Barebones API:
    get_maze_sessions  -- filter maze sessions by subject / maze / day / goal subset.
    MazeSession        -- one session's metadata plus lazily-attached data.
    load               -- load a single processed-data file by path.
"""

# %% Imports
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date

from GridMaze.maze import representations as mr

# %% Paths [CHANGE IF YOU DOWNLOADED THE DATA SOMEWHERE ELSE]
EXPERIMENT_INFO_PATH = Path("../data/experiment_info")
PROCESSED_DATA_PATH = Path("../data/processed_data")

# %% Global variables

with open(EXPERIMENT_INFO_PATH / "maze_configs.json", "r") as input_file:
    MAZE_CONFIGS = json.load(input_file)

with open(EXPERIMENT_INFO_PATH / "subject_IDs.json", "r") as input_file:
    SUBJECT_IDS = json.load(input_file)

with open(EXPERIMENT_INFO_PATH / "maze_day2date.json", "r") as input_file:
    MAZE_DAY2DATE = json.load(input_file)

DATA_STRUCTURE2FILENAME = {
    "events_df": "events.htsv",
    "trials_df": "trials.htsv",
    "spike_times": "spikes.times.npy",
    "spike_clusters": "spikes.clusters.npy",
    "cluster_metrics": "clusters.metrics.htsv",
    "tracking_df": "frames.tracking.htsv",
    "trajectories_df": "frames.trajectories.htsv",
    "trial_info_df": "frames.trialInfo.htsv",
    "lfp_times": "lfp.times.npy",
    "lfp_signal": "lfp.signal.npy",
    "lfp_metrics": "lfp.metrics.htsv",
}

# %% Session lookup


def get_maze_sessions(
    subject_IDs="all",
    maze_names="all",
    days_on_maze="all",
    goal_subsets="all",
    with_data="all",
    must_have_data=True,
    verbose=False,
):
    """Return MazeSession objects matching the given filters.

    Parameters
    ----------
    subject_IDs : "all" or list of str (e.g. ["m2", "m7"]).
    maze_names : "all" or list of str (e.g. ["maze_1", "rooms_maze"]).
    days_on_maze : "all", "late" (final 7 days), or list of int.
    goal_subsets : "all" or subset of ["all", "subset_1", "subset_2"].
    with_data : "all" or list of keys from DATA_STRUCTURE2FILENAME.
    must_have_data : if True, drop sessions missing any requested data.
    verbose : print a message for each file that fails to load.

    Returns the single MazeSession if exactly one matches, else a list.
    Raises FileNotFoundError if no sessions match.
    """
    if with_data == "all":
        with_data = list(DATA_STRUCTURE2FILENAME.keys())
    if subject_IDs == "all":
        subject_IDs = SUBJECT_IDS
    if maze_names == "all":
        maze_names = list(MAZE_CONFIGS.keys())
    if goal_subsets == "all":
        goal_subsets = ["all", "subset_1", "subset_2"]
    _check_request_inputs(subject_IDs, maze_names, days_on_maze, goal_subsets)

    sessions = []
    for subject in subject_IDs:
        for maze in maze_names:
            all_days = [int(d) for d in MAZE_DAY2DATE[maze]]
            if days_on_maze == "all":
                days = all_days
            elif days_on_maze == "late":
                days = all_days[-7:]  # last 7 days
            else:
                days = days_on_maze
            for day in days:
                if str(day) not in MAZE_DAY2DATE[maze]:
                    continue
                session_date = MAZE_DAY2DATE[maze][str(day)]
                session_name = f"{session_date}.maze"
                session_info = load(PROCESSED_DATA_PATH / subject / session_name / "session_info.json")
                if session_info["goal_subset"] not in goal_subsets:
                    continue
                sessions.append(MazeSession(subject, session_name, with_data=with_data, verbose=verbose))

    if must_have_data:
        sessions = [s for s in sessions if all(d in s.has_data for d in with_data)]
    if not sessions:
        raise FileNotFoundError("No sessions found with the specified criteria.")
    return sessions[0] if len(sessions) == 1 else sessions


def _check_request_inputs(subject_IDs, maze_names, days_on_maze, goal_subsets):
    """Checks if the inputs for get_maze_sessions are valid. If not raises useful error messages."""
    for arg in [subject_IDs, maze_names, days_on_maze, goal_subsets]:
        if not isinstance(arg, list) and arg not in ["all", "late"]:
            raise ValueError(f"{arg} must be a list")
    for subject in subject_IDs:
        if subject not in SUBJECT_IDS:
            raise ValueError(f"{subject} not in SUBJECT_IDS")
    for maze in maze_names:
        if maze not in MAZE_CONFIGS:
            raise ValueError(f"{maze} not in MAZE_CONFIGS")


# %% Session class


class MazeSession:
    """A single maze session's metadata plus selected processed-data arrays/tables.

    Fields from ``session_info.json`` (subject_ID, maze_name, day_on_maze, goal_subset,
    goals, maze_structure, …) are unpacked as attributes. Each name in ``with_data`` is
    attached as an attribute holding the loaded array/DataFrame, or None if missing;
    ``has_data`` lists which loads succeeded.

    Use ``.simple_maze()`` or ``.skeleton_maze()`` to build a networkx graph of the maze.
    """

    def __init__(self, subject, session_name, with_data, verbose):
        self.has_data = []
        processed_data_path = PROCESSED_DATA_PATH / subject / session_name
        session_info = load(processed_data_path / "session_info.json")
        self.session_info = session_info
        self.name = f"{subject}.{session_name}"
        self.date = date.fromisoformat(session_info["session_date"])
        for k, v in session_info.items():
            setattr(self, k, v)
        total_days = max(int(d) for d in MAZE_DAY2DATE[self.maze_name])
        self.late_session = (total_days - self.day_on_maze) <= 7

        for attr_name in with_data:
            file_path = processed_data_path / DATA_STRUCTURE2FILENAME[attr_name]
            try:
                data = load(file_path)
                self.has_data.append(attr_name)
            except FileNotFoundError:
                if verbose:
                    print(f"{file_path.name} not found for {self.name}")
                data = None
            setattr(self, attr_name, data)

    def __repr__(self):
        """Return a nicely formatted string representation of the MazeSession object."""
        total_width = 50
        return (
            f"\n-MazeSession{'-' * (total_width)}\n"
            f"  Subject ID     : {self.subject_ID:<{total_width - 26}}\n"
            f"  Maze Name      : {self.maze_name:<{total_width - 26}}\n"
            f"  Day on Maze    : {self.day_on_maze:<{total_width - 26}}\n"
            f"  Goal Subset    : {self.goal_subset:<{total_width - 26}}\n"
            f"  Date           : {self.date.isoformat():<{total_width - 26}}\n"
            f"{'-' * (total_width+13)}\n"
        )

    def simple_maze(self):
        """networkx graph: towers as nodes, bridges as edges."""
        return mr.simple_maze(self.maze_structure)

    def skeleton_maze(self):
        """networkx graph: 5 nodes per tower, 3 nodes per bridge (sub-tower spatial resolution)."""
        return mr.skeleton_maze(self.maze_structure)


# %% File loading


def load(filepath):
    """Load a processed-data file. Dispatches on extension:

    - ``.json`` -> dict
    - ``.htsv`` -> pandas DataFrame (MultiIndex columns restored from ``'level0.level1'`` strings)
    - ``.npy``  -> numpy array (``lfp.signal.npy`` cast to float32)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File {filepath} does not exist")
    name = filepath.name
    if name.endswith(".json"):
        with open(filepath, "r") as infile:
            return json.load(infile)
    if name.endswith(".htsv"):
        df = pd.read_csv(filepath, sep="\t")
        if any("." in c for c in df.columns):
            tuples = [tuple(c.split(".")) for c in df.columns]
            n_levels = max(len(t) for t in tuples)
            tuples = [t + ("",) * (n_levels - len(t)) for t in tuples]
            df.columns = pd.MultiIndex.from_tuples(tuples)
        return df
    if name.endswith(".npy"):
        data = np.load(filepath)
        if name == "lfp.signal.npy":
            data = data.astype(np.float32)
        return data
    raise ValueError(f"File {name} not recognised")
