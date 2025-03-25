async function requestPasswordChange(email) {
    document.querySelector("#request-password-change-form button i").style.display = "";

    const response = await fetch("/request_password_change", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({email})
    });

    document.querySelector("#request-password-change-form button i").style.display = "none";

    if (response.status === 429) {
        createGeneralPopup("Wow, niet zo snel", "error");
        return;
    }

    const responseJson = await response.json();

    if (response.ok) {
        createGeneralPopup("Email verstuurd", "success");
    } else {
        if (responseJson.error === true) {
            if (responseJson.type === "general") {
                createGeneralPopup(responseJson.message, responseJson.category);
                return;
            }

            const error = document.getElementById(`${responseJson.type}-error`);
            error.classList.add("show");
            error.innerHTML = `<span>${responseJson.message}</span>`;
            
            document.getElementById(`${responseJson.type}-input`).focus();
        }
    }
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
