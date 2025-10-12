🧾 Simple Invoice Generator
A user-friendly desktop application built with Python and Tkinter for creating, managing, and printing simple invoices. It automatically calculates totals, including GST, and generates a professional PDF.

✨ Features
Intuitive Interface: A clean and straightforward GUI for easy invoice creation.

Dynamic Item List: Add or remove product/service rows as needed.

Automatic Calculation: Real-time updates for item values, sub-totals, GST amounts, and the grand total as you type.

PDF Generation: Create a clean, professional-looking PDF of your invoice with a single click.

Direct Printing: Send the generated PDF directly to your default printer.

Date Picker: A convenient calendar widget to easily select the invoice date.

Cross-Platform: Works on Windows, macOS, and Linux.

🛠️ Setup and Installation
Follow these steps to get the application running on your local machine.

Prerequisites
Python 3.x: Make sure you have Python 3 installed. You can download it from python.org.

Installation Steps
Download the Code
Clone this repository or download the source code files to a folder on your computer.

Create a Virtual Environment (Recommended)
It's best practice to create a virtual environment to manage project dependencies. Open your terminal or command prompt in the project folder and run:

On macOS/Linux:

Bash

python3 -m venv venv
source venv/bin/activate
On Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
Install Required Libraries
The application requires two external libraries: reportlab for PDF generation and tkcalendar for the date picker widget. The script will alert you if they are missing, but you can install them manually.

Install them using pip:

Bash

pip install reportlab tkcalendar
🚀 How to Run
Once the setup is complete, run the application from your terminal with the following command:

Bash

python your_script_name.py 
(Replace your_script_name.py with the actual name of the Python file).

The application window will appear, ready for you to create an invoice.

📝 Using the Application
Enter Header Details: Fill in the Doctor's Name (or any other recipient/client name) and select the Date using the calendar icon (📅).

Add Invoice Items:

Fill in the details for each item in a row: Product Name, Packing, Batch No., Qty, Rate, and GST (%).

The Value (Excl. GST) and Value (Incl. GST) fields for each item will update automatically.

Manage Items:

Click the Add Item button to add a new blank row.

Click the Remove Last Item button to delete the last row in the list.

Review Totals: The total amounts at the bottom right will update in real-time as you add or modify items.

Generate a PDF:

Click the Generate PDF button.

A dialog will ask you to select a folder where you want to save the invoice.

The PDF will be saved with a filename like Invoice_DoctorsName_dd-mm-yyyy.pdf.

Print the Invoice:

After generating a PDF, click the Print Invoice button.

This will send the most recently generated PDF directly to your system's default printer.
