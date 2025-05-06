async function login(email, password) {
    document.querySelector("#login-form button i").style.display = "";

    const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({email, password})
    });

    await handleJsonResponse(response);
    document.querySelector("#login-form button i").style.display = "none";
}


document.getElementById("login-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const email = document.getElementById("email-input").value;
    const password = document.getElementById("password-input").value;

    if (!isValidEmail(email)) {
        document.getElementById("email-input").focus();

        const emailError = document.getElementById("email-error");
        emailError.classList.add("show");
        emailError.innerHTML = "<span>Ongeldig e-mailadres</span>";

        return;
    }

    await login(email, password);
});

