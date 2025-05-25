from datetime import datetime, timedelta
from flask import render_template, request, send_file
import pdfkit
import os

# ... existing code ...

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')
    format_type = request.form.get('format', 'pdf')
    
    # Calculate date range
    end_date = datetime.now()
    if date_range == 'daily':
        start_date = end_date - timedelta(days=1)
    elif date_range == 'weekly':
        start_date = end_date - timedelta(weeks=1)
    elif date_range == 'monthly':
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=7)  # Default to weekly
    
    # Get data based on report type
    if report_type == 'missing':
        data = MissingPerson.query.filter(
            MissingPerson.date_reported >= start_date,
            MissingPerson.date_reported <= end_date
        ).all()
        title = f"Missing Persons Report ({date_range.capitalize()})"
    elif report_type == 'found':
        data = MissingPerson.query.filter(
            MissingPerson.date_found >= start_date,
            MissingPerson.date_found <= end_date,
            MissingPerson.status == 'found'
        ).all()
        title = f"Found Persons Report ({date_range.capitalize()})"
    else:  # summary
        missing = MissingPerson.query.filter(
            MissingPerson.date_reported >= start_date,
            MissingPerson.date_reported <= end_date
        ).all()
        found = MissingPerson.query.filter(
            MissingPerson.date_found >= start_date,
            MissingPerson.date_found <= end_date,
            MissingPerson.status == 'found'
        ).all()
        data = {'missing': missing, 'found': found}
        title = f"Summary Report ({date_range.capitalize()})"
    
    # Generate HTML report
    html = render_template(
        'report_template.html',
        title=title,
        data=data,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date
    )
    
    # Create PDF
    if format_type == 'pdf':
        pdf = pdfkit.from_string(html, False)
        filename = f"report_{report_type}_{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'reports', filename)
        
        # Ensure reports directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(pdf)
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    else:
        # Return HTML version
        return html 