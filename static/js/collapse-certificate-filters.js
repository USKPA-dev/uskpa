(function($) {
    $(document).ready(function() {
    $('#filter-toggle-link').click(function(event) {
			event.preventDefault();
            if ($('#certificate-filters:visible').length > 0) {
                $('#certificate-filters').hide();
				$('#filter-toggle-link').html('Open filters<i class="fas fa-caret-right"></i>');
				$('.cert-listing').removeClass('usa-width-two-thirds');
				$('.filters').removeClass('usa-width-one-third');
				$('#certDataTable').css('width', '100%');
            }
            else {
                $('#certificate-filters').show();
				$('#filter-toggle-link').html('<i class="fas fa-caret-left"></i>Close filters');
				$('.cert-listing').addClass('usa-width-two-thirds');
				$('.filters').addClass('usa-width-one-third');
            }
        })
    });
})(window.jQuery);
