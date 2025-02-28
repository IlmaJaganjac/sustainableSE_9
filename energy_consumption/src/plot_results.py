import os
import ast
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

FINAL_ENERGY_FILE = "results/final_energy_results.csv"
SAVE_FIG_DIR = "results/plots"
TIMESTAMPS_FILE = "search_engine_results/search_engine_timestamps.csv"

def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")

def ensure_dir(path):
    """Ensure the directory exists."""
    os.makedirs(path, exist_ok=True)
    
def plot_power_across_iterations(sample_df, output_path_power="results/plots/power_across_iterations.png", output_path_memory="results/plots/memory_across_iterations.png"):
    """
    Plots average power (W) and used memory vs. time offset (s) for each search engine,
    averaged across all iterations.
    """
    # Check for required columns
    required_columns = {"Search Engine", "Iteration", "Time", "Start_Time", "Power (W)", "USED_MEMORY"}
    if not required_columns.issubset(sample_df.columns):
        print("Sample DataFrame missing required columns for plots.")
        return
    
    # 1) Remove NaNs and negative values
    sample_df = sample_df.dropna(subset=["Power (W)", "USED_MEMORY"])
    sample_df = sample_df[sample_df["Power (W)"] >= 0].copy()

    # 2) Compute time offset in seconds
    sample_df["Time_s"] = (sample_df["Time"] - sample_df["Start_Time"]) / 1000.0

    # 3) (Optional) Bin the time offset if slight variations exist across iterations.
    sample_df["Time_s_binned"] = sample_df["Time_s"].round(1)
    
    # 4) Group by Search Engine and binned time offset to average across all iterations for power
    grouped_power = sample_df.groupby(["Search Engine", "Time_s_binned"], as_index=False).agg({
        "Power (W)": "mean",
        "Time_s": "mean"
    })
    
    # 5) Remove any time offsets beyond 40 seconds for power plot
    grouped_power = grouped_power[grouped_power["Time_s"] <= 40]
    
    # 6) Plot power with Seaborn
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=grouped_power, x="Time_s", y="Power (W)", hue="Search Engine", marker="o")
    plt.title("Average Power Over Time (s) by Search Engine")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Power (W)")
    plt.tight_layout()
    plt.savefig(output_path_power)
    plt.close()
    
    print(f"Saved power vs. time plot to {output_path_power}")

    # 7) Group by Search Engine and binned time offset to average across all iterations for memory
    grouped_memory = sample_df[sample_df["Time_s"] <= 40].groupby(["Search Engine", "Time_s_binned"], as_index=False).agg({
        "USED_MEMORY": "mean",
        "Time_s": "mean"
    })
    
    # 8) Plot memory with Seaborn
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=grouped_memory, x="Time_s", y="USED_MEMORY", hue="Search Engine", marker="o")
    plt.title("Average Used Memory Over Time (s) by Search Engine")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Used Memory")
    plt.tight_layout()
    plt.savefig(output_path_memory)
    plt.close()
    
    print(f"Saved memory vs. time plot to {output_path_memory}")

