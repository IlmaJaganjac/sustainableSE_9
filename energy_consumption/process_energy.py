import pandas as pd

# Load timestamps
timestamps_df = pd.read_csv("search_engine_timestamps.csv")

# Load energy log data
energy_df = pd.read_csv("energy_log.csv")

# Convert timestamps to numeric format if needed
energy_df["Time"] = pd.to_numeric(energy_df["Time"])

# Initialize results list
final_results = []

# Process each search engine
for index, row in timestamps_df.iterrows():
    engine = row["Search Engine"]
    start_time = row["Start Time"]
    end_time = row["End Time"]

    # Filter energy data within this timeframe
    engine_energy_df = energy_df[(energy_df["Time"] >= start_time) & (energy_df["Time"] <= end_time)]

    # Calculate total energy consumption
    total_energy = engine_energy_df["SYSTEM_POWER (Watts)"].sum()

    # Save results
    final_results.append({
        "Search Engine": engine,
        "Total Energy (Joules)": total_energy
    })

# Convert to DataFrame and save
final_results_df = pd.DataFrame(final_results)
final_results_df.to_csv("final_energy_results.csv", index=False)

print("\nFinal energy results saved as 'final_energy_results.csv'.")