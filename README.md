# 🚀 UniUni Batch Clearance Automation

**An automated solution for high-volume logistics order processing.**

## 📖 Overview

This project is a high-performance automation tool designed to streamline the internal "Daily Clearance" workflow. By leveraging **Python** and **Playwright**, it replaces manual data entry with a concurrent "worker" system capable of handling **40,000+ orders** in a single run.

The application features a user-friendly **Streamlit** interface that allows users to upload Excel datasets, configure concurrency levels, and monitor real-time progress.

## ✨ Key Features

* **⚡ High Concurrency:** Utilizes `ThreadPoolExecutor` to launch multiple browser instances (Workers) simultaneously, reducing processing time by up to 90%.
* **🤖 Automated Queue System:** Automatically splits massive datasets (e.g., 40k rows) into manageable batches (e.g., 500 rows) and dispatches them to available workers.
* **🛡️ Robust Validation:** Includes intelligent validation logic that waits for server-side confirmation ("External API Processed") before marking a batch as successful.
* **📂 Excel Integration:** Drag-and-drop support for `.xlsx` files, with automatic detection of the `TNO` (Tracking Number) column.
* **⏱️ Smart Retry & Long-Wait:** Engineered to handle slow server responses with extended timeouts (up to 20 minutes per batch) and auto-retry mechanisms for network fluctuations.

## 🛠️ Tech Stack

* **Language:** Python 3.10+
* **UI Framework:** [Streamlit](https://streamlit.io/)
* **Automation:** [Playwright](https://playwright.dev/)
* **Data Handling:** Pandas, OpenPyXL
* **Concurrency:** Python `concurrent.futures`

## 🚀 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/czb135/auto_dispatcher.git
    cd uniuni-batch-tool
    ```

2.  **Install dependencies**
    Create a `requirements.txt` file (if not exists) and install:
    ```bash
    pip install streamlit pandas playwright openpyxl
    ```

3.  **Install Playwright browsers**
    ```bash
    playwright install
    ```

## 💻 How to Run

1.  **Start the application**
    Run the following command in your terminal:
    ```bash
    streamlit run auto_dispatcher_v4.py
    ```
    *(Note: Replace `auto_dispatcher_v4.py` with your actual script name)*

2.  **Configure Settings (Sidebar)**
    * **Concurrent Workers:** Recommended **3-5** for standard laptops.
    * **Batch Size:** Recommended **500** orders per batch.
    * **Visible Mode:** Uncheck to run in "Headless Mode" (faster background execution).

3.  **Upload Data**
    * Upload your `.xlsx` file.
    * Ensure the file has a column named **`TNO`** containing the order numbers.

4.  **Start Processing**
    * Click the **"Start Processing"** button.
    * Watch the progress bar and real-time logs.

## ⚠️ Important Notes for Mac Users

To prevent the script from pausing when your Mac goes to sleep or the screen turns off, please use the `caffeinate` command.

**Before running Streamlit, open a terminal and run:**

```bash
caffeinate -d