def plot_avg_duration(df, output_path="results/plots/barplot_avg_duration.png"):
    """
    Plots the average duration (s) per search engine, averaged over all iterations.
    """
    # Ensure the DataFrame has the necessary column
    required_columns = {"Search Engine", "Duration (s)"}
    if not required_columns.issubset(df.columns):
        print("DataFrame missing required columns for duration plot.")
        return

    # Group by "Search Engine" and compute the mean of "Duration (s)"
    avg_duration_df = df.groupby("Search Engine", as_index=False)["Duration (s)"].mean()
    
    # Plot using Seaborn's barplot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=avg_duration_df, x="Search Engine", y="Duration (s)")
    plt.title("Average Duration (s) per Search Engine")
    plt.xlabel("Search Engine")
    plt.ylabel("Average Duration (s)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    print(f"Saved average duration plot to {output_path}")

def plot_response_time_vs_energy(df, output_path="results/plots/correlation_response_time_energy.png"):
    """
    Creates a correlation plot showing the relationship between response time (Duration (s))
    and energy consumption metrics (Total Energy (J) and Average Power (W)) for each search engine.
    This plot helps to illustrate how response time affects energy usage and to highlight which
    search engine is most energy efficient.
    """
    df = df[df["Duration (s)"] <= 40]
    required_columns = {"Search Engine", "Duration (s)", "Total Energy (J)", "Average Power (W)"}
    if not required_columns.issubset(df.columns):
        print("DataFrame missing required columns for correlation plot.")
        return

    sns.set(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    engines = df["Search Engine"].unique()
    palette = sns.color_palette("husl", n_colors=len(engines))

    # Left subplot: Response Time vs Total Energy (J)
    ax = axes[0]
    for engine, color in zip(engines, palette):
        engine_df = df[df["Search Engine"] == engine]
        ax.scatter(engine_df["Duration (s)"], engine_df["Total Energy (J)"],
                   color=color, label=engine, alpha=0.7)
        # Plot a regression line for this engine's data
        sns.regplot(x="Duration (s)", y="Total Energy (J)",
                    data=engine_df, scatter=False, ax=ax,
                    color=color, ci=None)
    ax.set_title("Response Time vs Total Energy (J)")
    ax.set_xlabel("Duration (s) [Response Time]")
    ax.set_ylabel("Total Energy (J)")
    ax.legend(title="Search Engine")

    # Right subplot: Response Time vs Average Power (W)
    ax = axes[1]
    for engine, color in zip(engines, palette):
        engine_df = df[df["Search Engine"] == engine]
        ax.scatter(engine_df["Duration (s)"], engine_df["Average Power (W)"],
                   color=color, label=engine, alpha=0.7)
        # Plot a regression line for this engine's data
        sns.regplot(x="Duration (s)", y="Average Power (W)",
                    data=engine_df, scatter=False, ax=ax,
                    color=color, ci=None)
    ax.set_title("Response Time vs Average Power (W)")
    ax.set_xlabel("Duration (s) [Response Time]")
    ax.set_ylabel("Average Power (W)")
    ax.legend(title="Search Engine")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved correlation plot to {output_path}")

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def plot_percentage_changes(df_pct, output_path="results/plots/percentage_changes.png"):
    """
    Plots a grouped bar chart showing percentage change in various metrics per search engine.
    Expected columns in df_pct: 'Search Engine', 'Metric', 'Percentage Change'
    """
    plt.figure(figsize=(12, 7))
    sns.barplot(data=df_pct, x="Search Engine", y="Percentage Change", hue="Metric")
    plt.title("Percentage Change in Performance Metrics per Search Engine")
    plt.xlabel("Search Engine")
    plt.ylabel("Percentage Change (%)")
    plt.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Saved percentage change plot to {output_path}")

def plot_pairwise_comparison_heatmaps(df, value_col="Percentage Change (%)", output_dir="results/plots/"):
    """
    Creates heatmaps for each unique metric comparing all engines.
    
    Parameters:
      - df: DataFrame with pairwise comparison data containing columns:
          ['Metric', 'Engine A', 'Engine B', 'Mean A', 'Mean B', 'Test Used',
           'Statistic', 'p-value', 'Effect Size (non normal)', 'Percentage Change (%)']
      - value_col: Column name to display in the heatmap cells (default: "Percentage Change (%)").
      - output_dir: Directory to save the heatmap images.
      
    For each unique metric, this function:
      1. Filters the data.
      2. Pivots the DataFrame so that rows are Engine A and columns are Engine B.
      3. Creates a heatmap with annotations.
    """
  
    metrics = df["Metric"].unique()
    for metric in metrics:
        df_metric = df[df["Metric"] == metric]
        # Pivot the data: rows = Engine A, columns = Engine B, values = the selected metric (e.g. percentage change)
        heatmap_data = df_metric.pivot(index="Engine A", columns="Engine B", values=value_col)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(heatmap_data, annot=True, cmap="coolwarm", center=0, fmt=".1f")
        plt.title(f"{metric} - {value_col} Comparison")
        plt.xlabel("Engine B")
        plt.ylabel("Engine A")
        plt.tight_layout()
        
        output_path = os.path.join(output_dir, f"heatmap_{metric.replace(' ', '_')}.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Saved heatmap for {metric} to {output_path}")

def plot_selenium_energy(df):
    """
    Plots bar charts showing the percentage of baseline overhead compared to raw duration
    and the percentage of actual query time compared to raw duration for each search engine.
    """
    df["Baseline Overhead (%)"] = df["Baseline Overhead (ms)"] / df["Raw Duration (ms)"] * 100
    df["Actual Query Time (%)"] = (df["Raw Duration (ms)"]-df["Baseline Overhead (ms)"]) / df["Raw Duration (ms)"] * 100 + df["Baseline Overhead (%)"]
    
    avg_overhead_df = df.groupby("Search Engine", as_index=False)[["Baseline Overhead (%)", "Actual Query Time (%)"]].mean()
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=avg_overhead_df, x="Search Engine", y="Baseline Overhead (%)", label="Baseline Overhead")
    sns.barplot(data=avg_overhead_df, x="Search Engine", y="Actual Query Time (%)", label="Actual Query Time", alpha=0.4)
    
    plt.title("Selenium Overhead and Actual Query Time Percentage")
    plt.ylabel("Percentage of Raw Duration (%)")
    plt.legend(title="Metric")
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_FIG_DIR, "barplot_selenium_metrics.png"))
    plt.close()

