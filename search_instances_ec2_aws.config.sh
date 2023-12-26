#!/bin/bash

# Default profile set to the first profile found in .aws/config
DEFAULT_PROFILE=$(awk -F' ' '/^\[profile/ {gsub(/\[|\]/,""); print $2; exit}' ~/.aws/config)
PROFILE=$DEFAULT_PROFILE
IP_ADDRESS=""  # New variable for IP address

# Flag for displaying start-session command
DISPLAY_COMMAND=false

# Function to display available profiles
display_profiles() {
    echo "Available AWS CLI profiles:"
    awk -F' ' '/^\[profile/ {gsub(/\[|\]/,""); print $2}' ~/.aws/config
}

# Function to display script usage
usage() {
    echo "Usage: $0 -k <key_word> [-p <profile>] [-c] [-i <ip_address>]"
    echo "Options :"
    echo "  -k <key_word> : Specify the keyword to search"
    echo "  -p <profile> : Specify the AWS CLI profile (default: $DEFAULT_PROFILE)"
    echo "  -c : Display the 'aws ssm start-session' command for each INSTANCE_ID"
    echo "  -i <ip_address> : Specify the IP address to search"
    echo
    display_profiles
    exit 1
}

# Parse command line options
while getopts ":k:p:ci:" opt; do
    case $opt in
        k)
            KEY_WORD=$OPTARG
            ;;
        p)
            PROFILE=$OPTARG
            ;;
        c)
            DISPLAY_COMMAND=true
            ;;
        i)
            IP_ADDRESS=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument."
            usage
            ;;
    esac
done

# Check if mandatory options are provided
if [ -z "$KEY_WORD" ] && [ -z "$IP_ADDRESS" ]; then
    echo "Missing required option: -k <key_word> or -i <ip_address>"
    usage
fi

# Execute AWS CLI command and process the output
# Check if IP_ADDRESS is set and modify the filter accordingly
if [ -n "$IP_ADDRESS" ]; then
    FILTERS="Name=private-ip-address,Values=${IP_ADDRESS}"
else
    FILTERS="Name=tag:Name,Values=*${KEY_WORD}*"
fi

output=$(aws --region eu-west-1 --profile ${PROFILE} ec2 describe-instances --filters "Name=instance-state-name,Values=running" "${FILTERS}" --query "Reservations[*].Instances[*].{InstanceId:InstanceId, Name:Tags[?Key=='Name'].Value | [0], PrivateIpAddress:PrivateIpAddress}" | jq -r '.[][] | [.InstanceId, .Name, .PrivateIpAddress] | @tsv')

# Display INSTANCE_ID, INSTANCE_NAME, INSTANCE_IP
echo "$output"

# Display start-session command for each INSTANCE_ID if -c option is set
if $DISPLAY_COMMAND; then
    while IFS=$'\t' read -r INSTANCE_ID INSTANCE_NAME INSTANCE_IP; do
        echo "aws ssm start-session --profile ${PROFILE} --target $INSTANCE_ID #$INSTANCE_NAME"
    done <<< "$output"
fi