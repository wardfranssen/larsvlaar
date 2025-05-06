async function register(username, email, password) {
    document.querySelector("#register-form button i").style.display = "";

    const response = await fetch("/api/auth/register", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({username, email, password})
    });

    await handleJsonResponse(response);
    document.querySelector("#register-form button i").style.display = "none";
}


document.getElementById("register-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    document.getElementById("password-dont-match").classList.remove("show");

    const username = document.getElementById("username-input").value;
    const email = document.getElementById("email-input").value;
    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;

    if (!isStrongPassword(password)) {
        document.getElementById("password-input").focus();
        return;
    }

    if (password !== confirmPassword) {
        document.getElementById("confirm-password-input").focus();
        document.getElementById("password-dont-match").classList.add("show");
        return;
    }

    if (!isValidEmail(email)) {
        document.getElementById("email-input").focus();

        const emailError = document.getElementById("email-error");
        emailError.classList.add("show");
        emailError.innerHTML = "<span>Ongeldig e-mailadres</span>";

        return;
    }

    await register(username, email, password);
});

document.getElementById("email-input").addEventListener("input", function() {
    const email = document.getElementById("email-input").value;

    if (isValidEmail(email)) {
        document.getElementById("email-error").classList.remove("show");
    }
});

document.getElementById("password-input").addEventListener("input", function() {
    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;
    isStrongPassword(password);

    if (password === confirmPassword) {
        document.getElementById("password-dont-match").classList.remove("show");
    }
});

document.getElementById("confirm-password-input").addEventListener("input", function() {
    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;

    if (password === confirmPassword) {
        document.getElementById("password-dont-match").classList.remove("show");
    }
});

