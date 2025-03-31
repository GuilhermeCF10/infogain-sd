#!/bin/bash

# Display header
echo "================================================"
echo "  Dental Analytics Solution - Initialization    "
echo "================================================"
echo ""

# Activate conda environment
echo "Activating conda environment 'infogain'..."
eval "$(conda shell.bash hook)"
conda activate infogain

if [ $? -ne 0 ]; then
    echo "Error activating conda environment 'infogain'."
    echo "Make sure the environment was created with:"
    echo "  conda create --name infogain python=3.12"
    exit 1
fi

echo "Conda environment 'infogain' activated successfully!"
echo ""

# Execute ETL process for loading data into MySQL
echo "Running ETL process..."
python3 etl.py

# Check if ETL was successful
if [ $? -ne 0 ]; then
    echo "Error executing ETL. Check the logs above."
    exit 1
fi

echo "ETL completed successfully!"
echo ""

# Start Streamlit application
echo "Starting Streamlit dashboard..."
echo ""
echo "Dashboard is going to be available at: http://localhost:8501"
streamlit run app/app.py