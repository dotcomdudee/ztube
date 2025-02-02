#####################################################
#
# https://github.com/dotcomdudee/exportsubscriptions
#
# This script will extract channel names and IDs from sourcecode 
# It's super fast, and the easiest way to extract your data from YouTube 
# Place your "viewsource.txt" file in the same directory as this Python script 
# Run 'python3 getsubs.py'
# A yml will be generated in the same directory
#
#####################################################

import re
import yaml

def extract_channels_to_yaml(input_file, output_file):
    # Read the content of the file
    with open(input_file, "r", encoding="utf-8") as file:
        content = file.read()

    # Regular expression to extract channel names and IDs
    channel_pattern = re.findall(r'"title":{"simpleText":"(.*?)"}.*?"browseId":"(UC[\w-]+)"', content)

    # Format data for YAML
    yaml_data = {"channels": [f"{channel_id} # {channel_name}" for channel_name, channel_id in channel_pattern]}

    # Save to YAML file
    with open(output_file, "w", encoding="utf-8") as yaml_file:
        yaml.dump(yaml_data, yaml_file, default_flow_style=False, allow_unicode=True)

    print(f"Extraction completed! YAML file saved at: {output_file}")

# Example usage:
input_file = "viewsource.txt"  # Change this to your actual file path
output_file = "extracted_channels.yml"

extract_channels_to_yaml(input_file, output_file)
