from django.db import models

# Create your models here.

class StoreStatus(models.Model):
    store_id = models.CharField(max_length=50)
    timestamp_utc = models.DateTimeField()
    status = models.CharField(max_length=20)
    class Meta:
        indexes = [
            models.Index(fields=['store_id', 'timestamp_utc']),
        ]

class BusinessHours(models.Model):
    store_id = models.CharField(max_length=50)
    day_of_week = models.IntegerField()
    start_time_local = models.TimeField()
    end_time_local = models.TimeField()
    class Meta:
        indexes = [
            models.Index(fields=['store_id', 'day_of_week', 'start_time_local']),
        ] 

class StoreTimezone(models.Model):
    store_id = models.CharField(max_length=50, unique=True)
    timezone_str = models.CharField(max_length=50)

class Report(models.Model):
    report_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, default='Running')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    csv_file = models.FileField(upload_to='reports/', null=True, blank=True)