import os
import ast
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

FINAL_ENERGY_FILE = "results/final_energy_results.csv"
SAVE_FIG_DIR = "results/plots"

def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")

def ensure_dir(path):
    """Ensure the directory exists."""
    os.makedirs(path, exist_ok=True)

def plot_edp_boxplots(df, save_dir):
    """
    Create separate boxplots for each Energy Delay Product (w=1, w=2, w=3)
    with proper handling of missing or invalid values.
    """
    for w_col, w_label in zip(["EDP_w1", "EDP_w2", "EDP_w3"], ["w=1", "w=2", "w=3"]):
        # Skip if column not in dataframe or all values are None/NaN
        if w_col not in df.columns or df[w_col].isna().all():
            log_message(f"Skipping {w_label} plot as no valid data is available")
            continue
        
        # Create a copy of the dataframe with only valid values for this metric
        plot_df = df.dropna(subset=[w_col]).copy()
        
        # Skip if no data after filtering
        if plot_df.empty:
            log_message(f"No valid data for {w_label} plot after filtering NaNs")
            continue
            
        # Check if we have enough data for each search engine
        engine_counts = plot_df.groupby("Search Engine").size()
        valid_engines = engine_counts[engine_counts > 0].index.tolist()
        
        if not valid_engines:
            log_message(f"No search engines with valid data for {w_label}")
            continue
            
        # Filter to include only search engines with data
        plot_df = plot_df[plot_df["Search Engine"].isin(valid_engines)]
        
        plt.figure(figsize=(12, 5))
        try:
            # Create the boxplot with filtered data
            sns.boxplot(data=plot_df, x="Search Engine", y=w_col)
            plt.title(f"Energy Delay Product ({w_label}) per Search Engine")
            plt.ylabel("EDP")
            plt.tight_layout()
            plt.savefig(os.path.join(save_dir, f"boxplot_edp_{w_label}.png"))
            plt.close()
            log_message(f"Created boxplot for EDP {w_label}")
        except Exception as e:
            log_message(f"Error creating boxplot for {w_label}: {str(e)}")
            plt.close()  # Make sure to close the figure even if plotting fails

def plot_power_across_iterations(sample_df, output_path="results/plots/power_across_iterations.png"):
    """
    Plots average power (W) vs. time offset (s) for each search engine.
    - The time offset is computed per iteration: (Time - Start_Time)/1000.
    - We then group by [Search Engine, time_offset] to average across all iterations.
    - Finally, we plot one line per search engine with hue="Search Engine".
    """
    # Ensure we have the necessary columns
    required_columns = {"Search Engine", "Iteration", "Time", "Start_Time", "Power (W)"}
    if not required_columns.issubset(sample_df.columns):
        missing = required_columns - set(sample_df.columns)
        log_message(f"Sample DataFrame missing required columns for power plot: {missing}")
        return
    
    # Filter out rows with missing values in required columns
    sample_df = sample_df.dropna(subset=list(required_columns))
    
    if sample_df.empty:
        log_message("No valid data remaining after filtering missing values")
        return
    
    try:
        # 1) Compute time offset in seconds
        sample_df = sample_df.copy()
        sample_df["Time_s"] = (sample_df["Time"] - sample_df["Start_Time"]) / 1000.0
        
        # 2) Group by [Search Engine, Time_s] to average the power across all iterations
        grouped = sample_df.groupby(["Search Engine", "Time_s"], as_index=False)["Power (W)"].mean()
        
        # 3) Plot with Seaborn lineplot, hue="Search Engine"
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=grouped, x="Time_s", y="Power (W)", hue="Search Engine", marker="o")
        plt.title("Average Power Over Time (s) by Search Engine")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Power (W)")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        log_message(f"Saved power vs. time plot to {output_path}")
    except Exception as e:
        log_message(f"Error plotting power across iterations: {str(e)}")
        plt.close()

