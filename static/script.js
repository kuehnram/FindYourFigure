// Apply active to filter-btn
document.addEventListener('DOMContentLoaded', function () {
    const buttons = document.querySelectorAll('.filter-btn');
    const currentPath = window.location.pathname;

    buttons.forEach(button => {
        const buttonPath = new URL(button.href).pathname; // Extracts the path part of the button's href
        if (buttonPath === currentPath) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
});

// Back-to-Top Button
let backToTopButton = document.getElementById('backToTop');
window.addEventListener('scroll', function () {
    if (window.scrollY > 0) {
        backToTopButton.style.display = 'block';
    } else {
        backToTopButton.style.display = 'none';
    }
});

backToTopButton.addEventListener('click', function () {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'  // Smooth transition to the top
    });
});