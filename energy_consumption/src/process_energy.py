import os
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
import sys
import re

# File paths
TIMESTAMPS_FILE = "search_engine_results/search_engine_timestamps.csv"
ENERGY_LOG_FILE = "energy_log.csv"
OUTPUT_FILE = "results/final_energy_results.csv"

BUFFER = int(os.getenv("INTERVAL", 200))  # Default to 200 if not set

def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")

def load_data(timestamps_file, energy_file):
    log_message(f"Loading timestamps from {timestamps_file}")
    timestamps_df = pd.read_csv(timestamps_file)
    
    log_message(f"Loading energy log from {energy_file}")
    energy_df = pd.read_csv(energy_file)
    
    energy_df["Time"] = pd.to_numeric(energy_df["Time"])
    return timestamps_df, energy_df

def remove_outliers_zscore(samples, threshold=3):
    z_scores = np.abs(stats.zscore(samples))
    return samples[z_scores < threshold]


def compute_energy_dell(subframe):
    """
    For Dell, use the energy column ("PACKAGE_ENERGY (J)"). 
    This function tests the raw samples for normality, removes outliers if needed,
    and returns a tuple: (energy, sw_stat, sw_p, sample_size).
    """
    energy_col = "PACKAGE_ENERGY (J)"
    if energy_col not in subframe.columns:
        return 0.0, None, None, 0
    raw_values = subframe[energy_col].values
    sample_size = len(raw_values)
    sw_stat, sw_p = None, None
    if sample_size >= 3:
        sw_stat, sw_p = stats.shapiro(raw_values)
        log_message(f"Shapiro-Wilk test: stat = {sw_stat:.4f}, p = {sw_p:.4f}")
        if sw_p < 0.05:
            log_message("Data non-normal; removing outliers via Z-score.")
            filtered = remove_outliers_zscore(raw_values, threshold=3)
            if len(filtered) >= 2:
                raw_values = filtered
                sample_size = len(raw_values)
                # Re-run the test on filtered data
                sw_stat, sw_p = stats.shapiro(raw_values)
                log_message(f"After removal: SW stat = {sw_stat:.4f}, p = {sw_p:.4f}")
            else:
                log_message("Not enough data after removal; using original values.")
    # Energy computed as the difference between last and first sample
    if len(raw_values) > 1:
        energy = raw_values[-1] - raw_values[0]
    else:
        energy = 0.0
    return energy, sw_stat, sw_p, sample_size

def compute_energy_macos(subframe):
    """
    For macOS, use the power column ("SYSTEM_POWER (Watts)") and perform trapz integration.
    Returns a tuple: (total_energy, avg_temp, sw_stat, sw_p, sample_size).
    """
    if "SYSTEM_POWER (Watts)" not in subframe.columns:
        return 0.0, None, None, None, 0
    
    times_s = subframe["Time"].values / 1000.0
    raw_power = subframe["SYSTEM_POWER (Watts)"].values
    sample_size = len(raw_power)
    sw_stat, sw_p = None, None
    if sample_size >= 3:
        sw_stat, sw_p = stats.shapiro(raw_power)
        log_message(f"macOS power: SW stat = {sw_stat:.4f}, p = {sw_p:.4f}")
        if sw_p < 0.05:
            log_message("macOS power non-normal; removing outliers via Z-score.")
            mask = np.abs(stats.zscore(raw_power)) < 3
            filtered_power = raw_power[mask]
            filtered_times = times_s[mask]
            if len(filtered_power) >= 2:
                raw_power = filtered_power
                times_s = filtered_times
                sample_size = len(raw_power)
                sw_stat, sw_p = stats.shapiro(raw_power)
                log_message(f"After removal: SW stat = {sw_stat:.4f}, p = {sw_p:.4f}")
            else:
                log_message("Not enough data after removal; using original values.")
    # Also compute average temperature
    all_temps = subframe[['CPU_TEMP_0','CPU_TEMP_1','CPU_TEMP_2','CPU_TEMP_3',
                           'CPU_TEMP_4','CPU_TEMP_5','CPU_TEMP_6','CPU_TEMP_7',
                           'CPU_TEMP_8','CPU_TEMP_9']]
    avg_temp = all_temps.mean(axis=1).values
    if len(times_s) > 1:
        total_energy = np.trapz(raw_power, times_s)
    else:
        total_energy = 0.0
    return total_energy, avg_temp, sw_stat, sw_p, sample_size

def compute_energy_for_interval(energy_df, start_time, end_time):
    buffer_ms = BUFFER
    subframe = energy_df[(energy_df["Time"] >= (start_time - buffer_ms)) &
                         (energy_df["Time"] <= (end_time + buffer_ms))]
    if subframe.empty:
        return 0.0, 0.0, None, None, 0  # (energy, avg_power, sw_stat, sw_p, sample_size)
    
    rapl_cols = [c for c in subframe.columns if "ENERGY (J)" in c]
    has_rapl = len(rapl_cols) > 0
    has_system_power = "SYSTEM_POWER (Watts)" in subframe.columns
    if has_rapl:
        energy, sw_stat, sw_p, sample_size = compute_energy_dell(subframe)
        duration_s = (end_time - start_time) / 1000.0
        avg_power = energy / duration_s if duration_s > 0 else 0.0
    elif has_system_power:
        energy, avg_temp, sw_stat, sw_p, sample_size = compute_energy_macos(subframe)
        avg_power = subframe["SYSTEM_POWER (Watts)"].mean()
    else:
        log_message("Warning: No recognized energy columns found.")
        return 0.0, 0.0, None, None, 0
    return energy, avg_power, sw_stat, sw_p, sample_size

