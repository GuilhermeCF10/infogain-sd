#!/usr/bin/env python3
# ETL Script for Dental Analytics
# This script loads the raw CSV data into MySQL and executes the transformation queries

import os
import pandas as pd
import mysql.connector
import time
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables from .env file
load_dotenv()

# MySQL connection configurations from environment variables
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'localhost'),
    'port': int(os.getenv('DATABASE_PORT', 3306)),
    'user': os.getenv('DATABASE_USER', 'root'),
    'password': os.getenv('DATABASE_PASSWORD', 'root'),
    'database': os.getenv('DATABASE_NAME', 'dental_analytics'),
    'allow_local_infile': True
}

def execute_sql_file(cursor, sql_file_path):
    """Execute a SQL file on the MySQL database"""
    print(f"Executing SQL file: {sql_file_path}")
    
    # Read SQL commands from file
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()
    
    # Split into individual statements (respecting delimiters for stored procedures)
    delimiter = ';'
    in_procedure = False
    current_statement = []
    statements = []
    
    for line in sql_content.splitlines():
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--') or line.startswith('#'):
            continue
            
        # Check for delimiter change
        if line.upper().startswith('DELIMITER'):
            if in_procedure:
                statements.append('\n'.join(current_statement))
                current_statement = []
            
            delimiter = line.split()[1]
            in_procedure = (delimiter != ';')
            continue
            
        # Add line to current statement
        current_statement.append(line)
        
        # Check if statement is complete
        if line.endswith(delimiter):
            if delimiter != ';':
                if 'END' + delimiter in line:
                    in_procedure = False
                    delimiter = ';'
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            else:
                statements.append('\n'.join(current_statement))
                current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    # Execute each statement
    for i, statement in enumerate(statements):
        if statement.strip():
            try:
                cursor.execute(statement)
                print(f"Statement {i+1}/{len(statements)} executed successfully")
            except mysql.connector.Error as err:
                print(f"Error executing statement {i+1}: {err}")
                print(f"Statement: {statement[:150]}...")
    
    # Commit changes
    cursor.execute("COMMIT;")
    print(f"SQL file {sql_file_path} executed successfully")

def initialize_database():
    """Initialize the database and tables structure"""
    try:
        # Connect to MySQL server
        cnx = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            allow_local_infile=True
        )
        cursor = cnx.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database {DB_CONFIG['database']} created or already exists")
        
        # Switch to the database
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Execute create database script to set up table structure
        create_db_script = './sql/01_create_database.sql'
        execute_sql_file(cursor, create_db_script)
        
        # Close connection
        cursor.close()
        cnx.close()
        
        print("Database structure initialized successfully")
        return True
    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")
        return False

def load_raw_data(csv_path='./raw_dental.csv'):
    """Load raw CSV data into MySQL database directly using pandas and SQLAlchemy"""
    try:
        # Create SQLAlchemy engine
        connection_string = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string, connect_args={'allow_local_infile': True})
        
        # Check if table already has data
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM raw_dental"))
            count = result.scalar()
        
        if count > 0:
            print(f"Table raw_dental already contains {count} rows. Skipping data load.")
        else:
            print(f"Loading data from {csv_path}...")
            # Load data with Pandas
            df = pd.read_csv(csv_path, sep=';')
            print(f"Read {len(df)} rows from CSV file")
            
            # Clean column names (lowercase, strip whitespace, fix specific known issues)
            df.columns = df.columns.str.strip().str.lower()
            # Specifically rename the problematic column if it exists after stripping/lowercasing
            if 'txmt_user_ annotation_code' in df.columns:
                df.rename(columns={'txmt_user_ annotation_code': 'txmt_user_annotation_code'}, inplace=True)
            print("Cleaned DataFrame column names.")

            # Insert data directly using pandas to_sql
            df.to_sql('raw_dental', engine, if_exists='append', index=False, 
                      chunksize=1000, method='multi')
            
            print(f"Loaded {len(df)} rows into raw_dental table")
        
        return True
    except Exception as e:
        print(f"Error loading raw data: {e}")
        return False

def execute_transformations():
    """Execute all transformation SQL files"""
    try:
        # Connect to database
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor(buffered=True)
        
        # Start a transaction
        print("\nStarting transaction for data transformations...")
        cursor.execute("START TRANSACTION;")
        
        # Execute raw to trusted transformation
        print("\nTransforming data from raw to trusted layer...")
        raw_to_trusted_path = './sql/02_raw_to_trusted.sql'
        execute_sql_file(cursor, raw_to_trusted_path)
        
        # Execute trusted to refined transformation
        print("\nTransforming data from trusted to refined layer...")
        trusted_to_refined_path = './sql/03_trusted_to_refined.sql'
        execute_sql_file(cursor, trusted_to_refined_path)
        
        # Commit all transformations at once
        print("\nCommitting all transformations...")
        cnx.commit()
        print("Transaction committed successfully")
        
        # Close connection
        cursor.close()
        cnx.close()
        
        return True
    except Exception as e:
        print(f"Error executing transformations: {e}")
        try:
            # Rollback the transaction in case of error
            print("Rolling back transaction due to error...")
            cnx.rollback()
            print("Transaction rolled back successfully")
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}")
        return False

def main():
    start_time = time.time()
    print("\n=== Starting Dental Analytics ETL Process ===\n")
    
    # Step 1: Initialize database (create structure)
    print("\n--- Step 1: Initializing Database Structure ---")
    if not initialize_database():
        sys.exit("Failed to initialize database structure")
    
    # Step 2: Load raw data from CSV
    print("\n--- Step 2: Loading Raw Data from CSV ---")
    if not load_raw_data('./raw_dental.csv'):
        sys.exit("Failed to load raw data")
    
    # Step 3: Execute transformations (raw to trusted, trusted to refined)
    print("\n--- Step 3: Executing Data Transformations ---")
    if not execute_transformations():
        sys.exit("Failed to execute transformations")
    
    end_time = time.time()
    print(f"\n=== ETL Process Completed Successfully in {end_time - start_time:.2f} seconds! ===\n")

if __name__ == "__main__":
    main()
