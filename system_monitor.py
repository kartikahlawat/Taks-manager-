from collections import deque
import psutil
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
import platform  # Added for system information

class SystemResourceMonitor:
    def __init__(self):
        self.cpu_history = deque(maxlen=50)
        self.mem_history = deque(maxlen=50)
        self.disk_read_history = deque(maxlen=50)
        self.disk_write_history = deque(maxlen=50)
        self.network_send_history = deque(maxlen=50)
        self.network_recv_history = deque(maxlen=50)
        self.last_network_stats = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.console = Console()
        self.log_file = "system_performance.log"
        self.process_update_interval = 2
        self.last_process_update = 0
        self.processes = []

    def _convert_bytes(self, num):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return f"{num:.2f} {unit}"
            num /= 1024.0
        return f"{num:.2f} PB"

    def get_disk_activity(self):
        current_disk_io = psutil.disk_io_counters()
        read_bytes = current_disk_io.read_bytes - self.last_disk_io.read_bytes
        write_bytes = current_disk_io.write_bytes - self.last_disk_io.write_bytes
        self.last_disk_io = current_disk_io
        self.disk_read_history.append(read_bytes / 1024)
        self.disk_write_history.append(write_bytes / 1024)
        return {
            'read': self._convert_bytes(read_bytes) + '/s',
            'write': self._convert_bytes(write_bytes) + '/s'
        }

    def get_running_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'memory': proc.info['memory_percent'],
                    'cmd': ' '.join(proc.info['cmdline'][:2]) if proc.info['cmdline'] else proc.info['name']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(processes, key=lambda x: (x['cpu'], x['memory']), reverse=True)[:10]

    def get_system_stats(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_percent)
        mem = psutil.virtual_memory()
        self.mem_history.append(mem.percent)
        disk_activity = self.get_disk_activity()
        current_network_stats = psutil.net_io_counters()
        sent_diff = current_network_stats.bytes_sent - self.last_network_stats.bytes_sent
        recv_diff = current_network_stats.bytes_recv - self.last_network_stats.bytes_recv
        self.network_send_history.append(sent_diff / 1024)
        self.network_recv_history.append(recv_diff / 1024)
        self.last_network_stats = current_network_stats

        if time.time() - self.last_process_update > self.process_update_interval:
            self.processes = self.get_running_processes()
            self.last_process_update = time.time()

        stats = {
            'cpu': cpu_percent,
            'memory': mem.percent,
            'disk_activity': disk_activity,
            'network': {
                'sent': self._convert_bytes(sent_diff) + '/s',
                'received': self._convert_bytes(recv_diff) + '/s'
            }
        }
        self.log_performance(stats)
        return stats

    def log_performance(self, stats):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as log:
            log.write(f"[{timestamp}] CPU: {stats['cpu']}%, Memory: {stats['memory']}%, "
                      f"Disk Read: {stats['disk_activity']['read']}, Disk Write: {stats['disk_activity']['write']}, "
                      f"Network Sent: {stats['network']['sent']}, Network Received: {stats['network']['received']}\n")

    def create_graph(self, history, title, color):
        graph_str = "".join(["█" * (int(v) // 2) + " " * (50 - int(v) // 2) + "\n" for v in history])
        return Panel(graph_str, title=title, border_style=color)

    def create_process_table(self):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("PID", width=8)
        table.add_column("Name", width=20)
        table.add_column("CPU%", width=8)
        table.add_column("Mem%", width=8)
        table.add_column("Command", width=50)

        for proc in self.processes:
            table.add_row(
                str(proc['pid']),
                proc['name'][:20],
                f"{proc['cpu']:.1f}",
                f"{proc['memory']:.1f}",
                proc['cmd'][:45]
            )
        return table

    def create_dashboard(self):
        stats = self.get_system_stats()
        layout = Layout()

        # Get battery info
        battery = psutil.sensors_battery()
        battery_info = "N/A"
        if battery:
            battery_info = f"{battery.percent:.2f}% {'(Charging)' if battery.power_plugged else '(Discharging)'}"


        # Get system info
        system_info = (
            f"{platform.system()} {platform.release()} | "
            f"{platform.processor()} | "
            f"{platform.machine()}"
        )

        overview_panel = Panel(
            f"[bold blue]CPU:[/] {stats['cpu']}%\n"
            f"[bold red]Memory:[/] {stats['memory']}%\n"
            f"[bold yellow]Disk Read:[/] {stats['disk_activity']['read']}\n"
            f"[bold yellow]Disk Write:[/] {stats['disk_activity']['write']}\n"
            f"[bold cyan]Network:[/] {stats['network']['sent']} | {stats['network']['received']}\n"
            f"[bold green]Battery:[/] {battery_info}\n"
            f"[bold magenta]System:[/] {system_info}",
            title="System Overview",
            border_style="blue"
        )

        cpu_graph = self.create_graph(self.cpu_history, "CPU Usage", "green")
        mem_graph = self.create_graph(self.mem_history, "Memory Usage", "red")
        disk_read_graph = self.create_graph(self.disk_read_history, "Disk Read KB/s", "yellow")
        disk_write_graph = self.create_graph(self.disk_write_history, "Disk Write KB/s", "magenta")
        net_graph = self.create_graph(self.network_send_history, "Network Activity", "cyan")
        process_panel = Panel(self.create_process_table(), title="Top Processes", border_style="green")

        layout.split_column(
            Layout(overview_panel, name="overview", ratio=1),
            Layout(name="middle"),
            Layout(name="bottom")
        )

        layout["middle"].split_row(
            Layout(cpu_graph, name="cpu", ratio=1),
            Layout(mem_graph, name="memory", ratio=1),
            Layout(disk_read_graph, name="disk_read", ratio=1),
            Layout(disk_write_graph, name="disk_write", ratio=1),
            Layout(net_graph, name="network", ratio=1)
        )

        layout["bottom"].split_row(
            Layout(process_panel, name="processes", ratio=3),
        )

        return layout

    def run(self):
        with Live(self.create_dashboard(), refresh_per_second=4, screen=True) as live:
            try:
                while True:
                    live.update(self.create_dashboard())
                    time.sleep(0.25)
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")

def main():
    monitor = SystemResourceMonitor()
    monitor.run()

if __name__ == "__main__":
    main()

