"""
Module for processing instrument descriptions using the Gemini AI API.

This module provides functionality to generate descriptions for financial instruments
by leveraging the Gemini AI model.
"""

import argparse
import os
import sys
import time

import pandas as pd
from google import genai

from parsers import helpers

# pylint: disable=broad-exception-caught


def filter_dataset(
    dataset: pd.DataFrame,
    summary_column: str,
    name_column: str,
    process_all: bool = False,
) -> pd.DataFrame:
    """
    Filter dataset to include only rows with missing summaries but valid names.

    Parameters:
        dataset (pd.DataFrame): The dataset containing instrument information.
        summary_column (str): Column name containing summaries/descriptions.
        name_column (str): Column name containing instrument names.
        process_all (bool, optional): Process all rows regardless of summary status.
                                      Defaults to False.

    Returns:
        pd.DataFrame: Filtered dataset containing only instruments with missing descriptions
                     but valid names, or all instruments with valid names if process_all is True.
    """
    if process_all:
        return dataset[~dataset[name_column].isna()]

    return dataset[dataset[summary_column].isna() & ~dataset[name_column].isna()]


def process_descriptions(
    dataset: pd.DataFrame,
    symbol_column: str,
    name_column: str,
    pickle_file_name: str,
    descriptions_dict: dict = None,
    batch_size: int = 100,
    model: str = "gemini-2.0-flash",
):
    """
    Process instrument descriptions using Gemini AI for instruments with missing descriptions.

    Parameters:
        dataset (pd.DataFrame): Dataset containing instruments to process.
        symbol_column (str): Column name containing instrument symbols/tickers.
        name_column (str): Column name containing instrument names.
        pickle_file_name (str): File path to save the generated descriptions.
        descriptions_dict (dict, optional): Dictionary of existing descriptions.
                                            Defaults to empty dict.
        batch_size (int, optional): Number of instruments to process in each batch.
                                   Defaults to 100.
        model (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".

    Returns:
        dict: Updated descriptions dictionary.

    Raises:
        ValueError: If GEMINI_API_KEY environment variable is not set.
    """
    if descriptions_dict is None:
        descriptions_dict = {}

    # Assumes you have an environment variable GEMINI_API_KEY set with your API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    # Initialize variables that were previously globals
    batch_content = "EMPTY"
    total_instruments = 0
    processed_instruments = 0
    new_descriptions = 0
    descriptions_list = []

    # Calculate total number of equities to process for percentage tracking
    total_to_process = len(dataset)
    print(f"Processing {total_to_process} companies with missing descriptions")

    for index, row in dataset.iterrows():
        # Skip if we already have this symbol
        if row[symbol_column] in descriptions_dict:
            processed_instruments += 1
            continue

        if batch_content == "EMPTY":
            batch_content = (
                "Task: Provide a detailed instrument descriptions for the following tickers.\n\n"
                "Instructions:\n"
                "1. Give ONLY the instrument description, nothing else\n"
                "2. approximately 3 sentences. \n"
                "3. Format as: TICKER: DESCRIPTION FULL_STOP\n"
                "4. If you don't know an instrument, write 'TICKER: EMPTY FULL_STOP'\n"
                "5. Do not include commentary, explanations, or questions\n\n"
                "Tickers to describe:\n"
            )

        batch_content += f"- {row[symbol_column]} (name: {row[name_column]})\n"
        total_instruments += 1

        if (
            total_instruments >= batch_size or index == len(dataset) - 1
        ) and total_instruments > 0:
            batch_content += (
                "\nRemember to separate each instrument description with the phrase 'FULL_STOP' "
                "and use the exact format 'TICKER: DESCRIPTION FULL_STOP' for each entry."
            )

            while True:
                try:
                    response = client.models.generate_content(
                        model=model, contents=batch_content
                    )

                    if response.text is None:
                        print("Response text is None. Retrying in 10 seconds...")
                        time.sleep(10)
                        continue

                    # Add the raw response to the list
                    response_text = response.text
                    descriptions_list.append(response_text)

                    processed_instruments += total_instruments

                    # Calculate and display percentage done
                    percent_done = (processed_instruments / total_to_process) * 100
                    print(
                        f"Batch processed ({total_instruments} instruments), {percent_done:.2f}% "
                        f"done, response length: {len(response_text)}"
                    )

                    try:
                        # Parse the descriptions
                        descriptions = response_text.split("FULL_STOP")
                        for desc in descriptions:
                            if ":" in desc:
                                parts = desc.split(":", 1)  # Split only on first colon
                                ticker = parts[0].strip()
                                description = parts[1].strip() if len(parts) > 1 else ""

                                # Skip empty descriptions
                                if description and description != "EMPTY":
                                    # Store as dictionary in descriptions_dict
                                    descriptions_dict[ticker] = description
                                    new_descriptions += 1
                    except Exception as parsing_error:
                        print(
                            f"Error while parsing response: {parsing_error}. "
                            "Continuing with next batch..."
                        )

                    # Save to pickle after each successful batch
                    pd.DataFrame.from_dict(descriptions_dict, orient="index").to_pickle(
                        pickle_file_name
                    )
                    print(
                        f"Saved {new_descriptions} new descriptions, "
                        f"{len(descriptions_dict)} total in pickle file"
                    )

                    batch_content = "EMPTY"
                    total_instruments = 0
                    new_descriptions = 0

                    break
                except Exception as e:
                    print(f"An error occurred: {e}. Retrying in 60 seconds...")
                    time.sleep(60)

    print(
        f"Completed processing with {processed_instruments} instruments processed (100% done)"
    )
    return descriptions_dict


def main():
    """
    Main function to process instrument descriptions using command line arguments.

    Parses command line arguments, loads and filters the dataset, and processes
    descriptions using the Gemini AI model.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process instrument descriptions using Gemini AI"
    )
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset file")
    parser.add_argument(
        "--symbol-column",
        required=False,
        default="symbol",
        help="Column name containing symbols/tickers",
    )
    parser.add_argument(
        "--name-column",
        required=False,
        default="name",
        help="Column name containing instrument names",
    )
    parser.add_argument(
        "--summary-column",
        required=False,
        default="summary",
        help="Column name containing summaries/descriptions",
    )
    parser.add_argument(
        "--process-all", required=False, action="store_true", help="Process all rows"
    )
    parser.add_argument(
        "--output", required=True, help="Path to save the pickle file with descriptions"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of instruments to process in each batch",
    )
    parser.add_argument(
        "--model", default="gemini-2.0-flash", help="Gemini model to use"
    )

    args = parser.parse_args()

    try:
        # Load and filter dataset
        dataset = helpers.load_dataset(args.dataset)
        filtered_dataset = filter_dataset(
            dataset, args.summary_column, args.name_column, args.process_all
        )

        # Load existing descriptions
        descriptions_dict = helpers.load_existing(args.output)

        # Process descriptions
        process_descriptions(
            dataset=filtered_dataset,
            symbol_column=args.symbol_column,
            name_column=args.name_column,
            pickle_file_name=args.output,
            descriptions_dict=descriptions_dict,
            batch_size=args.batch_size,
            model=args.model,
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
