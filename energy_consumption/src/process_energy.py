import os
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

# File paths
TIMESTAMPS_FILE = "search_engine_results/search_engine_timestamps.csv"
ENERGY_LOG_FILE = "energy_log.csv"
OUTPUT_FILE = "results/final_energy_results.csv"


def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")


def load_data(timestamps_file, energy_file):
    """
    Load the timestamps and energy log data.
    
    Args:
        timestamps_file: Path to timestamps CSV file.
        energy_file: Path to energy log CSV file.
        
    Returns:
        tuple: (timestamps_df, energy_df) data frames
    """
    log_message(f"Loading timestamps from {timestamps_file}")
    timestamps_df = pd.read_csv(timestamps_file)
    
    log_message(f"Loading energy log from {energy_file}")
    energy_df = pd.read_csv(energy_file)
    
    # Convert timestamps to numeric format if needed
    energy_df["Time"] = pd.to_numeric(energy_df["Time"])
    
    return timestamps_df, energy_df


def compute_energy_dell(subframe):
    """
    For Linux-like columns (with cumulative Joules), sum up the difference across
    available RAPL columns. 
    """
    total_energy = 0.0
    energy_cols = ["DRAM_ENERGY (J)", "PACKAGE_ENERGY (J)", 
                   "PP0_ENERGY (J)", "PP1_ENERGY (J)"]
    
    # Add up the difference (last - first) for each energy column found
    for col in energy_cols:
        if col in subframe.columns:
            values = subframe[col].values
            if len(values) > 1:
                total_energy += (values[-1] - values[0])
    return total_energy


def compute_energy_macos(subframe):
    """
    For macOS-like columns (with `SYSTEM_POWER (Watts)`), do numerical integration
    over time (trapz).
    """
    if "SYSTEM_POWER (Watts)" not in subframe.columns:
        return 0.0
    
    # Time in seconds for integration (assuming Time is ms)
    times_s = subframe["Time"].values / 1000.0
    power_w = subframe["SYSTEM_POWER (Watts)"].values
    
    if len(times_s) > 1:
        # Integrate power over time to get Joules
        total_energy_j = np.trapz(power_w, times_s)
        return total_energy_j
    else:
        return 0.0


def compute_energy_for_interval(energy_df, start_time, end_time):
    """
    Given a start and end time, compute total energy based on available columns.
    - If we detect RAPL columns (PACKAGE_ENERGY (J), etc.), we do (last-first).
    - If we detect SYSTEM_POWER (Watts), we do trapz integration.
    """
    # Filter rows for this time interval
    subframe = energy_df[(energy_df["Time"] >= start_time) & 
                         (energy_df["Time"] <= end_time)]
    if subframe.empty:
        return 0.0, 0.0  # (total_energy, average_power) = (0, 0)
    
    # Check if we have RAPL columns
    rapl_cols = [c for c in subframe.columns if "ENERGY (J)" in c]
    has_rapl = len(rapl_cols) > 0
    
    # Check if we have SYSTEM_POWER (Watts)
    has_system_power = "SYSTEM_POWER (Watts)" in subframe.columns
    
    total_energy = 0.0
    average_power = 0.0
    
    if has_rapl:
        # Linux approach
        total_energy = compute_energy_dell(subframe)
        # Average power = total_energy / duration
        duration_s = (end_time - start_time) / 1000.0  # ms -> s
        if duration_s > 0:
            average_power = total_energy / duration_s
    elif has_system_power:
        # macOS approach
        total_energy = compute_energy_macos(subframe)
        # Average power = mean of the power column
        average_power = subframe["SYSTEM_POWER (Watts)"].mean()
    else:
        # No recognized columns
        log_message("Warning: No recognized energy columns found in this subframe.")
    
    return total_energy, average_power

def aggregate_iterations(results_df):
    """
    Aggregate energy metrics by averaging across iterations for each search engine.
    
    Args:
        results_df: DataFrame containing per-iteration results.
    
    Returns:
        DataFrame: Averaged metrics for each search engine.
    """
    log_message("Averaging energy metrics across iterations.")
    
    avg_results_df = results_df.groupby("Search Engine").agg({
        "Total Energy (J)": "mean",
        "Average Power (W)": "mean",
        "Duration (s)": "mean",
        "Energy Delay Product": "mean"
    }).reset_index()

    return avg_results_df


def calculate_energy_consumption(timestamps_df, energy_df):
    """
    Calculate energy consumption per iteration for each search engine.
    
    Args:
        timestamps_df: DataFrame with search engine timestamps (includes "Iteration").
        energy_df: DataFrame with energy log data.
        
    Returns:
        DataFrame: Results with search engines, iterations, and their energy consumption.
    """
    log_message("Calculating energy consumption per iteration.")

    results = []
    
    
    for index, row in timestamps_df.iterrows():
        engine = row["Search Engine"]
        start_time = row["Start Time"]
        end_time = row["End Time"]
        iteration = row["Iteration"]  # NEW: Track iteration
        
        log_message(f"Processing {engine} - Iteration {iteration}: {start_time} to {end_time}")

        # Filter energy data within this timeframe
        engine_energy_df = energy_df[(energy_df["Time"] >= start_time) & 
                                      (energy_df["Time"] <= end_time)]
        
        if engine_energy_df.empty:
            log_message(f"Warning: No energy data found for {engine} - Iteration {iteration}")
            total_energy = 0
            avg_power = 0
            duration_s = 0
            energy_delay_product = 0
        else:
            # Compute total energy (depends on available columns)
            total_energy, avg_power = compute_energy_for_interval(engine_energy_df, start_time, end_time)
            
            # Compute duration (assuming Time is in milliseconds)
            duration_s = (end_time - start_time) / 1000.0  # Convert ms → s
            
            # Compute Energy Delay Product
            energy_delay_product = total_energy * duration_s
        
        results.append({
            "Search Engine": engine,
            "Iteration": iteration,
            "Total Energy (J)": total_energy,
            "Average Power (W)": avg_power,
            "Duration (s)": duration_s,
            "Energy Delay Product": energy_delay_product
        })
    
    return pd.DataFrame(results)


