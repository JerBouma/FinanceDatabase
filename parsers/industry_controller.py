"""Industry controller module for categorizing financial instruments."""

import argparse
import os
import sys
import time

import pandas as pd
from google import genai

from parsers import helpers

# pylint: disable=broad-exception-caught


# Hardcoded, needs to change based on the information in the dataset
OPTIONS = {
    "Energy": {
        "Energy": ["Energy Equipment & Services", "Oil, Gas & Consumable Fuels"]
    },
    "Materials": {
        "Materials": [
            "Chemicals",
            "Construction Materials",
            "Containers & Packaging",
            "Metals & Mining",
            "Paper & Forest Products",
        ]
    },
    "Industrials": {
        "Capital Goods": [
            "Aerospace & Defense",
            "Building Products",
            "Construction & Engineering",
            "Electrical Equipment",
            "Industrial Conglomerates",
            "Machinery",
            "Trading Companies & Distributors",
        ],
        "Commercial & Professional Services": [
            "Commercial Services & Supplies",
            "Professional Services",
        ],
        "Transportation": [
            "Air Freight & Logistics",
            "Airlines",
            "Marine",
            "Road & Rail",
            "Transportation Infrastructure",
        ],
    },
    "Consumer Discretionary": {
        "Automobiles & Components": ["Auto Components", "Automobiles"],
        "Consumer Durables & Apparel": [
            "Household Durables",
            "Leisure Products",
            "Textiles, Apparel & Luxury Goods",
        ],
        "Consumer Services": [
            "Hotels, Restaurants & Leisure",
            "Diversified Consumer Services",
        ],
        "Retailing": [
            "Distributors",
            "Internet & Direct Marketing Retail",
            "Multiline Retail",
            "Specialty Retail",
        ],
    },
    "Consumer Staples": {
        "Food & Staples Retailing": ["Food & Staples Retailing"],
        "Food, Beverage & Tobacco": ["Beverages", "Food Products", "Tobacco"],
        "Household & Personal Products": ["Household Products", "Personal Products"],
    },
    "Health Care": {
        "Health Care Equipment & Services": [
            "Health Care Equipment & Supplies",
            "Health Care Providers & Services",
            "Health Care Technology",
        ],
        "Pharmaceuticals, Biotechnology & Life Sciences": [
            "Biotechnology",
            "Pharmaceuticals",
            "Life Sciences Tools & Services",
        ],
    },
    "Financials": {
        "Banks": ["Banks", "Thrifts & Mortgage Finance"],
        "Diversified Financials": [
            "Diversified Financial Services",
            "Consumer Finance",
            "Capital Markets",
            "Mortgage Real Estate Investment \nTrusts (REITs)",
        ],
        "Insurance": ["Insurance"],
    },
    "Information Technology": {
        "Software & Services": ["IT Services", "Software"],
        "Technology Hardware & Equipment": [
            "Communications Equipment",
            "Technology Hardware, Storage & Peripherals",
            "Electronic Equipment, Instruments & Components",
        ],
        "Semiconductors & Semiconductor Equipment": [
            "Semiconductors & Semiconductor Equipment"
        ],
    },
    "Communication Services": {
        "Telecommunication Services": [
            "Diversified Telecommunication Services",
            "Wireless Telecommunication Services",
        ],
        "Media & Entertainment": [
            "Media",
            "Entertainment",
            "Interactive Media & Services",
        ],
    },
    "Utilities": {
        "Utilities": [
            "Electric Utilities",
            "Gas Utilities",
            "Multi-Utilities",
            "Water Utilities",
            "Independent Power and Renewable Electricity Producers",
        ]
    },
    "Real Estate": {
        "Real Estate": [
            "Equity Real Estate Investment Trusts (REITs)",
            "Real Estate Management & Development",
        ]
    },
}


def filter_dataset(
    dataset: pd.DataFrame,
    category_column: str,
    name_column: str,
    all_rows: bool = False,
) -> pd.DataFrame:
    """
    Filter dataset to include only rows with missing categories but existing names.

    Args:
        dataset (pd.DataFrame): Dataset to filter
        category_column (str): Column name containing categories
        name_column (str): Column name containing instrument names
        all_rows (bool, optional): If True, include all rows with names. Defaults to False.

    Returns:
        pd.DataFrame: Filtered dataset
    """
    if all_rows:
        return dataset[~dataset[name_column].isna()]
    return dataset[dataset[category_column].isna() & ~dataset[name_column].isna()]


