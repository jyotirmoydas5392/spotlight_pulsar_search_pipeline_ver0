import os
import sys
import argparse
import numpy as np

# Get the base directory from the environment variable
base_dir = os.getenv("PULSELINE_VER0_DIR")
if not base_dir:
    print("Error: PULSELINE_VER0_DIR environment variable is not set.")
    sys.exit(1)

# List of relative paths to add dynamically
relative_paths = [
    "input_file_dir_init/scripts",
    "SPOTLIGHT_PULSELINE/scripts",
]

# Loop through and add each path to sys.path
for relative_path in relative_paths:
    full_path = os.path.join(base_dir, relative_path)
    sys.path.insert(0, full_path)

# Import necessary functions
try:
    from classifier import *
    from read_input_file_dir import load_parameters
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Define configuration file path
config_file_path = os.path.join(base_dir, "input_file_dir_init/input_dir/input_file_directory.txt")

# Define the folded outputs directory name
folded_outputs = "folded_outputs/"

def run_classifier(data_id):
    """Runs the classifier using parameters from the configuration file."""
    
    # Load configuration file for importing paths
    if not os.path.exists(config_file_path):
        print(f"Error: Configuration file not found: {config_file_path}")
        sys.exit(1)

    try:
        params = load_parameters(config_file_path)
    except Exception as e:
        print(f"Error loading parameters from configuration file: {e}")
        sys.exit(1)

    # Extract parameters from config
    machine_learning_files_path = params.get('machine_learning_files_path')
    python2_env_path = params.get('python2_env_path')
    pulseline_output_dir = params.get('pulseline_output_dir')

    # Classifier input directory is same as pulseline output directory
    classifier_input_dir = os.path.join(pulseline_output_dir, data_id) 
    classifier_output_dir = params.get('classifier_output_dir')

    if not all([machine_learning_files_path, python2_env_path, classifier_input_dir, classifier_output_dir]):
        print("Error: Missing required parameters in the configuration file.")
        sys.exit(1)

    # Classifier output path
    classifier_output_path = os.path.join(classifier_output_dir, data_id)
    os.makedirs(classifier_output_path, exist_ok=True)

    # PFD files directory
    classifier_pfd_files_dir = os.path.join(classifier_input_dir, folded_outputs)

    # Execute the classifier function
    classifier_cmds(classifier_pfd_files_dir, classifier_output_path, python2_env_path, machine_learning_files_path)

# Run the function if the script is executed
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the classifier on given data_id.")
    parser.add_argument("data_id", type=str, help="Data ID for which to run the classifier.")
    
    args = parser.parse_args()
    run_classifier(args.data_id)