import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# File paths
RESULTS_FILE = "results/final_energy_results.csv"
OUTPUT_PLOT = "plots/energy_consumption_plot.png"


def log_message(message):
    print(f"[{datetime.now()}] {message}")


def load_results(results_file):
    log_message(f"Loading results from {results_file}")
    df = pd.read_csv(results_file)
    
    # Check for missing data
    log_message(f"Found data for {len(df)} search engines")
    if df["Total Energy (Joules)"].isna().sum() > 0:
        log_message("Warning: Some entries have missing energy values!")
    
    return df


def create_plot(data_df, output_file):
    log_message("Creating energy consumption plot")
    
    # Sort by energy consumption
    df = data_df.sort_values(by="Total Energy (Joules)", ascending=False)
    
    # Set up bar chart
    plt.figure(figsize=(14, 8))
    
    # Use a different color for each search engine
    # Using a professional color palette that's distinct and visually appealing
    colors = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
        '#bcbd22',  # olive
        '#17becf',  # teal
    ]
    
    # Create the bar chart with multiple colors (one per search engine)
    bars = plt.bar(df["Search Engine"], df["Total Energy (Joules)"], 
                   color=colors[:len(df)])
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height + 0.1,
            f'{height:.1f}',
            ha='center', 
            va='bottom',
            rotation=0
        )
    
    # Set labels and title
    plt.xlabel("Search Engine", fontsize=12)
    plt.ylabel("Total Energy (Joules)", fontsize=12)
    plt.title("Energy Consumption Comparison of Search Engines", fontsize=16)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add a legend to identify search engines by color
    plt.legend(bars, df["Search Engine"], title="Search Engines", 
               loc="upper right", bbox_to_anchor=(1.15, 1))
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches="tight")
    log_message(f"Plot saved to {output_file}")
    
    # Show the plot
    plt.show()


def main():
    log_message("Starting visualization process")
    
    try:
        # Load results
        results_df = load_results(RESULTS_FILE)
        
        # Create and save plot
        create_plot(results_df, OUTPUT_PLOT)
        
        log_message("Visualization complete!")
        
    except FileNotFoundError as e:
        log_message(f"Error: Required file not found - {e}")
    except Exception as e:
        log_message(f"Error creating visualization: {e}")


if __name__ == "__main__":
    main()