# def store_temperature_data(energy_df):
#     """
#     Store temperature data if available, ensuring we keep only the latest run.
#     """
#     temp_cols = [c for c in energy_df.columns if "CPU_TEMP_" in c]
#     if not temp_cols:
#         return None  # No temperature data

#     # Calculate the average temperature per search engine
#     temperature_data = energy_df.groupby("Search Engine")[temp_cols].mean().reset_index()

#     # Generate a timestamp
#     timestamp = energy_df["Time"].max()
    
#     # Save to file with a timestamp to ensure we get the latest data
#     temp_file = f"results/temperature_data_{timestamp}.csv"
#     save_results(temperature_data, temp_file)
    
#     log_message(f"Saved latest temperature data to {temp_file}")
#     return temp_file



def save_results(results_df, output_file):
    """
    Save processed results to CSV.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    results_df.to_csv(output_file, index=False)
    log_message(f"Final energy results saved to {output_file}")


def perform_shapiro_tests(results_df):
    """
    Perform Shapiro–Wilk test for normality on 'Total Energy (J)' per engine.
    Returns a dict with test stats.
    """
    stats_results = {}
    grouped = results_df.groupby("Search Engine")
    for engine, group in grouped:
        data = group["Total Energy (J)"]
        if len(data) < 3:
            stats_results[engine] = {"error": "Not enough data for Shapiro–Wilk"}
            continue
        try:
            stat, p_val = stats.shapiro(data)
            stats_results[engine] = {
                "Shapiro–Wilk statistic": stat,
                "p-value": p_val
            }
        except Exception as e:
            stats_results[engine] = {"error": str(e)}
    return stats_results


def perform_welch_and_cohens_d(results_df):
    """
    Perform Welch’s t-test & Cohen’s d for each pair of search engines.
    Returns a dict with pairwise results.
    """
    engines = results_df["Search Engine"].unique()
    pairwise_results = {}
    
    for i in range(len(engines)):
        for j in range(i + 1, len(engines)):
            engine_a = engines[i]
            engine_b = engines[j]
            
            data_a = results_df[results_df["Search Engine"] == engine_a]["Total Energy (J)"]
            data_b = results_df[results_df["Search Engine"] == engine_b]["Total Energy (J)"]
            
            # Need at least 2 data points per group
            if len(data_a) < 2 or len(data_b) < 2:
                pairwise_results[f"{engine_a} vs {engine_b}"] = {
                    "error": "Not enough data"
                }
                continue
            
            # Welch’s t-test
            t_stat, p_val = stats.ttest_ind(data_a, data_b, equal_var=False)
            
            # Cohen’s d
            mean_a, mean_b = data_a.mean(), data_b.mean()
            std_a, std_b = data_a.std(ddof=1), data_b.std(ddof=1)
            pooled_std = np.sqrt((std_a**2 + std_b**2) / 2)
            if pooled_std == 0:
                d_val = None
            else:
                d_val = (mean_a - mean_b) / pooled_std
            
            pairwise_results[f"{engine_a} vs {engine_b}"] = {
                "Welch t-statistic": t_stat,
                "p-value": p_val,
                "Cohen's d": d_val
            }
    
    return pairwise_results


if __name__ == "__main__":
    log_message("Starting unified energy analysis with iterations.")

    try:
        # 1. Load data
        timestamps_df, energy_df = load_data(TIMESTAMPS_FILE, ENERGY_LOG_FILE)

        # 2. Calculate per-iteration energy consumption
        iteration_results_df = calculate_energy_consumption(timestamps_df, energy_df)
        
        # store_temperature_data(energy_df)
        
        save_results(iteration_results_df, "results/iteration_results.csv")
        # 3. Aggregate by averaging across iterations
        avg_results_df = aggregate_iterations(iteration_results_df)
        # 4. Save results
        save_results(avg_results_df, OUTPUT_FILE)

        # 5. Perform statistical tests on averaged results
        log_message("Performing statistical tests on averaged search engine results.")
        shapiro_results = perform_shapiro_tests(avg_results_df)
        pairwise_results = perform_welch_and_cohens_d(avg_results_df)

        # 6. Print or log the results
        log_message("---- Shapiro–Wilk Test ----")
        for eng, statsdict in shapiro_results.items():
            log_message(f"{eng}: {statsdict}")

        log_message("---- Welch’s t-test & Cohen’s d ----")
        for pair, statsdict in pairwise_results.items():
            log_message(f"{pair}: {statsdict}")

        log_message("Analysis complete!")

    except FileNotFoundError as e:
        log_message(f"Error: Required file not found - {e}")
    except Exception as e:
        log_message(f"Unexpected error: {e}")