function createEyes() {
    const passwords = document.querySelectorAll("input[type=password]");

    for (const password of passwords) {
        const eye = document.createElement("i");
        eye.className = "bi bi-eye-slash";
        eye.addEventListener('click', () => {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            eye.className = type === 'password' ? 'bi bi-eye-slash' : 'bi bi-eye';
        });
        password.parentNode.insertBefore(eye, password.nextSibling);
    }
}

createEyes();