def main():
    ensure_dir(SAVE_FIG_DIR)
    
    # 1) Read the final energy results
    df = pd.read_csv(FINAL_ENERGY_FILE)

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
    # 3) BAR PLOT OF AVERAGE TEMPERATURE (Celcius) PER SEARCH ENGINE (ALL ITERATIONS COMBINED)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df.groupby("Search Engine", as_index=False)["Temperature"].mean(), x="Search Engine", y="Temperature")
    plt.title("Average Temperature (Celcius) per Search Engine")
    plt.ylabel("Temperature (Celcius)")
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_FIG_DIR, "barplot_avg_temp.png"))
    plt.close()
    # ----------------------------------------------------------------
    # 1) BOX PLOT FOR EDP (w=1, w=2, w=3) IN SEPARATE FIGURES
    #    Combine all iterations for each search engine 
    for w_col, w_label in zip(["EDP_w1", "EDP_w2", "EDP_w3"], ["w=1", "w=2", "w=3"]):
        plt.figure(figsize=(12, 5))
        sns.boxplot(data=df, x="Search Engine", y=w_col)
        plt.title(f"Energy Delay Product ({w_label}) per Search Engine")
        plt.ylabel("EDP")
        plt.tight_layout()
        plt.savefig(os.path.join(SAVE_FIG_DIR, f"boxplot_edp_{w_label}.png"))
        plt.close()
    
    # ----------------------------------------------------------------
    # 2) VIOLIN PLOT OF TOTAL ENERGY (J) PER SEARCH ENGINE (ALL ITERATIONS COMBINED)
    plt.figure(figsize=(22, 5))
    sns.violinplot(data=df, x="Search Engine", y="Total Energy (J)", inner="box")
    plt.title("Total Energy (J) per Search Engine")
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_FIG_DIR, "violin_total_energy.png"))
    plt.close()
    
    # ----------------------------------------------------------------
    # 3) VIOLIN PLOT FOR AVERAGE POWER (W) PER SEARCH ENGINE (ALL ITERATIONS COMBINED)
    plt.figure(figsize=(22, 5))
    sns.violinplot(data=df, x="Search Engine", y="Average Power (W)", inner="box")
    plt.title("Average Power (W) per Search Engine\n")
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_FIG_DIR, "violin_avg_power.png"))
    plt.close()
    
    # ----------------------------------------------------------------
    # 4) HISTOGRAM OF THE AVERAGE TOTAL ENERGY OVER ALL ITERATIONS PER SEARCH ENGINE
    #    We'll group by search engine, compute the mean total energy, and plot a bar chart.
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

    sample_df = pd.read_csv("results/final_energy_samples.csv")
    
    plot_avg_duration(df, output_path=os.path.join(SAVE_FIG_DIR, "barplot_avg_duration.png"))

    plot_response_time_vs_energy(df, output_path=os.path.join(SAVE_FIG_DIR, "correlation_response_time_energy.png"))
    
    efficiency_df = df.groupby("Search Engine", as_index=False)["Average Power (W)"].mean().sort_values("Average Power (W)")
    print("Average Power (W) per Search Engine:")
    print(efficiency_df)
    best_engine = efficiency_df.iloc[0]
    print(f"\nConclusion: The most energy efficient search engine is '{best_engine['Search Engine']}' "
          f"with an average power consumption of {best_engine['Average Power (W)']:.2f} W.")
    

    plot_power_across_iterations(sample_df, output_path_power="results/plots/aggregated_metrics.png", )
    log_message(f"Plots saved in: {SAVE_FIG_DIR}")


    df_comparision = pd.read_csv("results/pairwise_comparisons.csv")
    plot_pairwise_comparison_heatmaps(df_comparision)

    df = pd.read_csv(TIMESTAMPS_FILE)
    plot_selenium_energy(df)
    
if __name__ == "__main__":
    main()
