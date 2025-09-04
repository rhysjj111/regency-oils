// In core/static/admin/js/log_form_helpers.js

window.addEventListener("load", function() {
    // This code runs when the admin page is loaded
    (function($) {
        $(document).ready(function() {
            // Find the route dropdown and the field we want to update
            const routeSelect = $('#id_route');
            const freshOilInput = $('#id_start_day_fresh_oil');

            // Function to fetch and update the total
            function updateFreshOilTotal() {
                const routeId = routeSelect.val();
                if (routeId) {
                    fetch(`/api/route-totals/${routeId}/`)
                        .then(response => response.json())
                        .then(data => {
                            freshOilInput.val(data.total_planned_fresh_oil);
                        })
                        .catch(error => console.error('Error fetching route totals:', error));
                }
            }

            // Run the function whenever the route dropdown changes
            routeSelect.on('change', updateFreshOilTotal);

            // Also run it on page load in case a route is already selected
            if (routeSelect.val()) {
                updateFreshOilTotal();
            }
        });
    })(django.jQuery);
});