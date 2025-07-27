#!/usr/bin/env python3
"""
Setup script for sqlBackup - A modern Python-based backup tool for MySQL databases.
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    """Read README.md for the long description."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt."""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Remove version comments
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    requirements.append(line)
    return requirements

setup(
    name='sqlBackup',  # Use this name for pip install sqlBackup
    version='0.2.2',
    description='A modern Python-based backup tool for MySQL databases',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='GK',
    author_email='gregor@klevze.com',
    url='https://github.com/klevze/sqlBackup',
    
    # Package discovery
    packages=find_packages(),
    include_package_data=True,
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Python version requirement
    python_requires='>=3.6',
    
    # Entry points for command-line usage
    entry_points={
        'console_scripts': [
            'sql-backup=sql_backup:cli_main',
            'sqlbackup=sql_backup:cli_main',  # Alternative name for backward compatibility
        ],
    },  # Make sure sql_backup.cli_main exists and is importable
    
    # Include the main script (deprecated - using entry_points instead)
    # scripts=['sqlBackup'],
    
    # Additional package data
    package_data={
        '': ['config.ini.default', 'README.md', 'LICENSE'],
    },
    
    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Database',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    
    # Keywords for easier discovery
    keywords='mysql backup database dump archive notification sftp ftp telegram email slack sms',
    
    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/klevze/sqlBackup/issues',
        'Source': 'https://github.com/klevze/sqlBackup',
        'Documentation': 'https://github.com/klevze/sqlBackup#readme',
    },
)
