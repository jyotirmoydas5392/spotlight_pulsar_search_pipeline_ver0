import numpy as np
import os

def is_harmonically_related(p1, p2, dm1, dm2, max_harm, period_tol, DM_slope, DM_intercept):
    """
    Check if p1 and p2 are harmonically related up to max_harm and have similar DM.
    Uses dynamic DM tolerance calculated from higher period.
    """
    max_period = max(p1, p2)
    dm_tolerance = DM_intercept + DM_slope * max_period
    period_ratio = p1 / p2
    
    for n in range(1, max_harm + 1):
        for m in range(1, max_harm + 1):
            # Check if period ratio is close to n/m within tolerance
            if abs(period_ratio - (n / m)) < period_tol:
                if abs(dm1 - dm2) <= dm_tolerance:
                    return True
    return False

def union_find_make_set(n):
    return list(range(n))

def union_find_find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union_find_union(parent, a, b):
    pa, pb = union_find_find(parent, a), union_find_find(parent, b)
    if pa != pb:
        parent[pa] = pb

def harmonic_filtering(input_dir, output_dir, file_name, period_tol_harm, max_harm,
                       DM_filtering_cut_10, DM_filtering_cut_1000):
    """
    Perform harmonic filtering on candidates, keeping only the strongest (highest SNR) in each harmonic group.
    
    Args:
        input_dir (str): Directory containing input candidate file
        output_dir (str): Directory to save filtered candidate file
        file_name (str): Base name of candidate file (without extension)
        period_tol_harm (float): Period tolerance factor for harmonic checking (multiplied by period)
        max_harm (int): Maximum harmonic order to check (e.g., 20)
        DM_filtering_cut_10 (float): DM tolerance at 10 ms period
        DM_filtering_cut_1000 (float): DM tolerance at 1000 ms period
    """

    input_path = os.path.join(input_dir, f"{file_name}_all_sifted_candidates.txt")
    output_path = os.path.join(output_dir, f"{file_name}_all_sifted_harmonic_removed_candidates.txt")

    # Read input file
    try:
        with open(input_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Input file {input_path} not found.")
        return

    # If file contains error message, write it back and return
    if len(lines) == 1 and "No valid data found to process." in lines[0]:
        with open(output_path, 'w') as f_out:
            f_out.write("No valid data found to process.\n")
        print(f"No valid data found. Exiting. Response written to {output_path}")
        return

    try:
        # Load data skipping header, columns: Period(sec), Pdot, DM, SNR (assumed)
        data = np.loadtxt(input_path, dtype=float, skiprows=1)
        if data.size == 0:
            raise ValueError("No valid candidate data found in the file.")
    except Exception as e:
        with open(output_path, 'w') as f_out:
            f_out.write("No valid data found to process.\n")
        print(f"Error reading input file: {e}. Response written to {output_path}")
        return

    periods = data[:, 0]
    p_dots = data[:, 1]
    DMs = data[:, 2]
    SNRs = data[:, 3]

    n_candidates = len(periods)

    # Calculate DM tolerance slope and intercept for dynamic DM tolerance
    DM_slope = (DM_filtering_cut_1000 - DM_filtering_cut_10) / (1.000 - 0.010)  # period in seconds
    DM_intercept = DM_filtering_cut_10 - DM_slope * 0.010

    # Build union-find structure for harmonic groups
    parent = union_find_make_set(n_candidates)

    # Period tolerance depends on higher period times period_tol_harm factor
    # We'll use period_tol = higher_period * period_tol_harm

    # Check all candidate pairs for harmonic relation
    for i in range(n_candidates):
        for j in range(i + 1, n_candidates):
            higher_period = max(periods[i], periods[j])
            period_tol = higher_period * period_tol_harm
            if is_harmonically_related(periods[i], periods[j], DMs[i], DMs[j], max_harm, period_tol, DM_slope, DM_intercept):
                union_find_union(parent, i, j)

    # Group candidates by their root parent
    groups = {}
    for idx in range(n_candidates):
        root = union_find_find(parent, idx)
        groups.setdefault(root, []).append(idx)

    # For each group, pick candidate with highest SNR as fundamental and remove others
    fundamental_indices = []
    removed_indices = set()

    for group in groups.values():
        group_snrs = SNRs[group]
        max_snr_idx_in_group = group[np.argmax(group_snrs)]
        fundamental_indices.append(max_snr_idx_in_group)
        # Mark others as removed
        for idx in group:
            if idx != max_snr_idx_in_group:
                removed_indices.add(idx)

    # Candidates to keep = those not removed
    keep_indices = sorted(list(set(range(n_candidates)) - removed_indices))

    filtered_data = data[keep_indices]

    # Sort filtered data by period descending (optional)
    filtered_data = filtered_data[np.argsort(filtered_data[:, 0])[::-1]]

    # Write filtered candidates to output
    with open(output_path, 'w') as f_out:
        f_out.write("Period(sec)   Pdot(s/s)  DM(pc/cc)   SNR\n")
        for row in filtered_data:
            f_out.write(f"{row[0]:.10f}     {row[1]:.6e}     {row[2]:.2f}     {row[3]:.2f}\n")

    print(f"Harmonic filtering done. Results saved to {output_path}")