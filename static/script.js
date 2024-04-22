document.addEventListener("DOMContentLoaded", function () {
    // Select all select elements within .input-group
    var selects = document.querySelectorAll('.input-group select');

    // Loop over each select element
    selects.forEach(function (select) {
        // Create a non-breaking space and add it before the select element
        var nbsp = document.createTextNode('\u00A0');
        select.parentNode.insertBefore(nbsp, select);

        // Create and append two line break elements after the select element
        var br1 = document.createElement('br');
        var br2 = document.createElement('br');

        // Append line breaks after the select element
        select.parentNode.insertBefore(br1, select.nextSibling);
        select.parentNode.insertBefore(br2, br1.nextSibling);
    });
});
