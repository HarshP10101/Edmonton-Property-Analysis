"""
Download Edmonton Property Assessment Data via the Socrata Open Data API.

Pulls historical property assessment records from the City of Edmonton
Open Data Portal for specified assessment years. Each year is saved as
a separate CSV file in the output directory.

Dataset: Property Assessment Data (Historical)
Endpoint: https://data.edmonton.ca/resource/qi6a-xuwt
Documentation: https://dev.socrata.com/foundry/data.edmonton.ca/qi6a-xuwt

Usage:
    python download_data.py
    python download_data.py --years 2022 2023 2024
    python download_data.py --output data/raw
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://data.edmonton.ca/resource/qi6a-xuwt.csv"
DEFAULT_YEARS = [2022, 2023, 2024]
DEFAULT_OUTPUT_DIR = "data"
REQUEST_LIMIT = 500_000  # Socrata max rows per request
REQUEST_TIMEOUT = 120  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds between retries

# Columns to keep (drop computed region columns that add no value)
COLUMNS_TO_KEEP = [
    "account_number",
    "assessment_year",
    "suite",
    "house_number",
    "street_name",
    "neighbourhood_name",
    "latitude",
    "longitude",
    "year_built",
    "garage",
    "zoning",
    "lot_size",
    "assessed_value",
    "mill_class_1",
    "tax_class_pct_1",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for year selection and output path."""
    parser = argparse.ArgumentParser(
        description="Download Edmonton property assessment data."
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=DEFAULT_YEARS,
        help="Assessment years to download (default: 2022 2023 2024)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for CSV files (default: data/)",
    )
    return parser.parse_args()


def fetch_year_data(year: int, attempt: int = 1) -> Optional[pd.DataFrame]:
    """
    Fetch property assessment data for a single year from the Socrata API.

    Parameters
    ----------
    year : int
        The assessment year to query (e.g. 2024).
    attempt : int
        Current retry attempt number (used internally for recursion).

    Returns
    -------
    pd.DataFrame or None
        A dataframe of property records, or None if all retries fail.
    """
    params = {
        "$where": f"assessment_year={year}",
        "$limit": REQUEST_LIMIT,
        "$order": "account_number ASC",
    }

    logger.info("Requesting %d data (attempt %d/%d)...", year, attempt, RETRY_ATTEMPTS)

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.warning("Request timed out for year %d.", year)
        return _retry_or_fail(year, attempt)

    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP error for year %d: %s", year, exc)
        return _retry_or_fail(year, attempt)

    except requests.exceptions.ConnectionError as exc:
        logger.warning("Connection error for year %d: %s", year, exc)
        return _retry_or_fail(year, attempt)

    # Parse response text into a dataframe
    from io import StringIO

    df = pd.read_csv(StringIO(response.text))

    if df.empty:
        logger.warning("No records returned for year %d.", year)
        return None

    logger.info("Received %s records for %d.", f"{len(df):,}", year)
    return df


def _retry_or_fail(year: int, attempt: int) -> Optional[pd.DataFrame]:
    """Retry the request or return None after max attempts."""
    if attempt < RETRY_ATTEMPTS:
        logger.info("Retrying in %d seconds...", RETRY_DELAY)
        time.sleep(RETRY_DELAY)
        return fetch_year_data(year, attempt + 1)

    logger.error("Failed to download %d after %d attempts.", year, RETRY_ATTEMPTS)
    return None


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only the columns needed for analysis and drop the rest.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe from the Socrata API response.

    Returns
    -------
    pd.DataFrame
        Dataframe with only the relevant columns retained.
    """
    available = [col for col in COLUMNS_TO_KEEP if col in df.columns]
    dropped = set(df.columns) - set(available)

    if dropped:
        logger.info("Dropping %d unused columns: %s", len(dropped), sorted(dropped))

    return df[available].copy()


def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save a dataframe to CSV without the pandas index column."""
    df.to_csv(filepath, index=False)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    logger.info("Saved %s (%s rows, %.1f MB)", filepath, f"{len(df):,}", size_mb)


def validate_data(df: pd.DataFrame, year: int) -> None:
    """
    Run basic validation checks and log warnings for data quality issues.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataframe for a single assessment year.
    year : int
        The assessment year (used for log messages).
    """
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]

    if not cols_with_nulls.empty:
        logger.info("Null counts for %d:", year)
        for col, count in cols_with_nulls.items():
            pct = count / len(df) * 100
            logger.info("  %-25s %6d nulls (%.1f%%)", col, count, pct)

    if "assessed_value" in df.columns:
        zero_values = (df["assessed_value"] == 0).sum()
        if zero_values > 0:
            logger.warning(
                "%d has %d records with $0 assessed value.", year, zero_values
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate the download, cleaning, validation, and saving pipeline."""
    args = parse_arguments()

    os.makedirs(args.output, exist_ok=True)
    logger.info("Output directory: %s", os.path.abspath(args.output))
    logger.info("Years to download: %s", args.years)

    all_frames = []

    for year in args.years:
        df_raw = fetch_year_data(year)

        if df_raw is None:
            logger.error("Skipping year %d due to download failure.", year)
            continue

        df_clean = clean_columns(df_raw)
        validate_data(df_clean, year)

        # Save individual year file
        filepath = os.path.join(args.output, f"property_assessment_{year}.csv")
        save_to_csv(df_clean, filepath)

        all_frames.append(df_clean)

    # Save combined file for convenience
    if all_frames:
        df_combined = pd.concat(all_frames, ignore_index=True)
        combined_path = os.path.join(args.output, "property_assessment_combined.csv")
        save_to_csv(df_combined, combined_path)
        logger.info(
            "Combined dataset: %s total records across %d years.",
            f"{len(df_combined):,}",
            len(all_frames),
        )
    else:
        logger.error("No data downloaded. Check your network connection and try again.")
        sys.exit(1)

    logger.info("Download complete.")


if __name__ == "__main__":
    main()
