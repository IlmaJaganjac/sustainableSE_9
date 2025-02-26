import importlib
import sys
import os

def ensure_directories_exist():
    directories = ["search_engine_results", "results", "plots"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def run_measurement_pipeline():
    # Ensure output directories exist
    ensure_directories_exist()
    
    interval = 200
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"Invalid interval value: {sys.argv[1]}, using default 200.")

    os.environ["INTERVAL"] = str(interval)

    # List of modules to run in order
    modules_to_run = [
        'measure',
        'process_energy',
        'plot_results'
    ]
    
    # Run each module in sequence
    for module_name in modules_to_run:
        print(f"\n{'='*80}")
        print(f"Running {module_name}.py...")
        print(f"{'='*80}\n")
        
        # Import and run the module
        try:
            # Force reload in case the module was previously imported
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            module = importlib.import_module(module_name)
            
            # If the module has a main function, use it
            if hasattr(module, 'main'):
                module.main()
            # Otherwise, the module's global code will run on import
            
            print(f"\n{module_name}.py completed successfully.")
            
        except Exception as e:
            print(f"Error running {module_name}.py: {e}")
            print("Pipeline execution stopped due to error.")
            return False
    
    print("\n\nComplete measurement pipeline executed successfully!")
    print("Check the 'plots' directory for visualization results.")
    return True

if __name__ == "__main__":
    run_measurement_pipeline()