import platform
import psutil
import time
import multiprocessing
import cpuinfo
import math
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from multiprocessing import Pool, freeze_support

class SystemInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Specifications & Performance Benchmark")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('Treeview', font=('Arial', 9))
        self.style.configure('Treeview.Heading', font=('Arial', 9, 'bold'))
        
        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # System Info Tab
        self.sysinfo_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sysinfo_tab, text="System Information")
        self.create_system_info_tab()
        
        # Benchmark Tab
        self.benchmark_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.benchmark_tab, text="Performance Benchmark")
        self.create_benchmark_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)
        
        # Load system info immediately
        self.load_system_info()
    
    def create_system_info_tab(self):
        # System Info Frame
        sysinfo_frame = ttk.LabelFrame(self.sysinfo_tab, text="System Specifications", padding="10")
        sysinfo_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for system info
        self.sysinfo_tree = ttk.Treeview(sysinfo_frame, columns=('value'), show='tree')
        self.sysinfo_tree.heading('#0', text='Category', anchor=tk.W)
        self.sysinfo_tree.heading('value', text='Value', anchor=tk.W)
        self.sysinfo_tree.column('#0', width=200)
        self.sysinfo_tree.column('value', width=550)
        
        vsb = ttk.Scrollbar(sysinfo_frame, orient="vertical", command=self.sysinfo_tree.yview)
        hsb = ttk.Scrollbar(sysinfo_frame, orient="horizontal", command=self.sysinfo_tree.xview)
        self.sysinfo_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.sysinfo_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        sysinfo_frame.grid_rowconfigure(0, weight=1)
        sysinfo_frame.grid_columnconfigure(0, weight=1)
        
        # Refresh button
        refresh_btn = ttk.Button(sysinfo_frame, text="Refresh System Info", command=self.load_system_info)
        refresh_btn.grid(row=2, column=0, pady=5, sticky='e')
    
    def create_benchmark_tab(self):
        # Benchmark Frame
        benchmark_frame = ttk.LabelFrame(self.benchmark_tab, text="CPU Performance Test", padding="10")
        benchmark_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Description
        desc_label = ttk.Label(benchmark_frame, 
                              text="This benchmark tests your CPU's single-core and multi-core performance\n"
                                   "by performing mathematical calculations. Lower times are better.",
                              justify=tk.CENTER)
        desc_label.pack(pady=5)
        
        # Results Frame
        results_frame = ttk.Frame(benchmark_frame)
        results_frame.pack(fill=tk.X, pady=10)
        
        # Single Core Results
        ttk.Label(results_frame, text="Single Core:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        self.single_time_var = tk.StringVar(value="Not tested")
        self.single_score_var = tk.StringVar(value="Not tested")
        ttk.Label(results_frame, text="Time:").grid(row=1, column=0, sticky='w', padx=20)
        ttk.Label(results_frame, textvariable=self.single_time_var).grid(row=1, column=1, sticky='w')
        ttk.Label(results_frame, text="Score:").grid(row=2, column=0, sticky='w', padx=20)
        ttk.Label(results_frame, textvariable=self.single_score_var).grid(row=2, column=1, sticky='w')
        
        # Dual Core Results
        ttk.Label(results_frame, text="Dual Core:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=(10,0))
        self.dual_time_var = tk.StringVar(value="Not tested")
        self.dual_score_var = tk.StringVar(value="Not tested")
        self.efficiency_var = tk.StringVar(value="Not tested")
        ttk.Label(results_frame, text="Time:").grid(row=4, column=0, sticky='w', padx=20)
        ttk.Label(results_frame, textvariable=self.dual_time_var).grid(row=4, column=1, sticky='w')
        ttk.Label(results_frame, text="Score:").grid(row=5, column=0, sticky='w', padx=20)
        ttk.Label(results_frame, textvariable=self.dual_score_var).grid(row=5, column=1, sticky='w')
        ttk.Label(results_frame, text="Efficiency:").grid(row=6, column=0, sticky='w', padx=20)
        ttk.Label(results_frame, textvariable=self.efficiency_var).grid(row=6, column=1, sticky='w')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(benchmark_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # Run Benchmark Button
        self.run_btn = ttk.Button(benchmark_frame, text="Run Benchmark", command=self.start_benchmark_thread)
        self.run_btn.pack(pady=5)
        
    def load_system_info(self):
        try:
            self.sysinfo_tree.delete(*self.sysinfo_tree.get_children())
            
            # CPU Information
            cpu_node = self.sysinfo_tree.insert('', 'end', text='CPU Information', open=True)
            cpu_info = cpuinfo.get_cpu_info()
            self.sysinfo_tree.insert(cpu_node, 'end', text='Processor', values=(cpu_info['brand_raw'],))
            self.sysinfo_tree.insert(cpu_node, 'end', text='Architecture', values=(platform.machine(),))
            self.sysinfo_tree.insert(cpu_node, 'end', text='Physical Cores', values=(psutil.cpu_count(logical=False),))
            self.sysinfo_tree.insert(cpu_node, 'end', text='Logical Cores', values=(psutil.cpu_count(logical=True),))
            if hasattr(psutil.cpu_freq(), 'current'):
                self.sysinfo_tree.insert(cpu_node, 'end', text='Current Frequency', values=(f"{psutil.cpu_freq().current:.2f} MHz",))
            
            # Memory Information
            mem_node = self.sysinfo_tree.insert('', 'end', text='Memory Information', open=True)
            mem = psutil.virtual_memory()
            self.sysinfo_tree.insert(mem_node, 'end', text='Total RAM', values=(f"{mem.total / (1024**3):.2f} GB",))
            self.sysinfo_tree.insert(mem_node, 'end', text='Available RAM', values=(f"{mem.available / (1024**3):.2f} GB",))
            self.sysinfo_tree.insert(mem_node, 'end', text='Used RAM', values=(f"{mem.used / (1024**3):.2f} GB",))
            
            # Disk Information
            disk_node = self.sysinfo_tree.insert('', 'end', text='Storage Information', open=True)
            disk = psutil.disk_usage('/')
            self.sysinfo_tree.insert(disk_node, 'end', text='Total Space', values=(f"{disk.total / (1024**3):.2f} GB",))
            self.sysinfo_tree.insert(disk_node, 'end', text='Used Space', values=(f"{disk.used / (1024**3):.2f} GB",))
            self.sysinfo_tree.insert(disk_node, 'end', text='Free Space', values=(f"{disk.free / (1024**3):.2f} GB",))
            
            # OS Information
            os_node = self.sysinfo_tree.insert('', 'end', text='Operating System', open=True)
            self.sysinfo_tree.insert(os_node, 'end', text='System', values=(f"{platform.system()} {platform.release()}",))
            self.sysinfo_tree.insert(os_node, 'end', text='Version', values=(platform.version(),))
            self.sysinfo_tree.insert(os_node, 'end', text='Python Version', values=(platform.python_version(),))
            
            self.status_var.set("System information loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load system information: {str(e)}")
            self.status_var.set("Error loading system information")
    
    @staticmethod
    def cpu_benchmark(iterations=10000000):
        """Static CPU benchmark function for multiprocessing"""
        for _ in range(iterations):
            math.sqrt(25) + math.pow(5, 2)
    
    def single_core_test(self):
        """Measure single core performance"""
        start_time = time.time()
        self.cpu_benchmark()
        end_time = time.time()
        return end_time - start_time
    
    def dual_core_test(self):
        """Measure dual core performance using multiprocessing Pool"""
        start_time = time.time()
        
        # Create a pool of 2 workers
        with Pool(processes=2) as pool:
            # Run two instances of the benchmark
            pool.map(self.cpu_benchmark, [10000000, 10000000])
        
        end_time = time.time()
        return end_time - start_time
    
    def run_benchmark(self):
        """Run and display performance tests"""
        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set("Running benchmark... Please wait")
        self.progress_var.set(0)
        
        try:
            # Warm-up run (first run is often slower)
            self.status_var.set("Warming up CPU...")
            self.progress_var.set(10)
            self.single_core_test()
            
            # Single core test
            self.status_var.set("Running single core test...")
            self.progress_var.set(30)
            single_time = self.single_core_test()
            self.single_time_var.set(f"{single_time:.4f} seconds")
            single_score = 1 / single_time * 1000
            self.single_score_var.set(f"{single_score:.2f} (higher is better)")
            
            # Dual core test
            self.status_var.set("Running dual core test...")
            self.progress_var.set(70)
            dual_time = self.dual_core_test()
            self.dual_time_var.set(f"{dual_time:.4f} seconds")
            dual_score = 1 / dual_time * 1000
            self.dual_score_var.set(f"{dual_score:.2f} (higher is better)")
            
            # Efficiency calculation
            efficiency = (single_time / dual_time) * 100
            self.efficiency_var.set(f"{efficiency:.2f}% of ideal scaling")
            
            self.progress_var.set(100)
            self.status_var.set("Benchmark completed successfully")
        except Exception as e:
            messagebox.showerror("Benchmark Error", f"An error occurred during benchmarking: {str(e)}")
            self.status_var.set("Benchmark failed")
        finally:
            self.run_btn.config(state=tk.NORMAL)
    
    def start_benchmark_thread(self):
        """Start the benchmark in a separate thread to keep the GUI responsive"""
        benchmark_thread = Thread(target=self.run_benchmark, daemon=True)
        benchmark_thread.start()

if __name__ == "__main__":
    freeze_support()  # Required for Windows multiprocessing
    root = tk.Tk()
    app = SystemInfoApp(root)
    root.mainloop()