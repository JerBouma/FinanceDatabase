"""Helper functions for loading and parsing data."""

import os

import pandas as pd


def load_dataset(file_location: str) -> pd.DataFrame:
    """Load a CSV dataset from the specified file location.

    Args:
        file_location: Path to the CSV file

    Returns:
        Loaded dataset as a pandas DataFrame

    Raises:
        FileNotFoundError: If the specified file does not exist
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"The file {file_location} does not exist")

    return pd.read_csv(file_location)


def load_existing(file_location: str) -> dict:
    """Load existing values from a pickle file.

    Args:
        file_location: Path to the pickle file containing values

    Returns:
        Dictionary of existing values, or empty dict if file not found
    """
    try:
        existing = pd.read_pickle(file_location)

        # Convert to dictionary for faster lookup
        existing_dict = existing[0].to_dict()
        print(f"Loaded {len(existing_dict)} existing values")
        return existing_dict
    except (FileNotFoundError, KeyError):
        print("No existing values found, starting fresh")
        return {}