def process_categories(
    dataset: pd.DataFrame,
    symbol_column: str,
    name_column: str,
    summary_column: str,
    sector_column: str,
    industry_group_column: str,
    pickle_file_name: str,
    categories_dict: dict = None,
    batch_size: int = 100,
    model: str = "gemini-2.0-flash",
):
    """
    Process instrument industries using Gemini AI for instruments with missing industries.

    Args:
        dataset (pd.DataFrame): Dataset containing instruments to process
        symbol_column (str): Column name containing instrument symbols/tickers
        name_column (str): Column name containing instrument names
        summary_column (str): Column name containing instrument summaries
        sector_column (str): Column name containing sector information
        industry_group_column (str): Column name containing industry group information
        pickle_file_name (str): File path to save the generated industries
        categories_dict (dict, optional): Dictionary of existing industries. Defaults to empty dict.
        batch_size (int, optional): Number of instruments to process in each batch. Defaults to 100.
        model (str, optional): Gemini model to use. Defaults to "gemini-2.0-flash".

    Returns:
        dict: Updated industries dictionary
    """
    if categories_dict is None:
        categories_dict = {}

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

    # Calculate total number of equities to process for percentage tracking
    total_to_process = len(dataset)
    print(f"Processing {total_to_process} instruments with missing categories")

    for index, row in dataset.iterrows():
        # Skip if we already have this symbol
        if row[symbol_column] in categories_dict:
            processed_instruments += 1
            continue

        if batch_content == "EMPTY":
            batch_content = (
                "Task: Provide a industry picking from a predefined list, do this for the following tickers.\n\n"
                "Instructions:\n"
                "1. Give ONLY the instrument industry, nothing else\n"
                "3. Format as: TICKER: industry FULL_STOP\n"
                "4. If you don't know an instrument, write 'TICKER: EMPTY FULL_STOP'\n"
                "5. Do not include commentary, explanations, or questions\n\n"
                "Tickers to describe:\n"
            )

        summary_string = (
            f" and summary: {row[summary_column]}" if row[summary_column] else ""
        )

        if (
            row[sector_column] not in OPTIONS
            or row[industry_group_column] not in OPTIONS[row[sector_column]]
        ):
            continue

        batch_content += (
            f"- {row[symbol_column]} (name: {row[name_column]}{summary_string}) "
            f"choose ONLY from {OPTIONS[row[sector_column]][row[industry_group_column]]}\n"
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
                        f"Batch processed ({total_instruments} instruments), {percent_done:.2f}% done, "
                        f"response length: {len(response_text)}"
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
                                    categories_dict[ticker] = description
                                    new_categories += 1
                    except Exception as parsing_error:
                        print(
                            f"Error while parsing response: {parsing_error}. Continuing with next batch..."
                        )

                    # Save to pickle after each successful batch
                    pd.DataFrame.from_dict(categories_dict, orient="index").to_pickle(
                        pickle_file_name
                    )
                    print(
                        f"Saved {new_categories} new categories, {len(categories_dict)} total in pickle file"
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

    return categories_dict


def main():
    """
    Main function to process industry classifications for financial instruments.

    Parses command line arguments and executes the industry classification workflow.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process instrument industry using Gemini AI"
    )
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset file")
    parser.add_argument(
        "--symbol-column", required=True, help="Column name containing symbols/tickers"
    )
    parser.add_argument(
        "--name-column", required=True, help="Column name containing instrument names"
    )
    parser.add_argument(
        "--summary-column",
        required=True,
        help="Column name containing summaries/descriptions",
    )
    parser.add_argument(
        "--industry-column",
        required=False,
        default="industry",
        help="Column name containing industry",
    )
    parser.add_argument(
        "--industry-group-column",
        required=False,
        default="industry_group",
        help="Column name containing industry group",
    )
    parser.add_argument(
        "--sector-column",
        required=False,
        default="sector",
        help="Column name containing sector",
    )
    parser.add_argument("--all-rows", action="store_true", help="Process all rows")
    parser.add_argument(
        "--output", required=True, help="Path to save the pickle file with categories"
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
        # Confirm if the current OPTIONS list is desired
        if not args.skip_confirmation:
            print("Current category options:")
            for sector, items in OPTIONS.items():
                print(f"{sector}: {items}")

            confirmation = input("\nAre these industries correct? (y/n): ").lower()
            if confirmation not in ["y", "yes"]:
                print("Please modify the OPTIONS list in the script and run again.")
                sys.exit(0)

        # Load and filter dataset
        dataset = helpers.load_dataset(args.dataset)
        filtered_dataset = filter_dataset(
            dataset, args.industry_column, args.name_column, args.all_rows
        )

        # Load existing categories
        categories_dict = helpers.load_existing(args.output)

        # Process categories
        process_categories(
            dataset=filtered_dataset,
            symbol_column=args.symbol_column,
            name_column=args.name_column,
            summary_column=args.summary_column,
            industry_group_column=args.industry_group_column,
            sector_column=args.sector_column,
            pickle_file_name=args.output,
            categories_dict=categories_dict,
            batch_size=args.batch_size,
            model=args.model,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
