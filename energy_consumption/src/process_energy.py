import os
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
import sys
import re
import matplotlib.pyplot as plt

# File paths
TIMESTAMPS_FILE = "search_engine_results/search_engine_timestamps.csv"
ENERGY_LOG_FILE = "energy_log.csv"
OUTPUT_FILE = "results/final_energy_results.csv"
PAIRWISE_RESULTS_FILE = "results/pairwise_comparisons.csv"
STAT_TEST_FILE = "results/statistical_tests.csv"



BUFFER = int(os.getenv("INTERVAL", 200))  # Default to 200 if not set

W = [1,2,3]

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

def compute_energy_for_interval(subframe, key="PACKAGE_ENERGY (W)"):
    avg_temp = None
    if "CPU_ENERGY (J)" in subframe.columns:
            key = "CPU_ENERGY (J)"
    if "PACKAGE_ENERGY (J)" in subframe.columns:
            key = "PACKAGE_ENERGY (J)"
    if "SYSTEM_POWER (Watts)" in subframe.columns:
            key = "SYSTEM_POWER (Watts)"
    data = subframe[key].copy().to_list()

    if key != "CPU_POWER (Watts)" and key != "SYSTEM_POWER (Watts)":
        subframe = subframe.copy()
        subframe.loc[:, key + "_original"] = subframe[key].copy()


        for i in range(1, len(subframe)):
            # Power is delta energy / delta time
            delta_e = subframe[key].iloc[i] - subframe[key].iloc[i - 1]
            delta_t = subframe["Delta"].iloc[i]
            if not np.isnan(delta_t) and delta_t > 0:
                subframe.loc[subframe.index[i], "Power (W)"] = (delta_e * 1000) / delta_t
            else:
                subframe.loc[subframe.index[i], "Power (W)"] = 0

    if key == "SYSTEM_POWER (Watts)":
        all_temps = subframe[['CPU_TEMP_0','CPU_TEMP_1','CPU_TEMP_2','CPU_TEMP_3',
                           'CPU_TEMP_4','CPU_TEMP_5','CPU_TEMP_6','CPU_TEMP_7',
                           'CPU_TEMP_8','CPU_TEMP_9']]
        avg_temp = all_temps.mean(axis=0).mean()

        times_s = subframe["Time"].values / 1000.0
        total_energy = np.trapz(data, times_s)  if len(times_s) > 1 else 0.0
    if key == "PACKAGE_ENERGY (J)":
        total_energy = subframe[key].iloc[-1] - subframe[key].iloc[0]
    print(f"Total energy: {total_energy}")
    avg_power = subframe["Power (W)"].mean()
    print(f"Average power: {avg_power}") 
    if key == "SYSTEM_POWER (Watts)":
        return total_energy, avg_power, avg_temp, data
    return total_energy, avg_power, avg_temp, subframe

def calculate_energy_consumption(timestamps_df, energy_df):
    log_message("Calculating energy consumption per iteration.")
    results = []
    sample_rows = []

    for idx, row in timestamps_df.iterrows():
        engine = row["Search Engine"]
        normalized_duration = row["Normalized Duration (ms)"]
        # if query took 2 seconds more than the baseline remove this overhead probably due to selenium.
        start_time = row["Start Time"] + row['Baseline Overhead (ms)'] if normalized_duration > 2000 else row["Start Time"]
        end_time = row["End Time"]
        iteration = row["Iteration"]
        log_message(f"Processing {engine} - Iteration {iteration}: {start_time} to {end_time}")
        buffer_ms = BUFFER
        
        iter_df = energy_df[(energy_df["Time"] >= (start_time - buffer_ms)) &
                         (energy_df["Time"] <= (end_time + buffer_ms))]
        
        if iter_df.empty:
            log_message(f"Warning: No energy data for {engine} Iteration {iteration}")
            res = {"Search Engine": engine, "Iteration": iteration,
                   "Total Energy (J)": 0, "Average Power (W)": 0, "Duration (s)": 0,
                   "Energy Delay Product": 0
                   }
        else:
            energy_val, avg_power, avg_temp, sample_data = compute_energy_for_interval(iter_df)
            duration_s = (end_time - start_time) / 1000.0
            
            # edp = energy_val * (duration_s ** w)
            # the exponent w denotes weights, and it can take the following values:
            #  1 for energy efficiency when energy is of major concern;
            #  2 for balanced, when both energy consumption and performance are important;
            #  3 for performance efficiency,
            edp1, edp2, edp3 = (energy_val * duration_s ** w for w in W)

            res = {"Search Engine": engine, "Iteration": iteration,
                   "Total Energy (J)": energy_val,
                   "Average Power (W)": avg_power,
                   "Duration (s)": duration_s,
                   "Energy Delay Product": [edp1, edp2, edp3],
                   "Temperature": avg_temp
                   }

        for i, r in sample_data.iterrows():
                    sample_row = {
                        "Search Engine": engine,
                        "Iteration": iteration,
                        "Time": r["Time"],             
                        "Start_Time": start_time,      
                        "Power (W)": r.get("Power (W)", None),
                    }
                    # If CPU usage, memory, or temperature columns exist, add them
                    if "CPU_USAGE" in r:
                        sample_row["CPU_USAGE"] = r["CPU_USAGE"]
                    for col in r.index:
                        if "CPU_TEMP" in col:
                            sample_row[col] = r[col]
                    if "USED_MEMORY" in r and "TOTAL_MEMORY" in r:
                        sample_row["USED_MEMORY"] = r["USED_MEMORY"]
                        sample_row["TOTAL_MEMORY"] = r["TOTAL_MEMORY"]
                    
                    sample_rows.append(sample_row)
    
        results.append(res)
    iter_results_df = pd.DataFrame(results)
    sample_results_df = pd.DataFrame(sample_rows)
    
    return iter_results_df, sample_results_df

