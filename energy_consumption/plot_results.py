import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load Data
df = pd.read_csv("final_energy_results.csv")

# Check for missing data
print("Available Search Engines:", df["Search Engine"].unique())
if df["Total Energy (Joules)"].isna().sum() > 0:
    print("Warning: Some entries have missing energy values!")

# Sort by energy consumption
df = df.sort_values(by="Total Energy (Joules)", ascending=False)

# Set up bar chart
plt.figure(figsize=(14, 8))

# Create the bar chart
bars = plt.bar(df["Search Engine"], df["Total Energy (Joules)"])

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

# Add color gradient based on energy usage
colors = plt.cm.YlOrRd(np.linspace(0.2, 0.8, len(df)))
for i, bar in enumerate(bars):
    bar.set_color(colors[i])

# Add a colorbar legend
sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd)
sm.set_array([])
cbar = plt.colorbar(sm)
cbar.set_label('Energy Consumption Level', rotation=270, labelpad=25)

# Save and show the plot
plt.tight_layout()
plt.savefig("plots/energy_consumption_plot.png", bbox_inches="tight")
plt.show()