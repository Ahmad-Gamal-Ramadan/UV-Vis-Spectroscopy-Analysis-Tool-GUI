import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class UVVisGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UV-Vis Spectrum Plotter")
        self.root.geometry("1000x650")

        self.file_path = tk.StringVar()
        self.title_var = tk.StringVar(value="UV-Vis Spectrum")
        self.x_label_var = tk.StringVar(value="Wavelength (nm)")
        self.y_label_var = tk.StringVar(value="Absorbance")
        self.status_var = tk.StringVar(value="Ready")

        self.wavelengths = None
        self.absorbance = None

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # Controls
        controls = ttk.LabelFrame(main, text="Controls", padding=10)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Data file:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.file_path, width=70).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(controls, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(controls, text="Load + Plot", command=self.load_and_plot).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(controls, text="Plot title:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.title_var, width=35).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(controls, text="X label:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.x_label_var, width=20).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(controls, text="Y label:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(controls, textvariable=self.y_label_var, width=35).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Button(controls, text="Update Labels", command=self.refresh_plot).grid(row=2, column=2, padx=5, pady=5)
        ttk.Button(controls, text="Save Plot", command=self.save_plot).grid(row=2, column=3, padx=5, pady=5)

        controls.columnconfigure(1, weight=1)

        # Figure
        fig_frame = ttk.LabelFrame(main, text="Spectrum", padding=5)
        fig_frame.pack(fill="both", expand=True)

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(self.title_var.get())
        self.ax.set_xlabel(self.x_label_var.get())
        self.ax.set_ylabel(self.y_label_var.get())
        self.ax.grid(alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.figure, master=fig_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, fig_frame)
        toolbar.update()

        # Status bar
        status = ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", pady=(8, 0))

    def browse_file(self):
        filetypes = [
            ("Text files", "*.txt *.dat *.csv"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select UV-Vis data file", filetypes=filetypes)
        if path:
            self.file_path.set(path)
            self.status_var.set(f"Selected: {path}")

    def load_uv_vis_data(self, path: str):
        # Try whitespace-delimited first, then comma-delimited
        loaders = [
            lambda p: np.loadtxt(p),
            lambda p: np.loadtxt(p, delimiter=','),
            lambda p: np.genfromtxt(p, comments='#'),
            lambda p: np.genfromtxt(p, delimiter=',', comments='#'),
        ]

        last_error = None
        for loader in loaders:
            try:
                data = loader(path)
                if data is None:
                    continue
                data = np.asarray(data)
                if data.ndim == 1:
                    if data.size < 2:
                        continue
                    data = data.reshape(-1, 2)
                if data.shape[1] < 2:
                    continue
                data = data[:, :2]
                # Remove rows with NaN values
                data = data[~np.isnan(data).any(axis=1)]
                if len(data) == 0:
                    continue
                wavelengths = data[:, 0]
                absorbance = data[:, 1]
                return wavelengths, absorbance
            except Exception as exc:
                last_error = exc
        raise ValueError(f"Could not read the file as two-column numeric data. Last error: {last_error}")

    def load_and_plot(self):
        path = self.file_path.get().strip()
        if not path:
            messagebox.showwarning("No file selected", "Please choose a UV-Vis data file first.")
            return

        try:
            self.wavelengths, self.absorbance = self.load_uv_vis_data(path)
            self.plot_uv_vis_spectrum()
            self.status_var.set(f"Loaded {len(self.wavelengths)} data points from {path}")
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))
            self.status_var.set("Failed to load file")

    def plot_uv_vis_spectrum(self):
        self.ax.clear()
        self.ax.plot(self.wavelengths, self.absorbance, color="blue", linewidth=1.8, label="Absorbance")
        self.ax.set_title(self.title_var.get())
        self.ax.set_xlabel(self.x_label_var.get())
        self.ax.set_ylabel(self.y_label_var.get())
        self.ax.grid(alpha=0.3)
        self.ax.legend()
        self.canvas.draw()

    def refresh_plot(self):
        if self.wavelengths is None or self.absorbance is None:
            messagebox.showinfo("No data", "Load a file first, then update the labels.")
            return
        self.plot_uv_vis_spectrum()
        self.status_var.set("Plot labels updated")

    def save_plot(self):
        if self.wavelengths is None or self.absorbance is None:
            messagebox.showinfo("No plot", "Load and plot data first.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save plot",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("PDF file", "*.pdf"), ("All files", "*.*")],
        )
        if save_path:
            self.figure.savefig(save_path, bbox_inches="tight")
            self.status_var.set(f"Plot saved to {save_path}")
            messagebox.showinfo("Saved", f"Plot saved successfully to:\n{save_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = UVVisGUI(root)
    root.mainloop()
