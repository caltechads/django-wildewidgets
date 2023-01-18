
function register_ww_dropdown_toggle() {
    /*
    Register our onClick handler for .dropdown-toggle with a data attribute
    of "data-bs-toggle='dropdown-ww'".

    This is what makes :py:class:`ClickableNavDropdownControl` work.
    */
    $(".dropdown-toggle[data-bs-toggle='dropdown-ww']").click(function () {
        var target_id = $(this).attr('data-bs-target');
        var target = $(target_id);
        if ($(this).attr('aria-expanded') === 'false') {
            target.addClass('show');
            $(this).attr('aria-expanded', 'true');
        } else {
            $(this).attr('aria-expanded', 'false');
            target.removeClass('show');
        }
    })

}

// ----------------------------------
// Document ready
// ----------------------------------

$(document).ready(function() {
    register_ww_dropdown_toggle();
});
