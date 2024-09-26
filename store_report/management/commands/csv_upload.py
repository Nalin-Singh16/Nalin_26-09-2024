from django.core.management.base import BaseCommand
import csv
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from datetime import datetime, timezone  # Use Python's built-in timezone module for UTC
from store_report.models import BusinessHours, StoreStatus, StoreTimezone

def store_status_to_db():
    csv_file_path = 'data/store status.csv' 
    batch_size = 1000
    store_status_list = []
    rows_processed = 0

    with open(csv_file_path, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        
        for row in csv_reader:
            store_id = row['store_id']
            timestamp_str = row['timestamp_utc']
            status = row['status']

            timestamp_str = timestamp_str.replace(' UTC', '')
            
            try:
                timestamp = parse_datetime(timestamp_str)
            except:
                print(f"Error parsing datetime for row: {row}")

            if timestamp.tzinfo is None:
                timestamp = make_aware(timestamp, timezone=timezone.utc)

            store_status = StoreStatus(
                store_id=store_id,
                timestamp_utc=timestamp,
                status=status
            )
            
            store_status_list.append(store_status)
            rows_processed += 1
            
            if len(store_status_list) >= batch_size:
                StoreStatus.objects.bulk_create(store_status_list)
                print(f"Uploaded {rows_processed} rows")
                store_status_list = []

    # Create any remaining objects
    if store_status_list:
        StoreStatus.objects.bulk_create(store_status_list)
        print(f"Uploaded final batch. Total rows processed: {rows_processed}")

    print(f"Upload complete.")

def business_hours_to_db():
    csv_file_path = 'data/Menu hours.csv'
    batch_size = 1000
    store_status_list = []
    rows_processed = 0
    time_format = "%H:%M:%S"  # Assuming times are in this format (e.g., 13:00:00)

    with open(csv_file_path, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)

        for row in csv_reader:
            store_id = row['store_id']
            day = row['day']
            start_time_local_str = row['start_time_local']
            end_time_local_str = row['end_time_local']

            # If start_time or end_time is missing, assume store is open 24/7
            try:
                start_time_local = datetime.strptime(start_time_local_str, time_format).time() if start_time_local_str else datetime.strptime('00:00:00', time_format).time()
                end_time_local = datetime.strptime(end_time_local_str, time_format).time() if end_time_local_str else datetime.strptime('23:59:59', time_format).time()
            except ValueError:
                print(f"Error parsing time for row: {row}")

            # Validate day of the week
            if int(day) < 0 or int(day) > 6:
                print(f"Invalid day of week for row: {row}")

            # Add the data to the batch list
            store_status_list.append(
                BusinessHours(
                    store_id=store_id,
                    day_of_week=day,
                    start_time_local=start_time_local,
                    end_time_local=end_time_local
                )
            )

            # Perform bulk insert when batch size is reached
            if len(store_status_list) >= batch_size:
                BusinessHours.objects.bulk_create(store_status_list)
                store_status_list = []  # Clear the list for the next batch

            rows_processed += 1

        # Insert remaining records if there are any
        if store_status_list:
            BusinessHours.objects.bulk_create(store_status_list)

    print(f"Total rows processed: {rows_processed}")

def store_tz_to_db():
    csv_file_path = 'data/store timezone.csv'  # Update the path as necessary
    batch_size = 1000
    store_timezone_list = []
    rows_processed = 0

    with open(csv_file_path, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)

        for row in csv_reader:
            store_id = row['store_id']
            timezone_str = row['timezone_str']

            if not store_id or not timezone_str:
                print(f"Missing data for row: {row}")

            store_timezone_list.append(
                StoreTimezone(
                    store_id=store_id,
                    timezone_str=timezone_str
                )
            )

            if len(store_timezone_list) >= batch_size:
                StoreTimezone.objects.bulk_create(store_timezone_list)
                store_timezone_list = []

            rows_processed += 1

        if store_timezone_list:
            StoreTimezone.objects.bulk_create(store_timezone_list)

    print(f"Total rows processed: {rows_processed}")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        store_status_to_db()
        business_hours_to_db()
        store_tz_to_db()


# uploading the csv as they were provided, not filling any default values to the db, 
# assuming that the data is populated in db in this format due to some dependencies