document.addEventListener('DOMContentLoaded', function() {
    // Order status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            window.location.href = `/admin/orders?status=${this.value}`;
        });
    }
    
    // Order approval confirmation
    const approveForm = document.getElementById('approveOrderForm');
    if (approveForm) {
        approveForm.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to approve this order?')) {
                e.preventDefault();
            }
        });
    }
    
    // Order rejection confirmation
    const rejectForm = document.getElementById('rejectOrderForm');
    if (rejectForm) {
        rejectForm.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to reject this order?')) {
                e.preventDefault();
            }
        });
    }
    
    // Plan update confirmation
    const updatePlanForms = document.querySelectorAll('form[id^="updatePlanForm"]');
    if (updatePlanForms.length > 0) {
        updatePlanForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!confirm('آیا از بروزرسانی این طرح اطمینان دارید؟')) {
                    e.preventDefault();
                } else {
                    console.log('Submitting form:', this.id);
                }
            });
        });
    }
    
    // Manually add click handlers to the update buttons
    const updatePlanButtons = document.querySelectorAll('.btn[type="submit"]');
    if (updatePlanButtons.length > 0) {
        updatePlanButtons.forEach(button => {
            button.addEventListener('click', function() {
                const formId = this.closest('form').id;
                console.log('Button clicked for form:', formId);
            });
        });
    }
    
    // Tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            navigator.clipboard.writeText(text).then(() => {
                // Change button text temporarily
                const originalText = this.innerHTML;
                this.innerHTML = 'Copied!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });
    
    // Order pagination
    const paginationLinks = document.querySelectorAll('.pagination .page-link');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('page', page);
            window.location.href = currentUrl.toString();
        });
    });
});
