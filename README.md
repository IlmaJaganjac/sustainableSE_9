# Search Engine Energy Efficiency Measurement

This repository contains tools to measure and analyze the energy consumption of various search engines. The system uses Selenium to automate search queries across multiple search engines, while EnergiBridge captures energy consumption metrics during these operations.

## Overview

The system consists of several Python scripts that work together to:

1. Automate search queries across multiple search engines
2. Measure the energy consumption during these searches
3. Process the collected data to calculate energy efficiency metrics
4. Generate visualizations to compare the energy efficiency of different search engines

## Dependencies

### Python Dependencies

Install the required Python packages using pip:

```bash
pip install selenium pandas numpy scipy matplotlib seaborn
```

### Chrome WebDriver

The system uses Chrome and ChromeDriver for automation:

1. Make sure you have Google Chrome installed
2. Download the appropriate ChromeDriver version from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)
3. Place the ChromeDriver executable in your PATH

### EnergiBridge

EnergiBridge is used to collect energy consumption metrics. You should clone the EnergiBridge repository inside this project's directory:

```bash
git clone https://github.com/DEEDS-TUD/EnergiBridge.git
cd EnergiBridge
cargo build --release
cd ..
```

Make sure Rust and Cargo are installed on your system to build EnergiBridge.

## Project Structure

- `main.py` - The main entry point that coordinates the measurement pipeline
- `measure.py` - Automates search queries across multiple search engines
- `process_energy.py` - Processes the collected energy data
- `plot_results.py` - Generates visualizations for the processed data
- `baseline_measurement.py` - Measures baseline overhead of Selenium for each search engine

## Setting Up

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/search-engine-energy-measurement.git
   cd search-engine-energy-measurement
   ```

2. Create necessary directories:
   ```bash
   mkdir -p search_engine_results results plots
   ```

3. Make sure EnergiBridge is properly set up inside the repository:
   ```bash
   git clone https://github.com/DEEDS-TUD/EnergiBridge.git
   cd EnergiBridge
   cargo build --release
   cd ..
   ```

## Running the System

To run the complete measurement pipeline, use the following command:

```bash
./EnergiBridge/target/release/energibridge -o energy_log.csv --summary -- python3 src/main.py
```

This command will:
1. Start EnergiBridge to collect energy metrics
2. Run the measurement pipeline which includes:
   - Automating search queries across search engines
   - Processing the collected energy data
   - Generating visualizations

## Configuration

You can modify the following parameters in the source files:

- `measure.py`:
  - `SEARCH_ENGINES`: Dictionary defining the search engines to test
  - `SEARCH_QUERIES`: List of search queries to use
  - `ITERATIONS`: Number of test iterations per search engine

- `process_energy.py`:
  - `BUFFER`: Buffer time in milliseconds (can be set via environment variable `INTERVAL`)
  - `W`: Weights for the Energy Delay Product calculations

## Results

After running the system, results will be available in the following locations:

- `search_engine_results/search_engine_timestamps.csv` - Raw timestamps of search operations
- `energy_log.csv` - Raw energy measurements from EnergiBridge
- `results/final_energy_results.csv` - Processed energy consumption results
- `results/pairwise_comparisons.csv` - Statistical comparisons between search engines
- `results/plots/` - Visualizations of the results

## Notes

- The measurement process may take several hours to complete depending on the number of search engines and iterations.
- Make sure your system is in a stable state during measurements (minimal background processes).
- Internet connectivity is required throughout the measurement process.
- The system automatically handles temporary internet connectivity issues.

## Baseline Measurement

To measure the baseline overhead introduced by Selenium for each search engine:

```bash
python3 baseline_measurement.py
```

This will generate a `baseline_average.csv` file that is used by the main measurement process.

## Customization

You can adjust the interval parameter by passing it as an argument to `main.py`:

```bash
./EnergiBridge/target/release/energibridge -o energy_log.csv --summary -- python3 src/main.py 300
```

This sets the buffer interval to 300ms (default is 200ms).
