import uuid
import threading
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Report
from .report_generator import generate_report

@csrf_exempt
def trigger_report(request):
    if request.method == 'POST':
        report_id = str(uuid.uuid4())
        try:
            report = Report.objects.create(report_id=report_id)
            threading.Thread(target=generate_report, args=(report.report_id,)).start()
        except Exception as e:
            return JsonResponse({'error': e}, status = 500)
        return JsonResponse({'report_id': report_id}, status = 200)
    else:
        return JsonResponse({'error':'Request method not allowed'}, status = 405)

def get_report(request):
    report_id = request.GET.get('report_id')
    try:
        report = Report.objects.get(report_id=report_id)
        if report.status == 'Complete':
            return JsonResponse({'status': 'Complete','report_url': report.csv_file.url})
        elif report.status == 'Failed':
            return JsonResponse({'status': 'Failed'}, status=500)
        else:
            return JsonResponse({'status': 'Running'})
    except Report.DoesNotExist:
        return JsonResponse({'error': 'Report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': e}, status=500)