#!/usr/bin/env python3

"""
This script is used to export AWS SSO credentials as environment variables for the current shell session.
These credentials can then be used by tools such as Terraform that require AWS credentials.

Prerequisites:
- AWS CLI installed and configured for SSO.
- AWS SSO login performed:
    - Configure SSO: `aws configure sso --profile <PROFILE_NAME>`
    - Login to SSO: `aws sso login --profile <PROFILE_NAME>`

Usage:
1. Run the script: `python3 /usr/local/bin/aws_sso_export.py` to display export commands of AWS_* var
2. Run `eval $(/usr/local/bin/aws_sso_export.py)` to export var in the current environment
3. The script sets AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN for the current session.
4. Run your AWS-dependent tools (like Terraform) in the same session.

Note:
- The script must be run in the same shell session where you intend to use the AWS credentials.
- The credentials will expire according to the SSO session's lifetime and will need to be refreshed with a new `aws sso login`.
"""

import json
import os
import subprocess
from pathlib import Path

def find_newest_file(paths):
    latest_time = None
    latest_file = None

    for path in paths:
        if path.exists() and path.is_dir():
            for file in path.iterdir():
                if file.is_file() and (latest_time is None or file.stat().st_mtime > latest_time):
                    latest_time = file.stat().st_mtime
                    latest_file = file

    return latest_file

def get_profile_name():
    config_path = Path(os.path.expanduser('~/.aws/config'))
    profile_name = None

    if config_path.is_file():
        with open(config_path, 'r') as file:
            for line in file:
                if line.startswith('[profile '):
                    # Extracting profile name
                    profile_name = line.split()[1].strip('[]')
                    break
    return profile_name

def main():
    # Paths to the AWS CLI and SSO cache directories
    sso_cache_path = Path(os.path.expanduser('~/.aws/sso/cache'))
    cli_cache_path = Path(os.path.expanduser('~/.aws/cli/cache'))

    # Find the most recently modified file in both cache directories
    latest_file = find_newest_file([sso_cache_path, cli_cache_path])

    if not latest_file:
        print("No AWS SSO cache files found.")
        return

    # Check if the newest file is under sso cache and execute aws command
    if str(latest_file).startswith(str(sso_cache_path)):
        profile_name = get_profile_name()
        if profile_name:
            subprocess.run(["aws", "s3", "ls", f"--profile", profile_name], stdout=subprocess.PIPE)
            # Recheck for the latest file in cli cache after the command
            latest_file = find_newest_file([cli_cache_path])

    # Extract the credentials from the file
    with open(latest_file) as f:
        data = json.load(f)
        credentials = data.get('Credentials') or data
        if 'AccessKeyId' in credentials:
            print(f"export AWS_ACCESS_KEY_ID={credentials['AccessKeyId']}")
            print(f"export AWS_SECRET_ACCESS_KEY={credentials['SecretAccessKey']}")
            print(f"export AWS_SESSION_TOKEN={credentials['SessionToken']}")

if __name__ == "__main__":
    main()