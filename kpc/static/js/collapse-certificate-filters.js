(function($) {
    $(document).ready(function() {
	$('#filter-toggle-link').click(function() {
            if ($('#certificate-filters-container:visible').length > 0) {
                $('#certificate-filters-container').hide();
		$('#filter-toggle-link').text('Open filters');
            }
            else {
                $('#certificate-filters-container').show();
		$('#filter-toggle-link').text('Close filters');
            }
        })
    });
})(window.jQuery);