def main():
    ensure_dir(SAVE_FIG_DIR)
    
    # 1) Read the final energy results
    try:
        df = pd.read_csv(FINAL_ENERGY_FILE)
        log_message(f"Loaded data from {FINAL_ENERGY_FILE}, {len(df)} rows")
    except Exception as e:
        log_message(f"Error loading data: {str(e)}")
        return
    
    # Parse the "Energy Delay Product" column (which is a list string like "[123.4, 567.8, 9012.3]")
    edp_w1, edp_w2, edp_w3 = [], [], []
    for edp_str in df["Energy Delay Product"]:
        try:
            edp_list = ast.literal_eval(str(edp_str))
            edp_w1.append(edp_list[0] if len(edp_list) > 0 else None)
            edp_w2.append(edp_list[1] if len(edp_list) > 1 else None)
            edp_w3.append(edp_list[2] if len(edp_list) > 2 else None)
        except:
            edp_w1.append(None)
            edp_w2.append(None)
            edp_w3.append(None)
    
    df["EDP_w1"] = edp_w1
    df["EDP_w2"] = edp_w2
    df["EDP_w3"] = edp_w3
    
    # ----------------------------------------------------------------
    # 1) BOX PLOT FOR EDP (w=1, w=2, w=3) IN SEPARATE FIGURES
    log_message("Creating EDP boxplots...")
    plot_edp_boxplots(df, SAVE_FIG_DIR)
    
    # ----------------------------------------------------------------
    # 2) VIOLIN PLOT OF TOTAL ENERGY (J) PER SEARCH ENGINE (ALL ITERATIONS COMBINED)
    log_message("Creating total energy violin plot...")
    try:
        plt.figure(figsize=(22, 5))
        sns.violinplot(data=df, x="Search Engine", y="Total Energy (J)", inner="box")
        plt.title("Total Energy (J) per Search Engine")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_FIG_DIR, "violin_total_energy.png"))
        plt.close()
    except Exception as e:
        log_message(f"Error creating total energy violin plot: {str(e)}")
        plt.close()
    
    # ----------------------------------------------------------------
    # 3) VIOLIN PLOT FOR AVERAGE POWER (W) PER SEARCH ENGINE (ALL ITERATIONS COMBINED)
    log_message("Creating average power violin plot...")
    try:
        plt.figure(figsize=(22, 5))
        sns.violinplot(data=df, x="Search Engine", y="Average Power (W)", inner="box")
        plt.title("Average Power (W) per Search Engine\n")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_FIG_DIR, "violin_avg_power.png"))
        plt.close()
    except Exception as e:
        log_message(f"Error creating average power violin plot: {str(e)}")
        plt.close()
    
    # ----------------------------------------------------------------
    # 4) HISTOGRAM OF THE AVERAGE TOTAL ENERGY OVER ALL ITERATIONS PER SEARCH ENGINE
    log_message("Creating average total energy histogram...")
    try:
        avg_energy_df = df.groupby("Search Engine", as_index=False)["Total Energy (J)"].mean()
        plt.figure(figsize=(14, 5))
        engines = avg_energy_df["Search Engine"].unique()
        colors = sns.color_palette("husl", len(engines))
        for engine, color in zip(engines, colors):
            engine_df = avg_energy_df[avg_energy_df["Search Engine"] == engine]
            plt.bar(engine_df["Search Engine"], engine_df["Total Energy (J)"], color=color, label=engine)
        plt.legend(frameon=True, title="Search Engine", bbox_to_anchor=(1.0, 1), loc="upper left")
        plt.title("Average Total Energy (J) per Search Engine")
        plt.ylabel("Avg Total Energy (J)")
        plt.xlabel("Search Engine")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_FIG_DIR, "hist_avg_total_energy.png"))
        plt.close()
    except Exception as e:
        log_message(f"Error creating average total energy histogram: {str(e)}")
        plt.close()

    # ----------------------------------------------------------------
    # 5) POWER ACROSS ITERATIONS
    log_message("Creating power across iterations plot...")
    try:
        sample_file = "results/final_energy_samples.csv"
        if os.path.exists(sample_file):
            sample_df = pd.read_csv(sample_file)
            plot_power_across_iterations(sample_df, output_path=os.path.join(SAVE_FIG_DIR, "aggregated_metrics.png"))
        else:
            log_message(f"Sample file not found: {sample_file}")
    except Exception as e:
        log_message(f"Error creating power across iterations plot: {str(e)}")
    
    log_message(f"Plots saved in: {SAVE_FIG_DIR}")

if __name__ == "__main__":
    main()