def calculate_energy_consumption(timestamps_df, energy_df):
    """
    For each iteration (row in timestamps_df), compute energy consumption and store
    iteration-level statistics.
    """
    log_message("Calculating energy consumption per iteration.")
    results = []
    for idx, row in timestamps_df.iterrows():
        engine = row["Search Engine"]
        start_time = row["Start Time"]
        end_time = row["End Time"]
        iteration = row["Iteration"]
        log_message(f"Processing {engine} - Iteration {iteration}: {start_time} to {end_time}")
        
        iter_df = energy_df[(energy_df["Time"] >= start_time) &
                            (energy_df["Time"] <= end_time)]
        if iter_df.empty:
            log_message(f"Warning: No energy data for {engine} Iteration {iteration}")
            res = {"Search Engine": engine, "Iteration": iteration,
                   "Total Energy (J)": 0, "Average Power (W)": 0, "Duration (s)": 0,
                   "Energy Delay Product": 0, "SW_stat": None, "SW_p": None, "Sample Size": 0}
        else:
            energy_val, avg_power, sw_stat, sw_p, sample_size = compute_energy_for_interval(iter_df, start_time, end_time)
            duration_s = (end_time - start_time) / 1000.0
            edp = energy_val * duration_s
            res = {"Search Engine": engine, "Iteration": iteration,
                   "Total Energy (J)": energy_val,
                   "Average Power (W)": avg_power,
                   "Duration (s)": duration_s,
                   "Energy Delay Product": edp,
                   "SW_stat": sw_stat,
                   "SW_p": sw_p,
                   "Sample Size": sample_size}
        results.append(res)
    return pd.DataFrame(results)

def aggregate_iteration_statistics(results_df):
    """
    Aggregate iteration-level statistics per search engine.
    Returns a summary DataFrame with average total energy, SW statistic and p-value, etc.
    """
    agg = results_df.groupby("Search Engine").agg({
        "Total Energy (J)": "mean",
        "Average Power (W)": "mean",
        "Duration (s)": "mean",
        "Energy Delay Product": "mean",
        "SW_stat": "mean",
        "SW_p": "mean",
        "Iteration": "count"  # count iterations
    }).rename(columns={"Iteration": "Num Iterations"})
    return agg.reset_index()

def pairwise_comparisons(results_df):
    """
    For each pair of search engines, perform Welch's t-test and compute Cohen's d
    on the Total Energy (J) across iterations. Also, compute the percentage change.
    Returns a DataFrame of pairwise comparison results.
    """
    engines = results_df["Search Engine"].unique()
    comp_results = []
    for i in range(len(engines)):
        for j in range(i+1, len(engines)):
            engA = engines[i]
            engB = engines[j]
            dataA = results_df[results_df["Search Engine"] == engA]["Total Energy (J)"].dropna()
            dataB = results_df[results_df["Search Engine"] == engB]["Total Energy (J)"].dropna()
            if len(dataA) < 2 or len(dataB) < 2:
                continue
            t_stat, p_val = stats.ttest_ind(dataA, dataB, equal_var=False)
            # Cohen's d calculation using pooled standard deviation:
            stdA, stdB = dataA.std(ddof=1), dataB.std(ddof=1)
            pooled_std = np.sqrt((stdA**2 + stdB**2) / 2)
            cohens_d = (dataA.mean() - dataB.mean()) / pooled_std if pooled_std > 0 else np.nan
            # Percentage change (relative to engine A)
            pct_change = ((dataB.mean() - dataA.mean()) / dataA.mean() * 100) if dataA.mean() != 0 else np.nan
            comp_results.append({
                "Engine A": engA,
                "Engine B": engB,
                "Mean Energy A (J)": dataA.mean(),
                "Mean Energy B (J)": dataB.mean(),
                "Welch t-statistic": t_stat,
                "Welch p-value": p_val,
                "Cohen's d": cohens_d,
                "Percentage Change (%)": pct_change
            })
    return pd.DataFrame(comp_results)

def save_results(results_df, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    results_df.to_csv(output_file, index=False)
    log_message(f"Results saved to {output_file}")

def main():
    log_message("Starting unified energy analysis with iterations.")
    try:
        timestamps_df, energy_df = load_data(TIMESTAMPS_FILE, ENERGY_LOG_FILE)
        iter_results_df = calculate_energy_consumption(timestamps_df, energy_df)
        save_results(iter_results_df, "results/iteration_results.csv")
        
        # Aggregate iteration-level stats per search engine
        summary_df = aggregate_iteration_statistics(iter_results_df)
        save_results(summary_df, "results/summary_iteration_stats.csv")
        
        # Pairwise comparisons between search engines
        pairwise_df = pairwise_comparisons(iter_results_df)
        save_results(pairwise_df, "results/pairwise_comparisons.csv")
        
        log_message("Analysis complete!")
    except FileNotFoundError as e:
        log_message(f"Error: Required file not found - {e}")
    except Exception as e:
        log_message(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
