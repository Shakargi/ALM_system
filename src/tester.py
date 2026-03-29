import pandas as pd
import sys

# Import your modules
import fileProcessor
from scenarios import ScenarioEngine, Scenarios

def run_alm_pipeline_test():
    print("=== Starting Test Run: FileProcessor + ScenarioEngine ===\n")
    
    file_path = "data\AS_ALL.xlsx"
    
    # 1. Load and process data using fileProcessor
    print("[1] Loading data via fileProcessor...")
    try:
        # Assuming this is how the function is called based on standard naming.
        # Update the method call if your function in fileProcessor.py is named differently:
        if hasattr(fileProcessor, 'load'):
            master_df = fileProcessor.load(file_path)
        elif hasattr(fileProcessor, 'FileProcessor'):
            processor = fileProcessor.FileProcessor()
            master_df = processor.load(file_path)
        else:
            # Fallback in case the name is different
            master_df = fileProcessor.process(file_path)
            
        print(f"  [V] Data loaded and processed successfully. Total rows: {len(master_df)}")
        
    except Exception as e:
        print(f"  [X] Error processing file via fileProcessor: {e}")
        sys.exit(1)

    # 2. Initialize ScenarioEngine
    print("\n[2] Initializing ScenarioEngine...")
    try:
        engine = ScenarioEngine(master_df)
        print("  [V] Engine initialized successfully.")
    except Exception as e:
        print(f"  [X] Error initializing ScenarioEngine: {e}")
        sys.exit(1)

    # 3. Run all scenarios
    print("\n[3] Running ALM calculations (NII & EVE) for all 6 scenarios...")
    results_df = engine.apply_all()
    
    # Print results to the console
    print("\n" + "="*80)
    print("Portfolio Results (Summary):")
    print("="*80)
    print(results_df.to_string(index=False))
    print("="*80 + "\n")
    
    # 4. Automated Sanity Checks (without external libraries)
    print("[4] Running logical checks (Sanity Checks)...")
    passed_tests = 0
    failed_tests = 0
    
    def assert_logic(condition, success_msg, fail_msg):
        nonlocal passed_tests, failed_tests
        if condition:
            print(f"  [PASS] {success_msg}")
            passed_tests += 1
        else:
            print(f"  [FAIL] {fail_msg}")
            failed_tests += 1

    # Extract specific rows for testing
    try:
        up_row = results_df[results_df['Scenario'] == 'Parallel Up (+200bp)'].iloc[0]
        down_row = results_df[results_df['Scenario'] == 'Parallel Down (-200bp)'].iloc[0]
        
        # Test 1: Base EVE must be identical across all scenarios
        assert_logic(
            up_row['EVE Base (₪)'] == down_row['EVE Base (₪)'],
            "EVE Base remains stable across different scenarios.",
            "Error: EVE Base changes between scenarios!"
        )
        
        # Test 2: Parallel Up should increase (or maintain) NII due to variable rate loans
        assert_logic(
            up_row['ΔNII (₪)'] >= 0,
            "Parallel Up increases (or maintains) the NII (as expected with variable rates).",
            f"Error: Parallel Up decreased the NII! Delta is {up_row['ΔNII (₪)']}"
        )

        # Test 3: Parallel Up must erode the portfolio's EVE due to a higher discount rate
        assert_logic(
            up_row['ΔEVE (₪)'] < 0,
            "Parallel Up erodes the economic EVE value (as expected when interest rises).",
            f"Error: Parallel Up increased the EVE! Delta is {up_row['ΔEVE (₪)']}"
        )
        
    except IndexError:
        print("  [FAIL] Parallel Up/Down scenarios not found in results, skipping logical checks.")

    print(f"\nTest Summary: {passed_tests} passed, {failed_tests} failed.")
    
    # 5. Save results to a file
    output_filename = "ALM_Scenarios_Results.csv"
    results_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"\n[V] Results saved to '{output_filename}'.")

if __name__ == "__main__":
    run_alm_pipeline_test()