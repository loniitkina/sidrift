#!/bin/bash

# Check if the CSV file exists
if [ ! -f "$1" ]; then
    echo "CSV file not found."
    exit 1
fi

# Read the CSV file line by line
while IFS="," read -r name date lon lat; do
    # Skip the header row
    if [[ "$name" == "name" ]]; then
        continue
    fi

    # Construct the Python command
    python_command="python3 bin/sidtrack -- $date $lon $lat AA_Lucie/$name.csv"

    # Execute the Python command
    echo "$python_command"
    eval "$python_command"
done < "$1"
