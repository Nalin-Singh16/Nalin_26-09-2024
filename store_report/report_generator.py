import pandas as pd
import pytz
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from django.utils import timezone as django_timezone
from store_report.models import BusinessHours, Report, StoreStatus, StoreTimezone
from typing import List, Dict, Union

def generate_report(report_id: int) -> None:
    """ Generating a report for a given ID.
    Args:
        report_id (integer).

    Returns:
        None
    """
    report = Report.objects.get(report_id=report_id)
    print(f"Starting report generation for report_id: {report_id}")
    try:
        current_time = StoreStatus.objects.latest('timestamp_utc').timestamp_utc
        stores = StoreStatus.objects.values_list('store_id', flat=True).distinct()
        print(f"Processing {len(stores)} stores")
        results = []
        
        for store_id in stores:
            print(f"generating for store with store_id: {store_id}")
            timezone_str = get_store_timezone(store_id)
            local_tz = pytz.timezone(timezone_str)
            local_current_time = current_time.astimezone(local_tz)
            
            hour_ago = local_current_time - timedelta(hours=1)
            day_ago = local_current_time - timedelta(days=1)
            week_ago = local_current_time - timedelta(weeks=1)
            
            uptime_last_hour, downtime_last_hour = get_uptime_downtime(store_id, local_current_time, hour_ago)
            uptime_last_day, downtime_last_day = get_uptime_downtime(store_id, local_current_time, day_ago)
            uptime_last_week, downtime_last_week = get_uptime_downtime(store_id, local_current_time, week_ago)
            
            results.append({
                'store_id': store_id,
                'uptime_last_hour': uptime_last_hour,
                'uptime_last_day': uptime_last_day/60,
                'uptime_last_week': uptime_last_week/60,
                'downtime_last_hour': downtime_last_hour,
                'downtime_last_day': downtime_last_day/60,
                'downtime_last_week': downtime_last_week/60,
            })
        
        df = pd.DataFrame(results)
        csv_file = df.to_csv(index=False)
        report.status = 'Complete'
        report.csv_file.save(f'report_{report.report_id}.csv', ContentFile(csv_file))
        report.completed_at = django_timezone.now()
        report.save()
    except Exception as e:
        print(f"Report generation failed for report_id {report.report_id}: {e}")
        report.status = 'Failed'
        report.save()

def get_uptime_downtime(store_id: int, local_current_time: datetime, report_start_time: datetime) -> tuple[float, float]:
    """ Calculating uptime and downtime for a store within the time overlap

    Args:
        store_id (Integer).
        local_current_time (Datetime) in local timezone.
        report_start_time (Datetime) in local timezone.

    Returns:
        tuple[float, float]: A tuple containing uptime and downtime of the store in minutes
    """  
    store_hours = get_formatted_business_hours(store_id)
    
    is_24_7 = all(hour['start'] == '00:00:00' and hour['end'] == '23:59:59' for hour in store_hours)
    if is_24_7:
        print(f"Store {store_id} is operating 24/7")
        total_duration = (local_current_time - report_start_time).total_seconds() / 60
    else:
        overlap_periods = calculate_overlap(store_hours, report_start_time, local_current_time)
        print(f"overlap_periods: {overlap_periods}")
        if not overlap_periods:
            print(f"No overlap found for store_id: {store_id}. Assuming full downtime.")
            return 0, (local_current_time - report_start_time).total_seconds() / 60
        total_duration = sum(period['duration'] for period in overlap_periods)
    active_status, inactive_status = get_store_status_counts(store_id, report_start_time, local_current_time)
    uptime, downtime = calculate_uptime_downtime(total_duration, active_status, inactive_status)
    return uptime, downtime

