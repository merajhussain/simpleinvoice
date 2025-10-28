# 🧾 Simple Invoice Generator - v2.0

A user-friendly desktop application built with Python and Tkinter for creating, managing, and printing simple invoices. This version introduces **global discounting** and improved PDF alignment.

-----

## ✨ Features (v2.0 Updates)

 * **Intuitive Interface**: A clean and straightforward GUI for easy invoice creation.
 * **Dynamic Item List**: Add or remove product/service rows as needed.
 * **Automatic Calculation**: Real-time updates for item values, sub-totals, GST amounts, and the grand total as you type.
 * **NEW: Global Invoice Discount**: Apply a single percentage discount to the entire invoice subtotal, which is correctly factored into the final GST and Grand Total calculation.
 * **PDF Generation**: Create a clean, professional-looking PDF of your invoice with a single click.
 * **IMPROVED: PDF Alignment**: Fixed alignment issues in the PDF totals section, ensuring the discount and grand total fields are perfectly aligned with other totals.
 * **Direct Printing**: Send the generated PDF directly to your default printer.
 * **Date Picker**: A convenient calendar widget to easily select the invoice date.
 * **Cross-Platform**: Works on Windows, macOS, and Linux.

-----

## 🛠️ Setup and Installation

Follow these steps to get the application running on your local machine.

### Prerequisites

 * **Python 3.x**: Make sure you have Python 3 installed. You can download it from [python.org](https://www.python.org/).

### Installation Steps

1.  **Download the Code**
    Clone the repository or download the source code files to a folder on your computer.

2.  **Create a Virtual Environment (Recommended)**
    It's best practice to create a virtual environment to manage project dependencies. Open your terminal or command prompt in the project folder and run:

    * **On macOS/Linux:**
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    * **On Windows:**
      ```bash
      python -m venv venv
      .\venv\Scripts\activate
      ```

3.  **Install Required Libraries**
    The application requires `reportlab` for PDF generation and `tkcalendar` for the date picker widget. The script will alert you if they are missing, but you can install them manually.

    Install them using pip:

    ```bash
    pip install reportlab tkcalendar
    ```

-----

## 🚀 How to Run

Once the setup is complete, run the application from your terminal with the following command (replace `your_script_name.py` with the actual name of the Python file):

```bash
python your_script_name.py