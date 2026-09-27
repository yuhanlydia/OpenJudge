from .report import validate_report

def can_publish(report,bundle):
    result=validate_report(report,bundle)
    if report.get('editorial_state')!='approved' or not report.get('approval_record_id'):
        result['errors'].append({'code':'unapproved_report','record_id':report.get('report_id')})
        result['ok']=False
    return result
