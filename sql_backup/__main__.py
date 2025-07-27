#!/usr/bin/env python3
"""
Main module for running sql_backup as a module.
This allows running the package with: python -m sql_backup
"""

from .main import cli_main

if __name__ == "__main__":
    cli_main()
