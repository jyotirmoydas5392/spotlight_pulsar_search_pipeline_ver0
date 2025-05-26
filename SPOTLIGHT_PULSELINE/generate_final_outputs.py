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
    from final_outputs import *
    from read_input_file_dir import load_parameters
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Define configuration file path
config_file_path = os.path.join(base_dir, "input_file_dir_init/input_dir/input_file_directory.txt")

def generate_final_outputs(scan_id, data_id, band_id):
    """Generates the final output PDF and info file."""

    # Load configuration file for importing paths
    if not os.path.exists(config_file_path):
        print(f"Error: Configuration file not found: {config_file_path}")
        sys.exit(1)

    try:
        params = load_parameters(config_file_path)
    except Exception as e:
        print(f"Error loading parameters from configuration file: {e}")
        sys.exit(1)

    # Classified candidate files directory
    classifier_output_dir = os.path.join(params.get('classifier_output_dir'), data_id)
    final_positive_outputs_input_dir = os.path.join(classifier_output_dir, "positive_candidates")
    final_negative_outputs_input_dir = os.path.join(classifier_output_dir, "negative_candidates")
    final_outputs_output_dir = os.path.join(params.get("raw_input_base_dir"), scan_id, "PulsarPipeData", data_id)

    # Ensure output directory exists
    os.makedirs(final_outputs_output_dir, exist_ok=True)

    # Generate the final PDF output from the PNG files for positive as well as negative candidates
    pngs_to_pdf(final_positive_outputs_input_dir, final_outputs_output_dir, data_id, "positively")
    pngs_to_pdf(final_negative_outputs_input_dir, final_outputs_output_dir, data_id, "negatively")


    # Copy one header file for observation information extraction
    header_input_dir = os.path.join(params.get("raw_input_base_dir"), scan_id, params.get("fil_flag"), data_id)
    header_output_dir = final_outputs_output_dir
    copy_one_header_file(header_input_dir, header_output_dir)


    # Create summary TXT file for displaying the observation informations (reads the header file internally to extract informations).
    write_outputs_info(final_outputs_output_dir, data_id, band_id)

    
    # Define the additional paths to copy the required outputs
    folding_output_dir = os.path.join(params.get("pulseline_output_dir"), data_id)
    folding_output_copy_dir = os.path.join(final_outputs_output_dir, "folding_outputs")
    classifier_output_copy_dir = os.path.join(final_outputs_output_dir, "classifier_outputs")

    # Ensure output directory exists
    os.makedirs(folding_output_copy_dir, exist_ok=True)
    os.makedirs(classifier_output_copy_dir, exist_ok=True)

    # Copy the required outputs
    copy_contents_only(folding_output_dir, folding_output_copy_dir)           # Copy folding outputs
    copy_contents_only(classifier_output_dir, classifier_output_copy_dir)     # Copy classifier outputs


def main():
    """Main function to run the final output generation."""
    parser = argparse.ArgumentParser(description="Generate final outputs from candidate plots.")
    parser.add_argument("scan_id", type=str, help="Scan ID of the observation.")
    parser.add_argument("data_id", type=str, help="Data ID of the candidate.")
    parser.add_argument("band_id", type=str, help="Band ID of the observation.")

    args = parser.parse_args()

    generate_final_outputs(args.scan_id, args.data_id, args.band_id)

if __name__ == "__main__":
    main()