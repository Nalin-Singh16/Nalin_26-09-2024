# Store Uptime/Downtime Report Generator

## 1. Project Overview

- Provides an API for generating and retrieving reports on store uptime and downtime
- Calculates operational status based on business hours and status updates

## 2. API Endpoints

### 2.1 Generate Report

- URL: `/generate-report/`
- Method: POST
- Response: JSON with `report_id`

### 2.2 Get Report

- URL: `/get-report/`
- Method: GET
- Parameters: `report_id` (query parameter)
- Response: JSON with status and report URL (if complete)

Example:
[View CSV Data](reports/report_58f204fe-7815-418b-8caa-c4fef41536e8.csv)

## 3. Key Features

1. Asynchronous report generation using threading
2. Calculation of store uptime and downtime
3. Handling of 24/7 stores and varying business hours
4. Timezone-aware calculations

## 4. Uptime and Downtime Calculation Process

1. Retrieve Business Hours
2. Calculate Time Overlap
3. Get Store Status Counts
4. Calculate Uptime and Downtime

### 4.1 Detailed Calculation Steps

1. Time Overlap Calculation
2. Status Count Retrieval
3. Uptime/Downtime Calculation

### 4.2 Calculation Formula

- Inputs: total_duration, active_status, inactive_status
- Steps:
  1. Calculate Expected Status Updates
  2. Calculate Missing Status Updates
  3. Calculate Extrapolation Factor
  4. Extrapolate Missing Statuses
  5. Calculate Total Active and Inactive Statuses
  6. Calculate Uptime and Downtime

### 4.3 Special Cases and Limitations

- Handling of no status updates
- Accuracy depends on data representativeness
- Assumes consistent operation pattern

## 5. Potential Improvements

1. Replace threading with asyncio for better performance in I/O-bound tasks
2. Optimize database queries, possibly by implementing more efficient indexing or queries
3. Implement error handling and logging for better debugging and monitoring
4. Add unit tests to ensure the accuracy of calculations and API responses

## 6. Detailed Calculation Steps

### 6.1 Time Overlap Calculation

For each day in the report range, the function checks if the store was open.
It calculates the overlap between the store's open hours and the report time range.
The total overlap duration is the sum of all these periods.

### 6.2 Status Count Retrieval

The function fetches all status updates within the report time range.
It counts the number of 'active' and 'inactive' statuses.

### 6.3 Uptime/Downtime Calculation

The calculation of uptime and downtime follows these steps:

1. **Calculate expected status updates:**
   - The expected number of status updates is calculated as: `total_duration / 60` (assuming one status update per hour).

2. **Extrapolate missing data:**
   - If there are fewer actual status updates than expected, the function extrapolates:

     ```extrapolation_factor = statuses_to_be_extrapolated / (active_status + inactive_status)
     extrapolated_active_status = active_status * extrapolation_factor
     extrapolated_inactive_status = inactive_status * extrapolation_factor
     ```

3. **Calculate total active and inactive times:**

   ```total_active = active_status + extrapolated_active_status
   total_inactive = inactive_status + extrapolated_inactive_status
   ```

4. **Calculate final uptime and downtime:**

   ```uptime = total_duration * total_active / (total_active + total_inactive)
   downtime = total_duration - uptime
   ```

This method ensures that:

- The calculation takes into account the store's actual business hours.
- It handles cases where status data might be missing or incomplete.
- It provides a reasonable estimate of uptime and downtime based on the available data.

> **Note:** The accuracy of this calculation depends on the frequency and reliability of status updates. More frequent updates will generally provide more accurate results.
