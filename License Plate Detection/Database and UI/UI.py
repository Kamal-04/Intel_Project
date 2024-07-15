import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from database import ParkingArea
import sqlite3 as sql
import numpy as np

#st.set_page_config(layout="wide")

st.title("Parking Area Management System")

# Upload CSV files
customer_data_file = st.file_uploader("Upload Customer Data CSV", type=["csv"])
data_file = st.file_uploader("Upload Parking Data CSV", type=["csv"])

if customer_data_file is not None and data_file is not None:
    # Read CSV files
    customer_data = pd.read_csv(customer_data_file)
    data = pd.read_csv(data_file)
    
    # Initialize ParkingArea object
    parking_area = ParkingArea("MyParking2", 40)  # You can adjust the parameters as needed
    
    # Process customer data
    cust_id = customer_data['car_id']
    cust_number = customer_data['car_number']

    for i in range(len(cust_id)):
        id = cust_id[i]
        number = cust_number[i]
        parking_area.customer_data_entry(id, number)
    
    # Process parking data
    vehicle_id = data['vehicle_id']
    vehicle_number = data['vehicle_license_plate']
    entry_time_data = pd.to_datetime(data['entry_time'])
    exit_time_data = pd.to_datetime(data['exit_time'])
    date_data = pd.to_datetime(data['date']).dt.date

    for i in range(len(vehicle_id)):   
        id = vehicle_id[i] 
        number = vehicle_number[i]
        entry = entry_time_data[i].strftime('%H:%M:%S')
        exit = exit_time_data[i].strftime('%H:%M:%S')
        dt = date_data[i].strftime('%Y-%m-%d')

        cmd = f"SELECT * FROM {parking_area.parked_table_name} WHERE Car_Number = '{number}'"
        check = parking_area.db_cur.execute(cmd).fetchall()

        if len(check) == 0:
            ret = parking_area.entry(number, dt, entry)
        else:
            ret = parking_area.exit(number, exit)

        # Commit the transaction
        parking_area._db.commit()
        
        # Just for dummy dataset
        if i == len(vehicle_id) - 1:
            parking_area.daily_average(dt)
    
    st.success("Data has been successfully uploaded and processed.")

    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Data Upload", "Summary", "Visualizations"])

    with tab1:
        st.header("Data Upload")
        
        st.write("Customer Data")
        st.write(customer_data)
        
        st.write("Parking Data")
        st.write(data)

        if st.button('Show Parking Records'):
            try:
                # Connect to the database
                conn = sql.connect(parking_area._db_name)
                query = f"SELECT * FROM {parking_area.record_table_name}"
                record_df = pd.read_sql_query(query, conn)
                conn.close()
                
                st.write("Parking Records")
                st.write(record_df)
            except Exception as e:
                st.error(f"Error fetching records: {e}")

    with tab2:
        st.header("Summary")
        st.write(f"Total Capacity: {parking_area.total_capacity}")
        st.write(f"Average Occupancy: {parking_area.avg_occupancy:.2f}%")
        st.write(f"Newly Visiting Count: {sum(parking_area.daily_new_visiting.values())}")

        st.write("Daily Slot Averages")
        daily_slot_average_df = pd.DataFrame(list(parking_area.daily_slot_average.items()), columns=['Date', 'Average'])
        st.table(daily_slot_average_df)

        st.write("Daily Slot Counts")
        daily_slot_count_df = pd.DataFrame(list(parking_area.daily_slot_count.items()), columns=['Date', 'Count'])
        st.table(daily_slot_count_df)

        st.write("Slot Unavailable Counts")
        daily_slot_unavailable_df = pd.DataFrame(list(parking_area.slot_unavailable_count.items()), columns=['Date', 'Unavailable Count'])
        st.table(daily_slot_unavailable_df)

        st.write("Daily New Visiting")
        daily_slot_new_df = pd.DataFrame(list(parking_area.daily_new_visiting.items()), columns=['Date', 'Count'])
        st.table(daily_slot_new_df)

    with tab3:
        st.header("Visualizations")
        
        st.subheader('Distribution of Duration of Stay')
        data['duration_minutes'] = (exit_time_data - entry_time_data).dt.total_seconds() / 60
        fig, ax = plt.subplots()
        sns.histplot(data['duration_minutes'], kde=True, ax=ax)
        ax.set_title('Distribution of Duration of Stay')
        ax.set_xlabel('Duration (minutes)')
        ax.set_ylabel('Frequency')
        st.pyplot(fig)
        
        st.subheader('Vehicle Frequency')
        fig, ax = plt.subplots()
        data['vehicle_license_plate'].value_counts().plot(kind='bar', ax=ax)
        ax.set_title('Vehicle Frequency')
        ax.set_xlabel('Vehicle License Plate')
        ax.set_ylabel('Frequency')
        st.pyplot(fig)

        st.subheader('Duration Distribution')
        fig, ax = plt.subplots()
        sns.boxplot(x='duration_minutes', data=data, ax=ax)
        ax.set_title('Duration Distribution')
        ax.set_xlabel('Duration (minutes)')
        st.pyplot(fig)

        st.subheader('Entry/Exit Patterns')
        fig, ax = plt.subplots(figsize=(10, 6))
        entry_exit_patterns = pd.crosstab(entry_time_data.dt.hour, exit_time_data.dt.hour)
        sns.heatmap(entry_exit_patterns, annot=True, fmt='.1f', cmap='viridis', ax=ax)
        ax.set_title('Entry/Exit Patterns')
        ax.set_xlabel('Exit Hour')
        ax.set_ylabel('Entry Hour')
        st.pyplot(fig)

    
        st.subheader('Peak Entry and Exit Times')
        fig, ax = plt.subplots()
        sns.histplot(entry_time_data.dt.hour, bins=24, kde=True, color='blue', label='Entry Time', ax=ax)
        sns.histplot(exit_time_data.dt.hour, bins=24, kde=True, color='red', label='Exit Time', ax=ax)
        ax.set_title('Peak Entry and Exit Times')
        ax.set_xlabel('Hour of the Day')
        ax.set_ylabel('Frequency')
        ax.legend()
        st.pyplot(fig)           

        st.subheader('Utilization Rates by Hour')
        fig, ax = plt.subplots()
        entry_time_data.dt.hour.value_counts().sort_index().plot(kind='bar', ax=ax)
        ax.set_title('Utilization Rates by Hour')
        ax.set_xlabel('Hour of the Day')
        ax.set_ylabel('Number of Entries')
        st.pyplot(fig)

        st.subheader('Average Stay per Day')
        data['duration'] = exit_time_data - entry_time_data
        average_stay_per_day = data.groupby('date')['duration'].mean().dt.total_seconds() / 3600
        fig, ax = plt.subplots()
        average_stay_per_day.plot(kind='bar', ax=ax)
        ax.set_title('Average Stay per Day')
        ax.set_xlabel('Date')
        ax.set_ylabel('Average Duration (hours)')
        st.pyplot(fig)

        

        st.subheader('Average Time Between Visits')
        data['entry_time'] = pd.to_datetime(data['entry_time'])
        fig, ax = plt.subplots()
        avg_time_between_visits = data.groupby('vehicle_license_plate')['entry_time'].apply(lambda x: x.diff().mean())
        avg_time_between_visits = avg_time_between_visits.dt.total_seconds() / 3600
        avg_time_between_visits.plot(kind='bar', ax=ax)
        ax.set_title('Average Time Between Visits')
        ax.set_xlabel('Vehicle License Plate')
        ax.set_ylabel('Average Time Between Visits (hours)')
        st.pyplot(fig)

        st.subheader('Daily Trends of Vehicle Entries and Exits')
        fig, ax = plt.subplots()
        data['date'] = pd.to_datetime(data['date']).dt.date
        data['date'].value_counts().sort_index().plot(kind='bar', ax=ax)
        ax.set_title('Daily Trends of Vehicle Entries and Exits')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Entries/Exits')
        st.pyplot(fig)

        st.subheader('Vehicles Per Hour')
        fig, ax = plt.subplots()
        entry_time_data.dt.hour.value_counts().sort_index().plot(kind='bar', ax=ax)
        ax.set_title('Vehicles Per Hour')
        ax.set_xlabel('Hour of the Day')
        ax.set_ylabel('Number of Vehicles')
        st.pyplot(fig)

        st.subheader('Recurrent Visitors')
        fig, ax = plt.subplots()
        data['vehicle_license_plate'].value_counts().loc[lambda x: x > 1].plot(kind='bar', ax=ax)
        ax.set_title('Recurrent Visitors')
        ax.set_xlabel('Vehicle License Plate')
        ax.set_ylabel('Number of Visits')
        st.pyplot(fig)            

        st.subheader('Average Newly Coming Visitors')
        new_visitors = data[~data['vehicle_license_plate'].isin(customer_data['car_number'])]
        avg_new_visitors = new_visitors.groupby('date').size().mean()
        st.write(f"Average Newly Coming Visitors: {avg_new_visitors:.2f} per day")
