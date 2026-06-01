import pandas as pd
import heapq
import time
import matplotlib.pyplot as plt
import numpy as np

# --- 1. LOAD AND PREPARE BASE DATA ---
try:
    df_base = pd.read_csv("Student_Database.csv")
    df_base["Total"] = df_base["Nilai_Ujian"] + df_base["Nilai_Project"]
except FileNotFoundError:
    print("Error: Student_Database.csv not found. Please run this script in the correct directory.")
    exit()

# Define the sample sizes to test
dataset_sizes = [10, 30, 63]

# Arrays to store times
sorting_times = []
max_heap_times = []
loh_times = []

# --- 1. CONVERT ENTIRE DATASET TO PURE PYTHON STRUCTURES FIRST ---
raw_data = df_base[["Nama", "Total"]].to_dict('records')

# Define the sample sizes to test
dataset_sizes = [10, 30, 63]
sorting_times = []
max_heap_times = []
loh_times = []

NUM_RUNS = 200  # Increased iterations for highly stable microsecond averages

# --- 2. THE PURIFIED BENCHMARKING LOOP ---
for size in dataset_sizes:
    current_size = min(size, len(raw_data))
    
    # Take a random sample subset for this size using standard Python random
    import random
    random.seed(42)
    sample_data = random.sample(raw_data, current_size)
    
    # --- A. Benchmark Pure Python Full Data Sorting ---
    t_sort_total = 0
    for _ in range(NUM_RUNS):
        t0 = time.perf_counter()
        # Equivalent to sorting the data and picking top 5
        sorted_res = sorted(sample_data, key=lambda x: x["Total"], reverse=True)
        top_k_sort = sorted_res[:5]
        t1 = time.perf_counter()
        t_sort_total += (t1 - t0) * 1000
    sorting_times.append(t_sort_total / NUM_RUNS)
    
    # --- B. Benchmark Pure Python Max-Heap ---
    t_heap_total = 0
    for _ in range(NUM_RUNS):
        t0 = time.perf_counter()
        max_heap = []
        for row in sample_data:
            heapq.heappush(max_heap, (-row["Total"], row["Nama"]))
        top_k_heap = []
        for _ in range(min(5, current_size)):
            if max_heap:
                neg_total, nama = heapq.heappop(max_heap)
                top_k_heap.append({"Nama": nama, "Total": -neg_total})
        t1 = time.perf_counter()
        t_heap_total += (t1 - t0) * 1000
    max_heap_times.append(t_heap_total / NUM_RUNS)

    # --- PRE-BUILD LOH LAYERS AS PURE LISTS OUTSIDE THE TIMER ---
    sorted_sample_data = sorted(sample_data, key=lambda x: x["Total"], reverse=True)
    py_layers = []
    layer_size = 1
    idx = 0
    while idx < len(sorted_sample_data):
        py_layers.append(sorted_sample_data[idx:idx + layer_size])
        idx += layer_size
        layer_size *= 2

    # --- C. Benchmark Pure Python LOH (Pruning Algorithm) ---
    t_loh_total = 0
    for _ in range(NUM_RUNS):
        t0 = time.perf_counter()
        k = 5
        
        # Step 1: Initialize candidates with Level 1
        initial_candidates = list(py_layers[0]) if len(py_layers) > 0 else []
        # (Level 1 is already sorted by construction)
        if len(initial_candidates) >= k:
            threshold = initial_candidates[k-1]["Total"]
        else:
            threshold = initial_candidates[-1]["Total"] if initial_candidates else 0
            
        all_candidates = list(initial_candidates)
        
        # Step 2: Scan subsequent layers and PRUNE
        for layer in py_layers[1:]:
            # Native Python list lookups are lightning fast compared to Pandas series max()
            layer_max = layer[0]["Total"] # Since layers are sorted, index 0 is always the max
            
            if layer_max >= threshold:
                # ACTIVE LAYER: Process and incorporate elements
                all_candidates.extend(layer)
                all_candidates.sort(key=lambda x: x["Total"], reverse=True)
                threshold = all_candidates[min(k, len(all_candidates))-1]["Total"]
            else:
                # PRUNED LAYER: Completely skipped instantly!
                pass
                
        top_k_loh = all_candidates[:k]
        t1 = time.perf_counter()
        t_loh_total += (t1 - t0) * 1000
    loh_times.append(t_loh_total / NUM_RUNS)

# --- 3. PRINT BENCHMARK RESULTS ---
print("\n=== BENCHMARK RESULTS (in milliseconds) ===")
print(f"Dataset Sizes: {dataset_sizes}")
print(f"Sorting Times: {[f'{t:.4f} ms' for t in sorting_times]}")
print(f"Max-Heap Times: {[f'{t:.4f} ms' for t in max_heap_times]}")
print(f"LOH Times:     {[f'{t:.4f} ms' for t in loh_times]}")

# --- 4. GENERATE THE MATPLOTLIB GRAPH ---
x = np.arange(len(dataset_sizes))
width = 0.25

fig, ax = plt.subplots(figsize=(9, 6), dpi=100)

rects1 = ax.bar(x - width, sorting_times, width, label='Full Data Sorting', color='#e74c3c')
rects2 = ax.bar(x, max_heap_times, width, label='Traditional Max-Heap', color='#f39c12')
rects3 = ax.bar(x + width, loh_times, width, label='LOH (Pruning Algorithm)', color='#2ecc71')

ax.set_xlabel('Dataset Size (Number of Students)', fontsize=11, fontweight='bold', labelpad=10)
ax.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold', labelpad=10)
ax.set_title('Performance Comparison for Top-5 Retrieval', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels([f"{s} Students" for s in dataset_sizes])
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.5)

# Auto-label function to display values on top of bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.tight_layout()
plt.savefig('loh_performance_chart.png', dpi=300)
print("\n[Success] Chart saved as 'loh_performance_chart.png'!")
plt.show()