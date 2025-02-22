import pandas as pd
import os
from datetime import datetime

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


def calculate_energy_consumption(timestamps_df, energy_df):
    """
    Calculate energy consumption for each search engine.
    
    Args:
        timestamps_df: DataFrame with search engine timestamps.
        energy_df: DataFrame with energy log data.
        
    Returns:
        DataFrame: Results with search engines and their energy consumption.
    """
    log_message("Calculating energy consumption for each search engine")
    
    results = []
    
    for index, row in timestamps_df.iterrows():
        engine = row["Search Engine"]
        start_time = row["Start Time"]
        end_time = row["End Time"]
        
        log_message(f"Processing {engine}: {start_time} to {end_time}")
        
        # Filter energy data within this timeframe
        engine_energy_df = energy_df[(energy_df["Time"] >= start_time) & 
                                      (energy_df["Time"] <= end_time)]
        
        # Check if we have data
        if engine_energy_df.empty:
            log_message(f"Warning: No energy data found for {engine}")
            total_energy = 0
        else:
            # Calculate total energy consumption
            # Note: Assuming readings are 1 second apart, so sum of watts = joules
            total_energy = engine_energy_df["SYSTEM_POWER (Watts)"].sum()
        
        # Save results
        results.append({
            "Search Engine": engine,
            "Total Energy (Joules)": total_energy
        })
    
    return pd.DataFrame(results)


def save_results(results_df, output_file):
    """
    Save processed results to CSV file.
    
    Args:
        results_df: DataFrame with energy consumption results.
        output_file: Path to save the output CSV file.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save as CSV
    results_df.to_csv(output_file, index=False)
    log_message(f"Final energy results saved to {output_file}")


def main():
    """Main function to process energy data."""
    log_message("Starting energy data processing")
    
    try:
        # Load data
        timestamps_df, energy_df = load_data(TIMESTAMPS_FILE, ENERGY_LOG_FILE)
        
        # Process data
        results_df = calculate_energy_consumption(timestamps_df, energy_df)
        
        # Save results
        save_results(results_df, OUTPUT_FILE)
        
        log_message("Energy data processing complete!")
        
    except FileNotFoundError as e:
        log_message(f"Error: Required file not found - {e}")
    except Exception as e:
        log_message(f"Error processing energy data: {e}")


if __name__ == "__main__":
    main()