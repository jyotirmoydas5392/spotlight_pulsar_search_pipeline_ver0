import os
import shutil
import argparse
from multiprocessing import Pool

def remove_path(path):
    """Remove a file or directory."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Removed directory: {path}")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"Removed file: {path}")
    except Exception as e:
        print(f"Error removing {path}: {e}")

def clean_directory_parallel(target_dir, workers):
    """Remove all files and subdirectories under target_dir using multiprocessing.
    If target_dir does not exist, create it."""
    if not os.path.exists(target_dir):
        print(f"{target_dir} does not exist. Creating directory.")
        os.makedirs(target_dir, exist_ok=True)
        return

    if not os.path.isdir(target_dir):
        print(f"Error: {target_dir} is not a directory.")
        return

    items_to_remove = [
        os.path.join(target_dir, item) for item in os.listdir(target_dir)
    ]

    if not items_to_remove:
        print(f"No files or directories to remove in {target_dir}.")
        return

    with Pool(processes=workers) as pool:
        pool.map(remove_path, items_to_remove)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel clean-up of directory contents.")
    parser.add_argument("target_dir", type=str, help="Target directory whose contents will be cleaned.")
    parser.add_argument("workers", type=int, help="Number of parallel worker processes.")

    args = parser.parse_args()
    clean_directory_parallel(args.target_dir, args.workers)