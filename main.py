#!/usr/bin/env python3
"""CLI entry point for HR document generator."""

import argparse
import json
import sys

from database import MongoDatabase
from llm import LocalLLM
from generator import ReviewGenerator, OnboardingGenerator


def main():
    parser = argparse.ArgumentParser(
        description="HR document generator using local LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --list                      List all employees
  python main.py --employee "John Doe"       Generate review for John Doe
  python main.py --all                       Generate reviews for all employees
  python main.py --onboarding data.json      Generate onboarding plan from JSON
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--employee", "-e",
        type=str,
        metavar="NAME",
        help="Generate review for a specific employee",
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate reviews for all employees",
    )
    group.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all employee names",
    )
    group.add_argument(
        "--onboarding", "-o",
        type=str,
        metavar="JSON_FILE",
        help="Generate onboarding plan from JSON file",
    )

    args = parser.parse_args()

    try:
        # Handle --onboarding (no DB needed)
        if args.onboarding:
            with open(args.onboarding, "r") as f:
                onboarding_data = json.load(f)

            print("Loading LLM model...")
            with LocalLLM() as llm:
                print("Model loaded successfully.\n")
                generator = OnboardingGenerator(llm)
                generator.generate(onboarding_data)
            return 0

        # Database operations
        with MongoDatabase() as db:
            if args.list:
                print("Employees in database:")
                print("-" * 40)
                names = db.list_employee_names()
                if names:
                    for name in names:
                        print(f"  - {name}")
                    print(f"\nTotal: {len(names)} employees")
                else:
                    print("  No employees found.")
                return 0

            print("Loading LLM model...")
            with LocalLLM() as llm:
                print("Model loaded successfully.\n")
                generator = ReviewGenerator(llm, db)

                if args.employee:
                    generator.generate_single(args.employee)
                elif args.all:
                    generator.generate_all()

        return 0

    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
