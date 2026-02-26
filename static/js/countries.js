document.querySelectorAll('.country-name').forEach(name => {
    name.addEventListener('click', () => {
        const ul = name.nextElementSibling;
        if (ul.style.display === 'none') {
            ul.style.display = 'block';
        } else {
            ul.style.display = 'none';
        }
    });
});