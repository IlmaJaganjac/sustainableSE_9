import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# File path for the enhanced energy results
RESULTS_FILE = "results/final_energy_results.csv"

# def load_temperature_data(latest_energy_file):
#     """
#     Load the temperature data that matches the latest energy results timestamp.
#     """
#     # Read the latest energy results to extract the timestamp
#     if os.path.exists(latest_energy_file):
#         energy_df = pd.read_csv(latest_energy_file)
#         if "" in energy_df.columns:
#             latest_timestamp = energy_df["Run Timestamp"].iloc[0]  # Get the first row's timestamp
#         else:
#             log_message("Run Timestamp column missing from energy results.")
#             return None
#     else:
#         log_message("Latest energy results file not found.")
#         return None

#     # Check if the corresponding temperature file exists
#     temp_file = f"results/temperature_data_{latest_timestamp}.csv"
#     if os.path.exists(temp_file):
#         log_message(f"Loading matching temperature data from {temp_file}")
#         return pd.read_csv(temp_file)
#     else:
#         log_message("No matching temperature data file found.")
#         return None


def log_message(message):
    """Print a timestamped log message."""
    print(f"[{datetime.now()}] {message}")

def load_results(results_file):
    log_message(f"Loading results from {results_file}")
    return pd.read_csv(results_file)

def plot_violin(results_df, metric, title, filename):
    plt.figure(figsize=(10, 6))
    sns.violinplot(x='Search Engine', y=metric, data=results_df, inner='quartile')
    plt.title(title)
    plt.ylabel(metric)
    plt.xlabel("Search Engine")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    log_message(f"Saved violin plot to {filename}")

def plot_box(results_df, metric, title, filename):
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Search Engine', y=metric, data=results_df)
    plt.title(title)
    plt.ylabel(metric)
    plt.xlabel("Search Engine")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    log_message(f"Saved box plot to {filename}")

def plot_histogram_density(results_df, metric, title, filename):
    plt.figure(figsize=(10, 6))
    sns.histplot(data=results_df, x=metric, hue='Search Engine', kde=True, element="step")
    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    log_message(f"Saved histogram/density plot to {filename}")

def plot_scatter(results_df, x_metric, y_metric, title, filename):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=results_df, x=x_metric, y=y_metric, hue='Search Engine', s=100)
    plt.title(title)
    plt.xlabel(x_metric)
    plt.ylabel(y_metric)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    log_message(f"Saved scatter plot to {filename}")

def main():
    # Load the aggregated energy results
    results_df = load_results(RESULTS_FILE)
    
    # Create a directory for plots if it doesn't exist
    plots_dir = "plots"
    os.makedirs(plots_dir, exist_ok=True)
    
    # Total Energy Plots
    plot_violin(
        results_df, 
        metric="Total Energy (J)", 
        title="Violin Plot: Total Energy Consumption per Search Engine",
        filename=os.path.join(plots_dir, "violin_total_energy.png")
    )
    plot_box(
        results_df, 
        metric="Total Energy (J)", 
        title="Box Plot: Total Energy Consumption per Search Engine",
        filename=os.path.join(plots_dir, "box_total_energy.png")
    )
    plot_histogram_density(
        results_df, 
        metric="Total Energy (J)", 
        title="Histogram & Density: Total Energy Consumption",
        filename=os.path.join(plots_dir, "hist_density_total_energy.png")
    )
    
    # Average Power Plots
    plot_violin(
        results_df, 
        metric="Average Power (W)", 
        title="Violin Plot: Average Power per Search Engine",
        filename=os.path.join(plots_dir, "violin_average_power.png")
    )
    plot_box(
        results_df, 
        metric="Average Power (W)", 
        title="Box Plot: Average Power per Search Engine",
        filename=os.path.join(plots_dir, "box_average_power.png")
    )
    plot_histogram_density(
        results_df, 
        metric="Average Power (W)", 
        title="Histogram & Density: Average Power",
        filename=os.path.join(plots_dir, "hist_density_average_power.png")
    )
    
    # Energy Delay Product Plots
    plot_violin(
        results_df, 
        metric="Energy Delay Product", 
        title="Violin Plot: Energy Delay Product per Search Engine",
        filename=os.path.join(plots_dir, "violin_energy_delay_product.png")
    )
    plot_box(
        results_df, 
        metric="Energy Delay Product", 
        title="Box Plot: Energy Delay Product per Search Engine",
        filename=os.path.join(plots_dir, "box_energy_delay_product.png")
    )
    plot_histogram_density(
        results_df, 
        metric="Energy Delay Product", 
        title="Histogram & Density: Energy Delay Product",
        filename=os.path.join(plots_dir, "hist_density_energy_delay_product.png")
    )
    
    # Scatter Plot: Total Energy vs. Average Power
    plot_scatter(
        results_df,
        x_metric="Total Energy (J)",
        y_metric="Average Power (W)",
        title="Scatter Plot: Total Energy vs. Average Power",
        filename=os.path.join(plots_dir, "scatter_total_energy_vs_average_power.png")
    )
    
    log_message("All plots have been generated and saved.")

if __name__ == "__main__":
    main()
