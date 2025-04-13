import tkinter as tk
from dashboard.operator.OperatorDashboard import OperatorDashboard

class OperatorDashboardLauncher:
    def __init__(self):
        self.window = tk.Tk()  # Create the main tkinter window
        self.dashboard = None

    def launch(self):
        # Initialize and configure the OperatorDashboard inside the tkinter window
        self.dashboard = OperatorDashboard(master=self.window)
        
        # Start the tkinter main event loop
        self.window.mainloop()

if __name__ == "__main__":
    # Initialize and launch the Operator Dashboard
    launcher = OperatorDashboardLauncher()
    launcher.launch()

