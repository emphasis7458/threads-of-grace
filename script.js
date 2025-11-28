// Smooth scroll behavior for all links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add fade-in animation on scroll for elements
const observerOptions = {
    threshold: 0,
    rootMargin: '0px 0px 100px 0px'  // Trigger 100px before element enters viewport
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Check if element is in or near viewport (with buffer for upcoming sections)
function isNearViewport(element) {
    const rect = element.getBoundingClientRect();
    const buffer = 200;  // Show sections that are within 200px of viewport
    return rect.top < window.innerHeight + buffer && rect.bottom > -buffer;
}

// Observe sections for fade-in on scroll
document.addEventListener('DOMContentLoaded', () => {
    const sections = document.querySelectorAll('section');
    sections.forEach((section) => {
        // If section is already in or near viewport, show it immediately
        if (isNearViewport(section)) {
            section.style.opacity = '1';
            section.style.transform = 'translateY(0)';
        } else {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            section.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            observer.observe(section);
        }
    });
});
