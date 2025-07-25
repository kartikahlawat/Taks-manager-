# Task Manager

system_monitor.py is the core Python script powering the Task Manager. It uses the psutil and rich libraries to monitor and display real-time system resource usage in the terminal. The script tracks CPU, memory, disk, and network activity, and lists the top running processes. It also logs system performance data and presents everything in a dynamic dashboard with graphs and tables.



Key Features:CCC

Resource Monitoring: Tracks CPU, memory, disk I/O, and network usage over time.c
Process Display: Lists the top active processes with details including PID, name, CPU and memory usage, and command.
System Information: Shows operating system details and battery status (if available).
Real-time Dashboard: Presents all statistics in a dynamic terminal dashboard with graphs and tables.
Logging: Automatically logs system performance data (CPU, memory, disk, network) to a file (system_performance.log) for activity tracking and later review.
Run the script to launch an interactive terminal dashboard and keep a log of your system’s activity efficiently.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/kartikahlawat/Taks-manager-.git
