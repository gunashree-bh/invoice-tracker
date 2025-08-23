async function loadData() {
    // Fetch invoices
    let resp = await fetch("/invoices");
    let invoices = await resp.json();

    // Filters
    let customerId = document.getElementById("customerFilter").value;
    let startDate = document.getElementById("startDate").value;
    let endDate = document.getElementById("endDate").value;

    let filtered = invoices.filter(i => {
        let ok = true;
        if (customerId) ok = ok && (i.customer_id == customerId);
        if (startDate) ok = ok && (i.invoice_date >= startDate);
        if (endDate) ok = ok && (i.invoice_date <= endDate);
        return ok;
    });

    // Populate table
    let tbody = document.querySelector("#invoiceTable tbody");
    tbody.innerHTML = "";
    let today = new Date();
    filtered.forEach(i => {
        let due = new Date(i.due_date);
        let overdueClass = (i.outstanding > 0 && due < today) ? "table-danger" : "";
        tbody.innerHTML += `<tr class="${overdueClass}">
            <td>${i.customer_name}</td>
            <td>${i.invoice_id}</td>
            <td>${i.invoice_date}</td>
            <td>${i.due_date}</td>
            <td>${i.invoice_amount}</td>
            <td>${i.total_paid}</td>
            <td>${i.outstanding}</td>
            <td>${i.aging_bucket}</td>
            <td><button class="btn btn-sm btn-primary" onclick="openModal(${i.invoice_id})">Record Payment</button></td>
        </tr>`;
    });

    // Initialize DataTable
    if ($.fn.DataTable.isDataTable('#invoiceTable')) {
        $('#invoiceTable').DataTable().destroy();
    }
    $('#invoiceTable').DataTable({
        paging: true,
        searching: true,
        ordering: true,
        order: [[3, "asc"]] // sort by due date
    });

    // Load KPIs
    let kpiResp = await fetch("/kpis");
    let kpis = await kpiResp.json();
    let kpiDiv = document.getElementById("kpiTiles");
    kpiDiv.innerHTML = `
    <div class="col"><div class="card p-3 bg-light">Total Invoiced: ${kpis.total_invoiced}</div></div>
    <div class="col"><div class="card p-3 bg-light">Total Received: ${kpis.total_received}</div></div>
    <div class="col"><div class="card p-3 bg-light">Total Outstanding: ${kpis.total_outstanding}</div></div>
    <div class="col"><div class="card p-3 bg-light">% Overdue: ${kpis.percent_overdue}%</div></div>`;

    // Top customers chart
    let topResp = await fetch("/top-customers");
    let topCustomers = await topResp.json();
    let ctx = document.getElementById('topCustomersChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topCustomers.map(c => c.customer_name),
            datasets: [{
                label: 'Outstanding',
                data: topCustomers.map(c => c.outstanding),
                backgroundColor: 'rgba(255,99,132,0.6)'
            }]
        }
    });
}

function openModal(invoiceId) {
    document.getElementById("modalInvoiceId").value = invoiceId;
    let modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

async function submitPayment() {
    let invoiceId = document.getElementById("modalInvoiceId").value;
    let amount = document.getElementById("paymentAmount").value;
    let date = document.getElementById("paymentDate").value;

    await fetch("/payments", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({invoice_id: invoiceId, amount: amount, payment_date: date})
    });

    document.getElementById("paymentAmount").value = "";
    let modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
    modal.hide();
    loadData(); // Refresh table and KPIs
}

// Load data on page load
window.onload = loadData;