def statistical_tests(results_df):
    """
    For each search engine's 'Total Energy (J)' and 'Average Power (W)' values,
    perform a Shapiro–Wilk test for normality. If a group's p-value is below 0.05,
    remove outliers (using a z-score filter) and retest.
    
    Prints the initial and filtered test statistics and p-values.
    
    Returns:
      - normality_details: dict keyed by metric, where each value is a dict mapping
        each search engine to a dictionary with keys:
           'initial_stat', 'initial_p', 'filtered_stat' (if applied), 'filtered_p' (if applied),
           and 'is_normal' (boolean, or None if not enough data).
      - overall_normal: dict keyed by metric with an overall flag (True if all groups are normal, False otherwise).
    """
    import numpy as np
    from scipy import stats
    
    normality_details = {}
    overall_normal = {}
    metrics = ["Total Energy (J)", "Average Power (W)"]
    log_message("Performing Shapiro-Wilk tests for normality...")
    for metric in metrics:
        metric_details = {}
        all_normal = True
        for engine in results_df["Search Engine"].unique():
            values = results_df[results_df["Search Engine"] == engine][metric].dropna().values
            # print(f"{engine} - {metric}: {len(values)} values {values}") 
            detail = {}
            if len(values) < 3:
                detail["initial_stat"] = None
                detail["initial_p"] = None
                detail["filtered_stat"] = None
                detail["filtered_p"] = None
                detail["is_normal"] = None  # Not enough data to assess normality
                metric_details[engine] = detail
                continue
            
            # Perform initial Shapiro–Wilk test
            stat, p = stats.shapiro(values)
            detail["initial_stat"] = stat
            detail["initial_p"] = p
            log_message(f"{engine} - {metric} (initial): stat={stat:.4f}, p={p:.4f}")
            
            if p < 0.05:
                # Remove outliers and retest
                filtered_values = remove_outliers_zscore(values)
                if len(filtered_values) < 3:
                    detail["filtered_stat"] = None
                    detail["filtered_p"] = None
                    detail["is_normal"] = False
                    all_normal = False
                    log_message(f"{engine} - {metric}: Not enough data after outlier removal.")
                else:
                    stat2, p2 = stats.shapiro(filtered_values)
                    detail["filtered_stat"] = stat2
                    detail["filtered_p"] = p2
                    log_message(f"{engine} - {metric} (filtered): stat={stat2:.4f}, p={p2:.4f}")
                    if p2 < 0.05:
                        detail["is_normal"] = False
                        all_normal = False
                        log_message(f"{engine} - {metric}: Data is non-normal even after outlier removal.")
                    else:
                        detail["is_normal"] = True
                        log_message(f"{engine} - {metric}: Data is normal after outlier removal.")
            else:
                detail["filtered_stat"] = None
                detail["filtered_p"] = None
                detail["is_normal"] = True
                log_message(f"{engine} - {metric}: Data is normal.")
            metric_details[engine] = detail
        normality_details[metric] = metric_details
        overall_normal[metric] = all_normal
    return normality_details, overall_normal

