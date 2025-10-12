import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import os
import sys

# --- Environment Diagnosis ---
# This will help debug installation issues with reportlab.
print("--- Python Environment ---")
print(f"Executable: {sys.executable}")
print(f"Version: {sys.version}")
print("--------------------------")

# Attempt to import required libraries. If any fail, prompt the user to install them.
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    # Import the Calendar widget instead of DateEntry
    from tkcalendar import Calendar
except ImportError as e:
    missing_library = str(e).split("'")[1]
    messagebox.showerror(
        "Missing Library",
        f"The '{missing_library}' library is required. Please install it by running:\n\npip install {missing_library}"
    )
    sys.exit(1)

class InvoiceApp(tk.Tk):
    """
    A desktop application for creating and managing simple invoices.
    Allows adding items, calculating totals with GST, generating a PDF,
    and printing the invoice.
    """
    def __init__(self):
        super().__init__()
        self.title("Simple Invoice Generator")
        self.geometry("1200x700")
        self.minsize(950, 600) # Set a minimum size for the window
        self.configure(bg="#f0f0f0")

        # Style configuration for ttk widgets
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 10))
        style.configure("TEntry", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10, "bold"), padding=5)
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        
        self.item_rows = []
        self.last_pdf_path = None # To store the path of the last generated PDF
        self._create_widgets()
        self.add_item_row() # Start with one empty item row

    def _create_widgets(self):
        """Creates and places all the widgets in the main window."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Make the main frame's columns and rows responsive
        main_frame.rowconfigure(1, weight=1) # The items frame should expand vertically
        main_frame.columnconfigure(0, weight=1) # The single column should expand horizontally

        # --- Header Section (Doctor Name, Date) ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        # FIX: Replace DateEntry with a standard Entry and a Button to trigger a custom calendar popup.
        # This gives us full control over the popup's position to prevent clipping.
        
        # Pack date elements to the RIGHT first to reserve their space.
        self.date_button = ttk.Button(header_frame, text="📅", command=self._open_calendar, width=3)
        self.date_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.date_var = tk.StringVar(value=date.today().strftime('%d-%m-%Y'))
        self.date_entry = ttk.Entry(header_frame, textvariable=self.date_var, width=12, justify='center')
        self.date_entry.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(header_frame, text="Date:", font=("Helvetica", 11, "bold")).pack(side=tk.RIGHT, padx=(20, 5))

        # Pack doctor name elements to the LEFT, allowing the entry to expand and fill space.
        ttk.Label(header_frame, text="Doctor's Name:", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.doctor_name_entry = ttk.Entry(header_frame, width=40)
        self.doctor_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # --- Items Section ---
        items_canvas_frame = ttk.Frame(main_frame)
        items_canvas_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        canvas = tk.Canvas(items_canvas_frame, bg="#ffffff")
        scrollbar = ttk.Scrollbar(items_canvas_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self._create_item_headers()

        # --- Footer Section (Totals and Buttons) ---
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=10)

        # Action Buttons
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.add_item_btn = ttk.Button(button_frame, text="Add Item", command=self.add_item_row)
        self.add_item_btn.pack(side=tk.LEFT, padx=5)

        self.remove_item_btn = ttk.Button(button_frame, text="Remove Last Item", command=self.remove_last_item_row)
        self.remove_item_btn.pack(side=tk.LEFT, padx=5)
        
        # Totals Display
        totals_frame = ttk.Frame(footer_frame)
        totals_frame.pack(side=tk.RIGHT)

        ttk.Label(totals_frame, text="Total Amount (Excl. GST):", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5)
        self.total_excl_gst_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.total_excl_gst_label.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(totals_frame, text="Total GST Amount:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="e", padx=5)
        self.total_gst_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.total_gst_label.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(totals_frame, text="Grand Total (Incl. GST):", font=("Helvetica", 12, "bold")).grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.grand_total_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 12, "bold"))
        self.grand_total_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # --- PDF/Print Action Bar ---
        action_bar = ttk.Frame(main_frame, padding=10)
        action_bar.grid(row=3, column=0, sticky="ew")
        
        # Create a frame to push buttons to the right
        action_button_container = ttk.Frame(action_bar)
        action_button_container.pack(side=tk.RIGHT)

        self.generate_pdf_btn = ttk.Button(action_button_container, text="Generate PDF", command=self.generate_pdf)
        self.generate_pdf_btn.pack(side=tk.LEFT, padx=5)

        self.print_btn = ttk.Button(action_button_container, text="Print Invoice", command=self.print_invoice)
        self.print_btn.pack(side=tk.LEFT, padx=5)

    def _open_calendar(self):
        """Creates a Toplevel window with a calendar to select a date."""
        
        def set_date():
            """Updates the date entry with the selected date and closes the calendar."""
            self.date_var.set(cal.get_date())
            top.destroy()

        top = tk.Toplevel(self)
        top.title("Select Date")
        top.grab_set()  # Make the window modal

        try:
            current_date = datetime.strptime(self.date_var.get(), '%d-%m-%Y')
            cal = Calendar(top, selectmode='day', date_pattern='dd-mm-y',
                           year=current_date.year, month=current_date.month, day=current_date.day)
        except ValueError:
            cal = Calendar(top, selectmode='day', date_pattern='dd-mm-y')

        cal.pack(pady=10, padx=10)
        ttk.Button(top, text="OK", command=set_date).pack(pady=5)

        # --- Intelligent Positioning Logic ---
        self.update_idletasks()
        
        entry_x = self.date_entry.winfo_rootx()
        entry_y = self.date_entry.winfo_rooty()
        entry_height = self.date_entry.winfo_height()
        
        top_width = top.winfo_reqwidth()
        
        popup_y = entry_y + entry_height + 5
        popup_x = entry_x
        
        # If placing the calendar at the entry's x position would push it off-screen,
        # adjust the x position to keep it within the screen bounds.
        if popup_x + top_width > self.winfo_screenwidth():
            popup_x = self.winfo_screenwidth() - top_width - 10

        top.geometry(f"+{popup_x}+{popup_y}")


    def _create_item_headers(self):
        """Creates the header labels for the item list."""
        headers = [
            "S.No.", "Product Name", "Packing", "Batch No.", "Qty", "Free",
            "Rate", "GST (%)", "Value (Excl. GST)", "Value (Incl. GST)"
        ]
        column_widths = [5, 35, 15, 15, 8, 8, 10, 8, 15, 15]
        
        for i, header in enumerate(headers):
            label = ttk.Label(self.scrollable_frame, text=header, style="Header.TLabel", borderwidth=1, relief="solid", padding=5, anchor="center")
            label.grid(row=0, column=i, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=column_widths[i]*5) # Set column weights

    def add_item_row(self):
        """Adds a new row of entry fields for an invoice item."""
        row_num = len(self.item_rows) + 1
        
        # --- Create Variable Dictionary and Widgets for the new row ---
        row_vars = {
            'serial': tk.StringVar(value=str(row_num)),
            'product': tk.StringVar(),
            'packing': tk.StringVar(),
            'batch_no': tk.StringVar(),
            'qty': tk.StringVar(value='0'),
            'free': tk.StringVar(value='0'),
            'rate': tk.StringVar(value='0.00'),
            'gst': tk.StringVar(value='0'),
            'val_excl_gst': tk.StringVar(value='0.00'),
            'val_incl_gst': tk.StringVar(value='0.00')
        }
        
        # Create Entry widgets
        entry_widgets = {
            'serial': ttk.Entry(self.scrollable_frame, textvariable=row_vars['serial'], state='readonly', justify='center'),
            'product': ttk.Entry(self.scrollable_frame, textvariable=row_vars['product']),
            'packing': ttk.Entry(self.scrollable_frame, textvariable=row_vars['packing']),
            'batch_no': ttk.Entry(self.scrollable_frame, textvariable=row_vars['batch_no']),
            'qty': ttk.Entry(self.scrollable_frame, textvariable=row_vars['qty'], justify='right'),
            'free': ttk.Entry(self.scrollable_frame, textvariable=row_vars['free'], justify='right'),
            'rate': ttk.Entry(self.scrollable_frame, textvariable=row_vars['rate'], justify='right'),
            'gst': ttk.Entry(self.scrollable_frame, textvariable=row_vars['gst'], justify='right'),
            'val_excl_gst': ttk.Entry(self.scrollable_frame, textvariable=row_vars['val_excl_gst'], state='readonly', justify='right'),
            'val_incl_gst': ttk.Entry(self.scrollable_frame, textvariable=row_vars['val_incl_gst'], state='readonly', justify='right')
        }
        
        # Place widgets in the grid
        for i, key in enumerate(row_vars.keys()):
            entry_widgets[key].grid(row=row_num, column=i, sticky="nsew", padx=1, pady=1)

        # --- Bind Triggers for Automatic Calculation ---
        for key in ['qty', 'rate', 'gst']:
            # FIX: Simplified the callback to remove the confusing row_num parameter.
            # The update_totals function will now recalculate everything, which is more robust.
            row_vars[key].trace_add("write", lambda *args: self.update_totals())
            
        self.item_rows.append({'vars': row_vars, 'widgets': entry_widgets})
        self.update_totals() # Recalculate everything

    def remove_last_item_row(self):
        """Removes the last item row from the invoice."""
        if len(self.item_rows) > 1:
            last_row = self.item_rows.pop()
            for widget in last_row['widgets'].values():
                widget.destroy()
            self.update_totals()
        else:
            messagebox.showwarning("Warning", "Cannot remove the last item row.")
            
    def update_totals(self):
        """
        FIX: Rewritten for clarity and correctness.
        This function now iterates through all items, recalculates the values for each row,
        and then updates the grand totals. It is called whenever a relevant field is changed.
        """
        grand_total_excl_gst = 0.0
        grand_total_gst = 0.0
        
        for row in self.item_rows:
            try:
                qty = float(row['vars']['qty'].get() or 0)
                rate = float(row['vars']['rate'].get() or 0)
                gst_percent = float(row['vars']['gst'].get() or 0)

                # Calculate item values
                val_excl_gst = qty * rate
                gst_amount = val_excl_gst * (gst_percent / 100)
                val_incl_gst = val_excl_gst + gst_amount

                # Update row variables (which updates the UI)
                row['vars']['val_excl_gst'].set(f"{val_excl_gst:.2f}")
                row['vars']['val_incl_gst'].set(f"{val_incl_gst:.2f}")

                # Add to grand totals
                grand_total_excl_gst += val_excl_gst
                grand_total_gst += gst_amount

            except (ValueError, tk.TclError):
                # When a value is invalid (e.g., empty or text), reset the calculated fields for that row.
                # The grand total will be calculated correctly based on the other valid rows.
                row['vars']['val_excl_gst'].set("0.00")
                row['vars']['val_incl_gst'].set("0.00")

        grand_total_incl_gst = grand_total_excl_gst + grand_total_gst
        
        # Update grand total labels
        self.total_excl_gst_label.config(text=f"{grand_total_excl_gst:.2f}")
        self.total_gst_label.config(text=f"{grand_total_gst:.2f}")
        self.grand_total_label.config(text=f"{grand_total_incl_gst:.2f}")
        
    def _get_invoice_data(self):
        """Gathers all data from the UI fields and returns it in a structured dict."""
        invoice_data = {
            'doctor_name': self.doctor_name_entry.get(),
            'date': self.date_var.get(), # Get date from the variable
            'items': [],
            'total_excl_gst': self.total_excl_gst_label.cget("text"),
            'total_gst': self.total_gst_label.cget("text"),
            'grand_total': self.grand_total_label.cget("text")
        }

        for row in self.item_rows:
            item = {k: v.get() for k, v in row['vars'].items()}
            # Only add items with a product name
            if item['product']:
                invoice_data['items'].append(list(item.values()))
        
        return invoice_data
        
    def generate_pdf(self):
        """Generates a PDF file from the current invoice data."""
        data = self._get_invoice_data()
        
        if not data['doctor_name']:
            messagebox.showerror("Error", "Doctor's Name cannot be empty.")
            return
        if not data['items']:
            messagebox.showerror("Error", "Cannot generate a PDF with no items.")
            return

        # --- Ask user for save location ---
        folder_path = filedialog.askdirectory(title="Select a folder to save the PDF")
        if not folder_path: # User cancelled the dialog
            return
            
        safe_doctor_name = self.sanitize_filename(data['doctor_name'])
        filename = f"Invoice_{safe_doctor_name}_{data['date']}.pdf"
        print(folder_path)
        full_path = os.path.join(folder_path, filename)
        full_path = folder_path+'/'+filename
        print(full_path)
        
        doc = SimpleDocTemplate(full_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # --- PDF Title and Header ---
        elements.append(Paragraph("INVOICE", styles['h1']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # FIX: Create a table to position Doctor's Name on the left and Date on the top right.
        header_data = [
            [Paragraph(f"<b>Doctor's Name:</b> {data['doctor_name']}", styles['Normal']),
             Paragraph(f"<b>Date:</b> {data['date']}", styles['Normal'])]
        ]
        
        # Usable width is around 6.5 inches (8.5 inch page - 1 inch margin on each side)
        header_table = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT') # Align the second column (date) to the right
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.3 * inch))

        # --- PDF Items Table ---
        table_data = [
            ["S.No.", "Product Name", "Packing", "Batch No.", "Qty", "Free", "Rate", "GST(%)", "Value\n(Excl. GST)", "Value\n(Incl. GST)"]
        ]
        table_data.extend(data['items'])
        
        invoice_table = Table(table_data, colWidths=[0.4*inch, 2*inch, 0.8*inch, 0.8*inch, 0.4*inch, 0.4*inch, 0.5*inch, 0.6*inch, 0.8*inch, 0.8*inch])
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Align numeric columns to the right
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('PADDING', (4,1), (-1, -1), 4)
        ])
        invoice_table.setStyle(table_style)
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3 * inch))

        # --- PDF Totals Section ---
        totals_data = [
            ["Total (Excl. GST):", Paragraph(data['total_excl_gst'], styles['Normal'])],
            ["Total GST:", Paragraph(data['total_gst'], styles['Normal'])],
            [Paragraph("<b>Grand Total:</b>", styles['BodyText']), Paragraph(f"<b>{data['grand_total']}</b>", styles['BodyText'])]
        ]
        
        totals_table = Table(totals_data, colWidths=[1.6*inch, 1*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'), 
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        wrapper_table = Table([[totals_table]], colWidths=[7.4*inch])
        wrapper_table.setStyle(TableStyle([('ALIGN', (0,0), (0,0), 'RIGHT')]))

        elements.append(wrapper_table)
        
        try:
            doc.build(elements)
            self.last_pdf_path = full_path # Store the path of the successfully generated PDF
            messagebox.showinfo("Success", f"PDF '{filename}' generated successfully in\n{folder_path}")
        except PermissionError:
            messagebox.showerror("Error", f"Could not save PDF. Please close '{filename}' if it's open in another program and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

    def print_invoice(self):
        """Sends the last generated PDF to the default printer."""
        print("printing start")
        if not self.last_pdf_path or not os.path.exists(self.last_pdf_path):
            messagebox.showerror("Error", "No PDF found. Please generate the PDF first before printing.")
            return
            
        try:
            if sys.platform == "win32":
                print(self.last_pdf_path)
                os.startfile(self.last_pdf_path, "print")
            elif sys.platform == "darwin": # macOS
                os.system(f"lpr {self.last_pdf_path}")
            else: # Linux
                os.system(f"lp {self.last_pdf_path}")
            messagebox.showinfo("Printing", f"Sent '{os.path.basename(self.last_pdf_path)}' to the default printer.")
        except Exception as e:
            messagebox.showerror("Printing Error", f"Could not print the file. Please check your printer setup.\nError: {e}")
            
    # Add this method inside the InvoiceApp class
    def sanitize_filename(self, name):
        """Removes characters that are illegal in filenames."""
        # Characters that are invalid in Windows filenames
        invalid_chars = '<>:"/\\|?*'
        # Replace spaces with underscores first
        safe_name = name.replace(' ', '_')
        # Remove any remaining invalid characters
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '')        
            return safe_name
    



if __name__ == "__main__":
    app = InvoiceApp()
    app.mainloop()

