"""
Module for processing and generating financial instrument codes using Gemini AI.
"""

import argparse
import os
import sys
import time

import pandas as pd
from google import genai

from parsers import helpers

# pylint: disable=broad-exception-caught


def filter_dataset(dataset: pd.DataFrame, name_column: str) -> pd.DataFrame:
    """
    Filter dataset to include only rows with existing names.

    Args:
        dataset (pd.DataFrame): Dataset to filter
        name_column (str): Column name containing instrument names

    Returns:
        pd.DataFrame: Filtered dataset
    """
    return dataset[~dataset[name_column].isna()]


def process_categories(
    dataset: pd.DataFrame,
    symbol_column: str,
    name_column: str,
    summary_column: str,
    code_type: str,
    code_example: str,
    pickle_file_name: str,
    code_dict: dict = None,
    batch_size: int = 100,
    model: str = "gemini-2.0-flash",
):
    """
    Process instrument codes using Gemini AI for instruments with missing codes.

    Args:
        dataset (pd.DataFrame): Dataset containing instruments to process
        symbol_column (str): Column name containing instrument symbols/tickers
        name_column (str): Column name containing instrument names
        summary_column (str): Column name containing instrument summaries
        code_type (str): Type of code to generate (e.g., ISIN, CUSIP)
        code_example (str): Example of the expected code format
        pickle_file_name (str): File path to save the generated codes
        code_dict (dict, optional): Dictionary of existing codes. Defaults to None.
        batch_size (int, optional): Number of instruments to process in each batch. Defaults to 100.
        model (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".

    Returns:
        dict: Updated codes dictionary
    """
    # Initialize code_dict if None
    if code_dict is None:
        code_dict = {}

    # Assumes you have an environment variable GEMINI_API_KEY set with your API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    # Initialize variables that were previously globals
    batch_content = "EMPTY"
    total_instruments = 0
    processed_instruments = 0
    new_categories = 0
    descriptions_list = []

    # Calculate total number of instruments to process for percentage tracking
    total_to_process = len(dataset)
    print(f"Processing {total_to_process} instruments with missing codes")

    for index, row in dataset.iterrows():
        # Skip if we already have this symbol
        if row[symbol_column] in code_dict:
            processed_instruments += 1
            continue

        if batch_content == "EMPTY":
            batch_content = (
                f"Task: Provide {code_type} codes such as {code_example}, do this for the following tickers.\n\n"
                "Instructions:\n"
                f"1. Give ONLY the instrument {code_type} code, nothing else\n"
                f"3. Format as: TICKER: {code_type} code FULL_STOP\n"
                "4. If you don't know an instrument, write 'TICKER: EMPTY FULL_STOP'\n"
                "5. Do not include commentary, explanations, or questions\n\n"
                "Tickers to describe:\n"
            )

        summary_string = (
            f" and summary: {row[summary_column]}" if row[summary_column] else ""
        )

        batch_content += (
            f"- {row[symbol_column]} (name: {row[name_column]}{summary_string})\n"
        )
        total_instruments += 1

        if (
            total_instruments >= batch_size or index == len(dataset) - 1
        ) and total_instruments > 0:
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
                        f"Batch processed ({total_instruments} instruments), "
                        f"{percent_done:.2f}% done, response "
                        f"length: {len(response_text)}"
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
                                    # Store as dictionary in code_dict
                                    code_dict[ticker] = description
                                    new_categories += 1
                    except Exception as parsing_error:
                        print(
                            f"Error while parsing response: {parsing_error}. Continuing with next batch..."
                        )

                    # Save to pickle after each successful batch
                    pd.DataFrame.from_dict(code_dict, orient="index").to_pickle(
                        pickle_file_name
                    )
                    print(
                        f"Saved {new_categories} new codes, {len(code_dict)} total in pickle file"
                    )

                    batch_content = "EMPTY"
                    total_instruments = 0
                    new_categories = 0

                    break
                except Exception as e:
                    print(f"An error occurred: {e}. Retrying in 60 seconds...")
                    time.sleep(60)

    print(
        f"Completed processing with {processed_instruments} instruments processed (100% done)"
    )

    return code_dict


def main():
    """
    Main function to parse arguments and process instrument codes.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process instrument codes using Gemini AI"
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
        "--code-type",
        required=True,
        help="Type of code to generate (e.g., ISIN, CUSIP)",
    )
    parser.add_argument(
        "--output", required=True, help="Path to save the pickle file with codes"
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
    parser.add_argument(
        "--skip-confirmation",
        action="store_true",
        help="Skip confirmation of category options",
    )

    args = parser.parse_args()

    try:
        code_examples = {
            "ISIN": "US00846U1016",
            "CUSIP": "00846U101",
            "FIGI": "BBG000C2V541",
            "COMPOSITE_FIGI": "BBG000C2V3D6",
            "SHARECLASS_FIGI": "BBG001SCTQY4",
        }

        # Load and filter dataset
        dataset = helpers.load_dataset(args.dataset)
        filtered_dataset = filter_dataset(dataset, args.name_column)

        # Load existing categories
        code_dict = helpers.load_existing(args.output)

        # Process categories
        process_categories(
            dataset=filtered_dataset,
            symbol_column=args.symbol_column,
            name_column=args.name_column,
            summary_column=args.summary_column,
            code_type=args.code_type,
            code_example=code_examples[args.code_type],
            pickle_file_name=args.output,
            code_dict=code_dict,
            batch_size=args.batch_size,
            model=args.model,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
