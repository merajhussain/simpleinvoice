# 🚀 Release Notes - Version 2.0 (The Discount Update)

**Release Date: October 28, 2025**

This major update introduces the ability to apply a single, comprehensive discount to the entire invoice and fixes alignment issues in the generated PDF for a cleaner, more professional final document.

## ✨ New Features

### Global Discount Implementation
* **Feature:** A new input field for "Global Discount (%)" has been added to the bottom-left of the application interface.
* **Functionality:** The entered percentage is applied to the calculated subtotal (pre-GST), and the resulting discount amount is dynamically reflected in the totals summary.
* **Calculation:** GST is now correctly calculated on the **taxable amount** (Subtotal minus Discount), ensuring financial accuracy.

## ✅ Bug Fixes & Improvements

### PDF Rendering Fixes
* **Alignment Correction:** Resolved alignment issues in the PDF totals summary table. The Discount and Grand Total fields are now perfectly right-aligned with all other currency values.
* **Consistency:** Implemented uniform vertical and horizontal alignment across all item and totals tables for a professional look.