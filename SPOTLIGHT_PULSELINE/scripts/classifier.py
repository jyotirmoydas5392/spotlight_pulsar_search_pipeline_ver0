import os
import shutil
import numpy as np
import subprocess

def clean_output_dir(output_dir):
    """Removes all files in output_dir without deleting subdirectories."""
    if os.path.exists(output_dir):
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isfile(item_path):  # Only remove files
                os.remove(item_path)

def extract_pfd_basenames(txt_file):
    """Extracts base names of PFD files from a given candidate list file, ignoring the first line."""
    basenames = set()
    if not os.path.exists(txt_file):
        print(f"Warning: {txt_file} not found!")
        return basenames  # Return empty set if file is missing

    with open(txt_file, "r") as file:
        next(file)  # Skip the first line (header)
        for line in file:
            parts = line.strip().split(",")  # Split CSV line
            if parts:
                pfd_path = parts[0].strip()
                pfd_basename = os.path.basename(pfd_path)  # Extract only the filename
                basenames.add(pfd_basename)
    return basenames


def copy_matching_files(source_dir, target_dir, pfd_basenames):
    """Copies all files from source_dir to target_dir if their names contain any pfd_basename."""
    os.makedirs(target_dir, exist_ok=True)  # Ensure target directory exists
    copied_files = 0

    for file in os.listdir(source_dir):
        if any(pfd_name in file for pfd_name in pfd_basenames):  # Match any pfd base name
            src_file = os.path.join(source_dir, file)
            dest_file = os.path.join(target_dir, file)
            shutil.copy(src_file, dest_file)
            copied_files += 1

    return copied_files

def process_candidate_files(input_dir, output_dir):
    """Processes candidates.txt and candidates.txt.negative to copy matching files."""
    positive_candidates_dir = os.path.join(output_dir, "positive_candidates")
    negative_candidates_dir = os.path.join(output_dir, "negative_candidates")

    # Ensure positive and negative candidate directories exist
    os.makedirs(positive_candidates_dir, exist_ok=True)
    os.makedirs(negative_candidates_dir, exist_ok=True)

    # Extract PFD basenames from both candidate files
    positive_pfds = extract_pfd_basenames(os.path.join(output_dir, "candidates.txt"))
    negative_pfds = extract_pfd_basenames(os.path.join(output_dir, "candidates.txt.negative"))

    # Remove existing files in positive and negative candidates directories before copying
    for folder in [positive_candidates_dir, negative_candidates_dir]:
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

    # Copy files for both positive and negative candidates
    total_positive = copy_matching_files(input_dir, positive_candidates_dir, positive_pfds)
    total_negative = copy_matching_files(input_dir, negative_candidates_dir, negative_pfds)

    # Print results
    print(f"Total Positive Candidate Files to Copy: {len(positive_pfds)}")
    print(f"Total Negative Candidate Files to Copy: {len(negative_pfds)}")
    print(f"Copied Positive Candidate Files: {total_positive}")
    print(f"Copied Negative Candidate Files: {total_negative}")


def classifier_cmds(input_dir, output_dir, python_path, ml_path):
    # Construct the first command (Score generation)
    score_script = os.path.join(ml_path, "PulsarProcessingScripts", "src", "CandidateScoreGenerators", "ScoreGenerator.py")
    score_output = os.path.join(output_dir, "scores.arff")

    score_command = (
        f"{python_path} {score_script} "
        f"-c {input_dir} "
        f"-o {score_output} "
        "--pfd --arff --dmprof"
    )

    # Construct the Java command (Classification)
    ml_jar = os.path.join(ml_path, "HTRU_CLASSIFIER_STUFF", "ML.jar")
    model_path = os.path.join(ml_path, "HTRU_CLASSIFIER_STUFF", "DT_LOTAAS.model")
    candidates_output = os.path.join(output_dir, "candidates.txt")

    java_command = (
        f"java -jar {ml_jar} -v "
        f"-m{model_path} "
        f"-o{candidates_output} "
        f"-p{score_output} -a1"
    )

    # Clean the output directory
    clean_output_dir(output_dir)
    
    # Execute commands
    try:
        subprocess.run(score_command, shell=True, check=True)
        subprocess.run(java_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

    # Copy the output classidfied files into defined directories
    process_candidate_files(input_dir, output_dir)