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
        self.geometry("1200x750")
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
        self.discount_percent_var = tk.StringVar(value='0') # Global Discount Variable
        
        self._create_widgets()
        self.add_item_row() # Start with one empty item row
        
        # NEW BINDING: Trigger recalculation when global discount changes
        self.discount_percent_var.trace_add("write", lambda *args: self.update_totals())

    def _create_widgets(self):
        """Creates and places all the widgets in the main window."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(1, weight=1) 
        main_frame.columnconfigure(0, weight=1) 

        # --- Header Section (Doctor Name, Date) ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.date_button = ttk.Button(header_frame, text="📅", command=self._open_calendar, width=3)
        self.date_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.date_var = tk.StringVar(value=date.today().strftime('%d-%m-%Y'))
        self.date_entry = ttk.Entry(header_frame, textvariable=self.date_var, width=12, justify='center')
        self.date_entry.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(header_frame, text="Date:", font=("Helvetica", 11, "bold")).pack(side=tk.RIGHT, padx=(20, 5))

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

        # --- Footer Section (Global Discount, Totals and Buttons) ---
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=2, column=0, sticky="ew", pady=10)

        # Left Side - Action Buttons & GLOBAL DISCOUNT
        left_footer_frame = ttk.Frame(footer_frame)
        left_footer_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 1. Action Buttons
        button_frame = ttk.Frame(left_footer_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.add_item_btn = ttk.Button(button_frame, text="Add Item", command=self.add_item_row)
        self.add_item_btn.pack(side=tk.LEFT, padx=5)

        self.remove_item_btn = ttk.Button(button_frame, text="Remove Last Item", command=self.remove_last_item_row)
        self.remove_item_btn.pack(side=tk.LEFT, padx=5)
        
        # 2. Global Discount Input (Bottom Left)
        discount_input_frame = ttk.Frame(left_footer_frame)
        discount_input_frame.pack(fill=tk.X, anchor='w')
        
        ttk.Label(discount_input_frame, text="Global Discount (%):", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.discount_entry = ttk.Entry(discount_input_frame, textvariable=self.discount_percent_var, width=10, justify='right')
        self.discount_entry.pack(side=tk.LEFT, padx=5)


        # Right Side - Totals Display
        totals_frame = ttk.Frame(footer_frame)
        totals_frame.pack(side=tk.RIGHT)

        ttk.Label(totals_frame, text="Subtotal (Excl. Disc/GST):", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5)
        self.subtotal_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.subtotal_label.grid(row=0, column=1, sticky="w", padx=5)
        
        # Discount Label
        ttk.Label(totals_frame, text="Discount Amount:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky="e", padx=5)
        self.total_discount_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.total_discount_label.grid(row=1, column=1, sticky="w", padx=5)
        
        # Taxable Amount
        ttk.Label(totals_frame, text="Taxable Amount:", font=("Helvetica", 10, "bold")).grid(row=2, column=0, sticky="e", padx=5)
        self.total_excl_gst_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.total_excl_gst_label.grid(row=2, column=1, sticky="w", padx=5)
        
        ttk.Label(totals_frame, text="Total GST Amount:", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky="e", padx=5)
        self.total_gst_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 10))
        self.total_gst_label.grid(row=3, column=1, sticky="w", padx=5)

        ttk.Label(totals_frame, text="Grand Total (Incl. GST):", font=("Helvetica", 12, "bold")).grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.grand_total_label = ttk.Label(totals_frame, text="0.00", font=("Helvetica", 12, "bold"))
        self.grand_total_label.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # --- PDF/Print Action Bar ---
        action_bar = ttk.Frame(main_frame, padding=10)
        action_bar.grid(row=3, column=0, sticky="ew")
        
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
        
        for widget in self.scrollable_frame.winfo_children():
            if widget.grid_info().get('row') == 0:
                widget.destroy()

        for i, header in enumerate(headers):
            label = ttk.Label(self.scrollable_frame, text=header, style="Header.TLabel", borderwidth=1, relief="solid", padding=5, anchor="center")
            label.grid(row=0, column=i, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=column_widths[i]*5) 

    def add_item_row(self):
        """Adds a new row of entry fields for an invoice item."""
        row_num = len(self.item_rows) + 1
        
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
        
        item_keys_order = ['serial', 'product', 'packing', 'batch_no', 'qty', 'free', 'rate', 'gst', 'val_excl_gst', 'val_incl_gst']
        
        for i, key in enumerate(item_keys_order):
            if key in entry_widgets:
                entry_widgets[key].grid(row=row_num, column=i, sticky="nsew", padx=1, pady=1)

        for key in ['qty', 'rate', 'gst']:
            row_vars[key].trace_add("write", lambda *args: self.update_totals())
            
        self.item_rows.append({'vars': row_vars, 'widgets': entry_widgets})
        self.update_totals()

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
        Calculates item values and applies a Global Discount before calculating final totals.
        """
        # --- 1. Calculate Subtotal (Pre-Discount) ---
        subtotal_pre_discount = 0.0
        total_gst_amount_sum = 0.0
        
        for row in self.item_rows:
            try:
                qty = float(row['vars']['qty'].get() or 0)
                rate = float(row['vars']['rate'].get() or 0)
                gst_percent = float(row['vars']['gst'].get() or 0)

                # Base Value (Excl. GST & Discount)
                item_val_excl_gst = qty * rate
                
                # Item GST calculation 
                item_gst_amount = item_val_excl_gst * (gst_percent / 100)
                
                item_val_incl_gst = item_val_excl_gst + item_gst_amount

                # Update row variables (which updates the UI)
                row['vars']['val_excl_gst'].set(f"{item_val_excl_gst:.2f}")
                row['vars']['val_incl_gst'].set(f"{item_val_incl_gst:.2f}")

                # Accumulate for Subtotal
                subtotal_pre_discount += item_val_excl_gst
                total_gst_amount_sum += item_gst_amount
                
            except (ValueError, tk.TclError):
                row['vars']['val_excl_gst'].set("0.00")
                row['vars']['val_incl_gst'].set("0.00")

        # --- 2. Apply Global Discount ---
        try:
            discount_percent = float(self.discount_percent_var.get() or 0)
            if discount_percent < 0: discount_percent = 0
        except ValueError:
            discount_percent = 0.0
            
        # Calculate Discount Amount
        discount_amount = subtotal_pre_discount * (discount_percent / 100)
        
        # Calculate Taxable Amount (Subtotal after Discount)
        taxable_amount = subtotal_pre_discount - discount_amount
        
        # Recalculate GST based on the taxable amount using the effective average rate
        if subtotal_pre_discount > 0:
            effective_gst_rate = total_gst_amount_sum / subtotal_pre_discount
        else:
            effective_gst_rate = 0
            
        final_gst_amount = taxable_amount * effective_gst_rate
        
        # --- 3. Calculate Final Totals ---
        grand_total_incl_gst = taxable_amount + final_gst_amount
        
        # --- 4. Update UI Labels ---
        self.subtotal_label.config(text=f"{subtotal_pre_discount:.2f}") # Pre-discount subtotal
        self.total_discount_label.config(text=f"{discount_amount:.2f}") # Discount amount
        self.total_excl_gst_label.config(text=f"{taxable_amount:.2f}") # Taxable amount (After Discount)
        self.total_gst_label.config(text=f"{final_gst_amount:.2f}")
        self.grand_total_label.config(text=f"{grand_total_incl_gst:.2f}")
        
    def _get_invoice_data(self):
        """Gathers all data from the UI fields and returns it in a structured dict."""
        invoice_data = {
            'doctor_name': self.doctor_name_entry.get(),
            'date': self.date_var.get(), 
            'items': [],
            # Global Discount Data
            'discount_percent': self.discount_percent_var.get() or '0', 
            'subtotal': self.subtotal_label.cget("text"),
            'total_discount': self.total_discount_label.cget("text"),
            'taxable_amount': self.total_excl_gst_label.cget("text"), 
            'total_gst': self.total_gst_label.cget("text"),
            'grand_total': self.grand_total_label.cget("text")
        }

        item_keys_for_pdf = ['serial', 'product', 'packing', 'batch_no', 'qty', 'free', 'rate', 'gst', 'val_excl_gst', 'val_incl_gst']

        for row in self.item_rows:
            item_values = [row['vars'][key].get() for key in item_keys_for_pdf]
            
            if row['vars']['product'].get():
                invoice_data['items'].append(item_values)
        
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
        if not folder_path:
            return
            
        safe_doctor_name = self.sanitize_filename(data['doctor_name'])
        filename = f"Invoice_{safe_doctor_name}_{data['date']}.pdf"
        full_path = os.path.join(folder_path, filename)
        
        doc = SimpleDocTemplate(full_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # --- PDF Title and Header ---
        elements.append(Paragraph("INVOICE", styles['h1']))
        elements.append(Spacer(1, 0.2 * inch))
        
        header_data = [
            [Paragraph(f"<b>Doctor's Name:</b> {data['doctor_name']}", styles['Normal']),
             Paragraph(f"<b>Date:</b> {data['date']}", styles['Normal'])]
        ]
        
        header_table = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT') 
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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Global alignment for all text in table to CENTER/MIDDLE
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Override alignment for specific columns that should be RIGHT (numerical values)
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'), 
            ('PADDING', (4,1), (-1, -1), 4)
        ])
        invoice_table.setStyle(table_style)
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3 * inch))

        # --- PDF Totals Section with Discount (FIXED ALIGNMENT) ---
        
        discount_percent = float(data['discount_percent'])
        discount_display = f"{discount_percent:.0f}%" if discount_percent > 0 else ""
            
        # REVISED: Use raw strings for non-bold items and Paragraphs only for bolding
        # This ensures consistent cell content for TableStyle commands.
        totals_data = [
            ["Subtotal (Pre-Discount):", data['subtotal']], 
            # Use Paragraph for bolding the Discount row
            [Paragraph(f"<b>Discount ({discount_display}):</b>", styles['BodyText']), Paragraph(f"<b>-{data['total_discount']}</b>", styles['BodyText'])],
            ["Taxable Amount (Excl. GST):", data['taxable_amount']],
            ["Total GST:", data['total_gst']],
            # Use Paragraph for bolding the Grand Total row
            [Paragraph("<b>Grand Total:</b>", styles['BodyText']), Paragraph(f"<b>{data['grand_total']}</b>", styles['BodyText'])]
        ]

        totals_table = Table(totals_data, colWidths=[2.2*inch, 1*inch])
        totals_table.setStyle(TableStyle([
            # Enforce right alignment for ALL content in the first column (labels)
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            # Enforce right alignment for ALL content in the second column (values)
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'), 
            # Enforce MIDDLE vertical alignment for ALL content
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
            
            # Apply BOLD font name specifically to Discount and Grand Total rows
            ('FONTNAME', (0, 1), (1, 1), 'Helvetica-Bold'), # Discount Row (Row index 1)
            ('FONTNAME', (0, 4), (1, 4), 'Helvetica-Bold'), # Grand Total Row (Row index 4)

            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        wrapper_table = Table([[totals_table]], colWidths=[7.4*inch])
        wrapper_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'RIGHT')
        ]))

        elements.append(wrapper_table)
        
        try:
            doc.build(elements)
            self.last_pdf_path = full_path
            messagebox.showinfo("Success", f"PDF '{filename}' generated successfully in\n{folder_path}")
        except PermissionError:
            messagebox.showerror("Error", f"Could not save PDF. Please close '{filename}' if it's open in another program and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

    def print_invoice(self):
        """Sends the last generated PDF to the default printer."""
        if not self.last_pdf_path or not os.path.exists(self.last_pdf_path):
            messagebox.showerror("Error", "No PDF found. Please generate the PDF first before printing.")
            return
            
        try:
            if sys.platform == "win32":
                os.startfile(self.last_pdf_path, "print")
            elif sys.platform == "darwin": # macOS
                os.system(f"lpr {self.last_pdf_path}")
            else: # Linux
                os.system(f"lp {self.last_pdf_path}")
            messagebox.showinfo("Printing", f"Sent '{os.path.basename(self.last_pdf_path)}' to the default printer.")
        except Exception as e:
            messagebox.showerror("Printing Error", f"Could not print the file. Please check your printer setup.\nError: {e}")
            
    def sanitize_filename(self, name):
        """Removes characters that are illegal in filenames."""
        invalid_chars = '<>:"/\\|?*'
        safe_name = name.replace(' ', '_')
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '')         
        return safe_name
    

if __name__ == "__main__":
    app = InvoiceApp()
    app.mainloop()