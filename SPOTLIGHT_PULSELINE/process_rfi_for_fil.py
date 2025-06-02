import os
import sys
import argparse
import numpy as np

# Get the base directory from an environment variable
base_dir = os.getenv("PULSELINE_VER0_DIR")
if not base_dir:
    print("Error: PULSELINE_VER0_DIR environment variable is not set.")
    sys.exit(1)

# List of relative subdirectories where script modules are located
relative_paths = [
    "input_file_dir_init/scripts",
    "SPOTLIGHT_PULSELINE/scripts"
]

# Add the resolved full paths to sys.path so that Python can find and import them
for relative_path in relative_paths:
    full_path = os.path.join(base_dir, relative_path)
    if os.path.exists(full_path):
        sys.path.insert(0, full_path)
    else:
        print(f"Warning: Path does not exist and won't be added to sys.path: {full_path}")

# Try importing required modules from custom script paths
try:
    from apply_gptool import *                  # Module to apply gptool for RFI cleaning
    from extract_hdr_and_raw import *           # Module to extract .hdr and .raw from .fil
    from read_input_file_dir import load_parameters  # Loads configuration from a directory file
except ImportError as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

# Define the path to the central configuration file
config_file_path = os.path.join(base_dir, "input_file_dir_init/input_dir/input_file_directory.txt")

# Main RFI cleaning function
def clean_rfi(fil_files, data_id, scan_id, band_id):
    """
    Process .fil files to remove RFI using header/raw extraction and gptool filtering.
    
    Args:
        fil_files (list): List of .fil filenames.
        data_id (str): Data identifier for configuration selection (e.g., BAND3).
        scan_id (str): Identifier for the scan/session.
    """

    # Load configuration file and extract paths/settings
    if not os.path.exists(config_file_path):
        print(f"Configuration file not found: {config_file_path}")
        sys.exit(1)

    try:
        params = load_parameters(config_file_path)
    except Exception as e:
        print(f"Error loading parameters from configuration file: {e}")
        sys.exit(1)

    # Extract needed values from configuration
    gptool_module_path = params.get('gptool_module_path')
    gptool_input_file_path = params.get('gptool_input_file_path')
    workers_per_node = params.get('workers_per_node')

    # Sanity check to ensure all required parameters exist
    if None in (gptool_module_path, gptool_input_file_path, workers_per_node):
        print("One or more required parameters missing in configuration file.")
        sys.exit(1)

    # Construct input/output paths
    fil_input_dir = os.path.join(params.get("raw_input_base_dir"), scan_id, params.get("fil_flag"), data_id)
    raw_output_dir = fil_input_dir  # Use same dir for .raw/.hdr output

    # Step 1: Extract .raw and .hdr from each .fil (in parallel)
    process_fil_files_parallelly(
        fil_files=fil_files,
        input_dir=fil_input_dir,
        output_dir=raw_output_dir,
        workers=workers_per_node
    )

    # Step 2: Apply gptool to .raw files and generate cleaned .fil files
    raw_input_dir = fil_input_dir
    fil_output_dir = raw_output_dir
    process_gptool_parallelly(
        fil_files=fil_files,
        input_dir=raw_input_dir,
        input_file_dir=gptool_input_file_path,
        output_dir=fil_output_dir,
        gptool_path=gptool_module_path,
        data_id=data_id,
        band_id = band_id,
        workers=int(workers_per_node/4.0)
    )

# Entry point to make the script executable
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean RFI from .fil files using gptool and extract_hdr_and_raw modules.")
    parser.add_argument("fil_files", help="Comma-separated list of .fil files (e.g., file1.fil,file2.fil)")
    parser.add_argument("data_id", help="Data ID (e.g., BAND3, BAND4, etc.)")
    parser.add_argument("scan_id", help="Scan ID (used to construct paths)")
    parser.add_argument("band_id", help="BAND ID (used to construct paths)")

    args = parser.parse_args()
    fil_file_list = args.fil_files.split(",")

    # Call main cleaning function with parsed arguments
    clean_rfi(fil_file_list, args.data_id, args.scan_id, args.band_id)