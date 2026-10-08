"""Regenerate compression/ from database/ with Polars.

Run by the Update-Compression-Files and Update-Categorization-Files jobs of
`.github/workflows/database_update.yml`:

    python scripts/update_compression.py [--only datasets|categories]

Each asset class gets a bz2 CSV and a gzip categories CSV in the layout every earlier
version of the package reads, and a Parquet file of each with the final types for the
versions that read Parquet.
"""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.compression.compression_controller import main  # noqa: E402

if __name__ == "__main__":
    main()
