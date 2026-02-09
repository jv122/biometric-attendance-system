document.addEventListener('DOMContentLoaded', function() {
    const filterBtn = document.getElementById('filterBtn');
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    
    filterBtn.addEventListener('click', loadReports);
    exportCsvBtn.addEventListener('click', () => exportReports('csv'));
    exportExcelBtn.addEventListener('click', () => exportReports('excel'));
    
    // Set default dates (today)
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('end_date').value = today;
    
    // Load reports on page load
    loadReports();
});

function loadReports() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const classFilter = document.getElementById('filter_class').value;
    
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (classFilter) params.append('class_name', classFilter);
    
    fetch(`/api/get_attendance?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayReports(data.data);
            } else {
                alert('Error loading reports: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading reports');
        });
}

function displayReports(data) {
    const tbody = document.getElementById('reports-tbody');
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = data.map(record => `
        <tr>
            <td>${record.date}</td>
            <td>${record.time}</td>
            <td>${record.lecture_number}</td>
            <td>${record.student_name}</td>
            <td>${record.enrollment_number}</td>
            <td>${record.class_name}</td>
            <td><span style="color: ${record.status === 'Present' ? 'green' : 'red'}; font-weight: bold;">${record.status}</span></td>
            <td>${record.faculty_name}</td>
        </tr>
    `).join('');
}

function exportReports(format) {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const classFilter = document.getElementById('filter_class').value;
    
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (classFilter) params.append('class_name', classFilter);
    params.append('format', format);
    
    window.location.href = `/api/export_attendance?${params.toString()}`;
}
