async function requestPasswordChange(email) {
    document.querySelector("#request-password-change-form button i").style.display = "";

    const response = await fetch("/api/auth/request_password_change", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({email})
    });

    await handleJsonResponse(response);
    document.querySelector("#request-password-change-form button i").style.display = "none";
}

document.getElementById("request-password-change-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const email = document.getElementById("email-input").value;

    if (!isValidEmail(email)) {
        document.getElementById("email-input").focus();

        const emailError = document.getElementById("email-error");
        emailError.classList.add("show");
        emailError.innerHTML = "<span>Ongeldig e-mailadres</span>";

        return;
    }

    await requestPasswordChange(email);
});