def pairwise_comparisons_metric(results_df, metric, is_normal=True):
    """
    For each pair of search engines, perform a pairwise statistical test on the given metric.
    
    If is_normal is True, use Welch's t-test and compute Cohen's d as effect size.
    Otherwise, use the Mann–Whitney U test and compute an effect size based on rank-biserial correlation.
    
    Returns:
      A DataFrame containing the pairwise comparison results for the specified metric.
    """
    engines = results_df["Search Engine"].unique()
    comp_results = []
    
    for i in range(len(engines)):
        for j in range(i+1, len(engines)):
            engA = engines[i]
            engB = engines[j]
            dataA = results_df[results_df["Search Engine"] == engA][metric].dropna()
            dataB = results_df[results_df["Search Engine"] == engB][metric].dropna()
            if len(dataA) < 2 or len(dataB) < 2:
                continue
            
            if is_normal:
                # Welch's t-test
                t_stat, p_val = stats.ttest_ind(dataA, dataB, equal_var=False)
                test_used = "Welch t-test"
                # Cohen's d using pooled standard deviation
                stdA, stdB = dataA.std(ddof=1), dataB.std(ddof=1)
                pooled_std = np.sqrt((stdA**2 + stdB**2) / 2)
                cohens_d = (dataA.mean() - dataB.mean()) / pooled_std if pooled_std > 0 else np.nan
                effect_size = cohens_d
            else:
                # Mann-Whitney U test
                u_stat, p_val = stats.mannwhitneyu(dataA, dataB, alternative='two-sided')
                test_used = "Mann-Whitney U"
                # Common effect size as in lectures:
                n1, n2 = len(dataA), len(dataB)
                effect_size = u_stat / (n1 * n2)
            
            pct_change = ((dataB.mean() - dataA.mean()) / dataA.mean() * 100) if dataA.mean() != 0 else np.nan
            
            comp_results.append({
                "Metric": metric,
                "Engine A": engA,
                "Engine B": engB,
                "Mean A": dataA.mean(),
                "Mean B": dataB.mean(),
                "Test Used": test_used,
                "Statistic": t_stat if is_normal else u_stat,
                "p-value": p_val,
                "Effect Size (Cohen's d)" if is_normal else "Effect Size (non normal)": effect_size,
                "Percentage Change (%)": pct_change
            })
    
    # For consistent column naming, we rename the effect size field:
    comp_df = pd.DataFrame(comp_results)
    if is_normal:
        comp_df = comp_df.rename(columns={"Effect Size (Cohen's d)": "Effect Size"})
    else:
        comp_df = comp_df.rename(columns={"Effect Size (Rank-Biserial)": "Effect Size"})
    
    return comp_df

def save_results(results_df, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    results_df.to_csv(output_file, index=False)
    log_message(f"Results saved to {output_file}")

def main():
    log_message("Starting energy analysis with iterations.")
    try:
        timestamps_df, energy_df = load_data(TIMESTAMPS_FILE, ENERGY_LOG_FILE)
        iter_results_df, sample_results_df = calculate_energy_consumption(timestamps_df, energy_df)
        save_results(iter_results_df, OUTPUT_FILE)

        sample_file = "results/final_energy_samples.csv"
        save_results(sample_results_df, sample_file)


        normality_details, overall_normal = statistical_tests(iter_results_df)
        
        norm_rows = []
        for metric, engine_details in normality_details.items():
            for engine, details in engine_details.items():
                norm_rows.append({
                    "Metric": metric,
                    "Search Engine": engine,
                    "Initial Stat": details["initial_stat"],
                    "Initial p-value": details["initial_p"],
                    "Filtered Stat": details["filtered_stat"],
                    "Filtered p-value": details["filtered_p"],
                    "Is Normal": details["is_normal"]
                })
        norm_df = pd.DataFrame(norm_rows)
        save_results(norm_df, STAT_TEST_FILE)

        pairwise_energy = pairwise_comparisons_metric(iter_results_df, "Total Energy (J)", is_normal=overall_normal["Total Energy (J)"])
        pairwise_power = pairwise_comparisons_metric(iter_results_df, "Average Power (W)", is_normal=overall_normal["Average Power (W)"])

        combined_pairwise = pd.concat([pairwise_energy, pairwise_power], ignore_index=True)
        save_results(combined_pairwise, PAIRWISE_RESULTS_FILE)

        log_message("Analysis complete!")
        
    except FileNotFoundError as e:
        log_message(f"Error: Required file not found - {e}")
    except Exception as e:
        log_message(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