def get_formatted_business_hours(store_id: int) -> List[Dict[str, str]]:
    """ Get the working hours of the store
    Args:
        store_id (integer)

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing business hours.
    """
    business_hours = BusinessHours.objects.filter(store_id=store_id).order_by('day_of_week', 'start_time_local')
    
    print(f"Number of business hours records found: {business_hours.count()}")
    
    if business_hours.count() == 0:
        print(f"No business hours found for store_id: {store_id}. Assuming 24/7 operation.")
        return [{'day': day, 'start': '00:00:00', 'end': '23:59:59'} for day in range(7)]
    
    formatted_hours = [
        {
            'day': bh.day_of_week,
            'start': bh.start_time_local.strftime('%H:%M:%S'),
            'end': bh.end_time_local.strftime('%H:%M:%S')
        }
        for bh in business_hours
    ]
    
    print(f"Formatted hours: {formatted_hours}")
    
    return formatted_hours

def calculate_overlap(store_hours: List[Dict[str, str]], start_time: datetime, end_time: datetime) -> List[Dict[str, datetime]]:
    """ Calculate the overlap between store hours and the report time range.

    Args:
        store_hours (List[Dict[str, str]]): A list of dictionaries containing store hours.
        start_time (datetime): The start time of the report period.
        end_time (datetime): The end time of the report period.

    Returns:
        List[Dict[str, datetime]]: A list of dictionaries containing overlap periods.
    """
    overlap_periods = []
    
    current_date = start_time.date()
    
    while current_date <= end_time.date():
        day_of_week = current_date.weekday()
        
        for hours in store_hours:
            if hours['day'] == day_of_week:
                store_open = datetime.combine(current_date, parse_time(hours['start'])).replace(tzinfo=pytz.UTC)
                store_close = datetime.combine(current_date, parse_time(hours['end'])).replace(tzinfo=pytz.UTC)
                if store_close <= store_open: 
                    store_close += timedelta(days=1)
                
                overlap_start = max(start_time, store_open)
                overlap_end = min(end_time, store_close)
                
                if overlap_start < overlap_end:
                    overlap_duration = overlap_end - overlap_start
                    overlap_periods.append({
                        'start': overlap_start,
                        'end': overlap_end,
                        'duration': overlap_duration.total_seconds() / 60
                    })
        
        current_date += timedelta(days=1)
    
    return overlap_periods

def parse_time(time_str: str) -> datetime.time:
    return datetime.strptime(time_str, "%H:%M:%S").time()

def get_store_timezone(store_id: int) -> str:
    try:
        timezone_obj = StoreTimezone.objects.get(store_id=store_id)
        return timezone_obj.timezone_str
    except StoreTimezone.DoesNotExist:
        return 'America/Chicago'

def get_store_status_counts(store_id: int, start_time: datetime, end_time: datetime) -> tuple[int, int]:
    """ Get the count of active and inactive statuses for a store within a time range.

    Args:
        store_id (int)
        start_time (datetime) in local timezone
        end_time (datetime) in local timezone

    Returns:
        tuple[int, int]: Returns the count of active and inactive statuses.
    """
    statuses = StoreStatus.objects.filter(
        store_id=store_id, 
        timestamp_utc__range=(start_time, end_time)
    ).values('status')

    active_status = 0
    for s in statuses:
        if s['status'] == 'active':
            active_status += 1
    inactive_status = len(statuses) - active_status

    return active_status, inactive_status

def calculate_uptime_downtime(total_duration: float, active_status: int, inactive_status: int) -> tuple[float, float]:
    """ Calculate uptime and downtime based on active and inactive status counts.

    Args:
        total_duration (float): The total duration in hours.
        active_status (int): The count of active statuses.
        inactive_status (int): The count of inactive statuses.

    Returns:
        tuple[float, float]: A tuple containing uptime and downtime in hours.
    """
    expected_status_num = total_duration / 60
    statuses_to_be_extrapolated = expected_status_num - (active_status + inactive_status)

    if active_status + inactive_status > 0:
        extrapolation_factor = statuses_to_be_extrapolated / (active_status + inactive_status)
        extrapolated_active_status = active_status * extrapolation_factor
        extrapolated_inactive_status = inactive_status * extrapolation_factor

        total_active = active_status + extrapolated_active_status
        total_inactive = inactive_status + extrapolated_inactive_status

        uptime = total_duration * total_active / (total_active + total_inactive)
        downtime = total_duration - uptime
    else:
        uptime = 0
        downtime = total_duration

    return uptime, downtime
    

    