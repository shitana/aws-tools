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
2. Run `eval $(/usr/local/bin/aws_sso_export.py) to export var in the curent environment
3. The script sets AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN for the current session.
4. Run your AWS-dependent tools (like Terraform) in the same session.

Note:
- The script must be run in the same shell session where you intend to use the AWS credentials.
- The credentials will expire according to the SSO session's lifetime and will need to be refreshed with a new `aws sso login`.
"""

import json
import os
import subprocess

def main():
    # Path to the AWS CLI cache directory
    cli_cache_path = os.path.expanduser('~/.aws/cli/cache')

    # Find the most recently modified file in the CLI cache directory
    files = [os.path.join(cli_cache_path, f) for f in os.listdir(cli_cache_path)]
    latest_file = max(files, key=os.path.getmtime)

    # Extract the credentials from the file
    with open(latest_file) as f:
        data = json.load(f)
        credentials = data['Credentials']

    # Set the environment variables (only local process env !!)
    os.environ['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']

    # Print the environment variables (optional for verification)
    print(f"export AWS_ACCESS_KEY_ID={credentials['AccessKeyId']}")
    print(f"export AWS_SECRET_ACCESS_KEY={credentials['SecretAccessKey']}")
    print(f"export AWS_SESSION_TOKEN={credentials['SessionToken']}")

if __name__ == "__main__":
    main()

