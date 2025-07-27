#!/usr/bin/env python3
"""
Configuration validation command-line tool for sqlBackup.
Validates configuration files and provides detailed reports.
"""

import os
import sys
import argparse
import configparser
from typing import Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sql_backup.config_validator import get_validation_report, ConfigurationError


def load_config_file(config_path: str) -> Optional[configparser.ConfigParser]:
    """Load configuration file and return ConfigParser object."""
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return None
    
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
        print(f"✅ Configuration file loaded: {config_path}")
        return config
    except configparser.Error as e:
        print(f"❌ Error parsing configuration file: {e}")
        return None


def print_validation_results(report: dict, verbose: bool = False):
    """Print validation results in a formatted way."""
    print("\n" + "=" * 60)
    print("📋 CONFIGURATION VALIDATION REPORT")
    print("=" * 60)
    
    # Overall status
    if report['is_valid']:
        print("🎉 Overall Status: ✅ VALID")
    else:
        print("💥 Overall Status: ❌ INVALID")
    
    print(f"📊 Summary: {report['error_count']} errors, {report['warning_count']} warnings")
    
    # Errors section
    if report['errors']:
        print(f"\n🚨 ERRORS ({len(report['errors'])})")
        print("-" * 40)
        for i, error in enumerate(report['errors'], 1):
            print(f"{i:2}. {error}")
    
    # Warnings section
    if report['warnings']:
        print(f"\n⚠️  WARNINGS ({len(report['warnings'])})")
        print("-" * 40)
        for i, warning in enumerate(report['warnings'], 1):
            print(f"{i:2}. {warning}")
    
    # Recommendations
    if not report['is_valid']:
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        print("1. Fix all errors listed above before running sqlBackup")
        print("2. Review warnings - they may indicate potential issues")
        print("3. Use config.ini.default as a reference for correct configuration")
        print("4. Test configuration changes with this validator")
    
    if report['warnings'] and report['is_valid']:
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        print("1. Review warnings - they may indicate potential issues")
        print("2. Consider addressing warnings for optimal performance")
    
    if report['is_valid'] and not report['warnings']:
        print(f"\n🎯 PERFECT CONFIGURATION!")
        print("-" * 40)
        print("✅ No errors or warnings found")
        print("✅ Configuration is ready for production use")


def print_section_summary(config: configparser.ConfigParser):
    """Print a summary of configuration sections."""
    print(f"\n📁 CONFIGURATION SECTIONS")
    print("-" * 40)
    
    section_descriptions = {
        'backup': 'Backup settings and archive format',
        'mysql': 'MySQL connection and tools configuration',
        'logging': 'Logging level and output settings',
        'telegram': 'Telegram notification settings',
        'email': 'Email notification settings',
        'slack': 'Slack notification settings',
        'sms': 'SMS notification settings (Twilio)',
        'viber': 'Viber notification settings',
        'messenger': 'Messenger notification settings',
        'notification': 'Notification channel configuration',
        'remote': 'Remote upload settings',
        'export': 'Database export options'
    }
    
    for section_name in config.sections():
        description = section_descriptions.get(section_name, 'Custom section')
        option_count = len(config.options(section_name))
        print(f"  [{section_name:12}] {description} ({option_count} options)")
    
    # Check for missing common sections
    missing_sections = []
    essential_sections = ['backup', 'mysql']
    recommended_sections = ['logging']
    
    for section in essential_sections:
        if not config.has_section(section):
            missing_sections.append(f"❌ [{section}] - Required")
    
    for section in recommended_sections:
        if not config.has_section(section):
            missing_sections.append(f"⚠️  [{section}] - Recommended")
    
    if missing_sections:
        print(f"\n📋 MISSING SECTIONS")
        print("-" * 40)
        for missing in missing_sections:
            print(f"  {missing}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Validate sqlBackup configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s config.ini                    # Validate config.ini
  %(prog)s config.ini --verbose          # Detailed validation report
  %(prog)s config.ini --sections         # Show section summary
  %(prog)s config.ini --quiet            # Only show overall status
        """
    )
    
    parser.add_argument(
        'config_file',
        nargs='?',
        default='config.ini',
        help='Configuration file to validate (default: config.ini)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed validation information'
    )
    
    parser.add_argument(
        '-s', '--sections',
        action='store_true',
        help='Show configuration sections summary'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Only show overall validation status'
    )
    
    parser.add_argument(
        '--check-dependencies',
        action='store_true',
        help='Check if optional dependencies are installed'
    )
    
    args = parser.parse_args()
    
    # Load configuration file
    config = load_config_file(args.config_file)
    if config is None:
        return 1
    
    # Show sections summary if requested
    if args.sections:
        print_section_summary(config)
    
    # Check dependencies if requested
    if args.check_dependencies:
        print(f"\n🔍 DEPENDENCY CHECK")
        print("-" * 40)
        
        dependencies = {
            'requests': 'HTTP notifications (Telegram, Slack, Viber)',
            'paramiko': 'SFTP remote uploads',
            'twilio': 'SMS notifications'
        }
        
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                print(f"✅ {dep:10} - {description}")
            except ImportError:
                print(f"❌ {dep:10} - {description} (install with: pip install {dep})")
    
    # Perform validation
    report = get_validation_report(config)
    
    # Print results based on verbosity
    if args.quiet:
        if report['is_valid']:
            print("✅ Configuration is valid")
            return 0
        else:
            print(f"❌ Configuration is invalid ({report['error_count']} errors)")
            return 1
    else:
        print_validation_results(report, args.verbose)
    
    # Return appropriate exit code
    return 0 if report['is_valid'] else 1


if __name__ == "__main__":
    sys.exit(main())
