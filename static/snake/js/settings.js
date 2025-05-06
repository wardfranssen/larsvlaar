function openChangePfpPopup() {
    document.querySelector(".chang-pfp-popup").classList.add("show");
}

function closeChangePfpPopup() {
    document.querySelector(".chang-pfp-popup").classList.remove("show");
}

async function changeUsername(newUsername) {
    document.querySelector("#change-username-form button i").style.display = "";

    const response = await fetch("/api/account/username", {
        method: "POST",
        body: JSON.stringify({username: newUsername}),
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    })

    await handleJsonResponse(response);
    document.querySelector("#change-username-form button i").style.display = "none";
}

async function changePassword(newPassword) {
    document.querySelector("#change-password-form button i").style.display = "";

    const response = await fetch("/api/account/password", {
        method: "POST",
        body: JSON.stringify({new_password: newPassword}),
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
    document.querySelector("#change-password-form button i").style.display = "none";
}

function openSettingsTab(tabName) {
    if (document.querySelector(`#${tabName}-content`).classList.contains("show")) {
        return;
    }

    document.querySelectorAll('.settings-section').forEach(section => {
        section.classList.remove('show');
    });

    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('selected');
    });
    document.querySelector(`#${tabName}-nav`).classList.add('selected');

    setTimeout(() => {
        document.querySelectorAll('.settings-section').forEach(section => {
            section.style.display = 'none';
        });

        const section = document.querySelector(`#${tabName}-content`);
        section.style.display = '';

        setTimeout(() => {
            section.classList.add('show');
        }, 1)
    }, 300)
}

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

document.querySelector("#change-password-form").addEventListener("submit", (e) => {
    e.preventDefault();
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

    changePassword(password);
});

document.querySelector("#change-username-form").addEventListener("submit", (e) => {
    e.preventDefault();

    const newUsername = document.querySelector("#username-input").value;
    changeUsername(newUsername);
});

document.querySelector(".chang-pfp-popup").addEventListener("click", (e) => {
    if (e.target.classList.contains("chang-pfp-popup")) {
        closeChangePfpPopup();
    }
});

openSettingsTab("account-settings");


// Croppie stuff
const croppieContainer = document.getElementById('croppie-container');
const croppieCropper = document.getElementById("croppie-cropper");
const uploadButton = document.getElementById("upload");
const cropButton = document.getElementById("upload-cropped");

let croppieInstance;

uploadButton.addEventListener("change", (e) => {
    const file = e.target.files[0];
    croppieContainer.style.display = 'none';
    if (!file) return;
    croppieContainer.style.display = 'block';

    const reader = new FileReader();

    reader.onload = function(event) {
        if (croppieInstance) {
            croppieInstance.destroy();
        }

        // Initialize Croppie
        croppieInstance = new Croppie(croppieCropper, {
            viewport: { width: 128, height: 128, type: 'circle' },
            boundary: { width: 300, height: 220 },
            showZoomer: false, // Show slider for zooming
            enableOrientation: true
        });

        // Bind the image to Croppie
        croppieInstance.bind({
            url: event.target.result
        });

        cropButton.style.display = 'inline-block'; // Show the crop button after the image is loaded
    };

    reader.readAsDataURL(file);
});

cropButton.addEventListener("click", () => {
    croppieInstance.result({
        type: 'base64',  // Getting the base64 string
        size: { width: 256, height: 256 },  // Square size
        circle: false     // Ensure it's not cropped in a circle
    }).then((croppedImageBase64) => {
        // Convert base64 to Blob manually
        const byteString = atob(croppedImageBase64.split(',')[1]); // Get base64 data (without the 'data:image/png;base64,' part)
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const uint8Array = new Uint8Array(arrayBuffer);

        for (let i = 0; i < byteString.length; i++) {
            uint8Array[i] = byteString.charCodeAt(i);
        }

        const blob = new Blob([uint8Array], { type: 'image/png' }); // Create Blob from the byte array

        const formData = new FormData();
        formData.append("file", blob, "pfp.png"); // Append the Blob to FormData

        // Upload the image to the server
        fetch("/api/account/pfp", {
            method: "POST",
            body: formData
        }).then(response => response.json())
            .then(responseJson => {
                if (responseJson.error === true) {
                    if (responseJson.type === "general") {
                        createGeneralPopup(responseJson.message, responseJson.category);
                        return;
                    }

                    const error = document.getElementById(`${responseJson.type}-error`);
                    error.classList.add("show");
                    error.innerHTML = `<span>${responseJson.message}</span>`;

                    document.getElementById(`${responseJson.type}-input`).focus();
                } else {
                    window.location.reload();
                }
            });
    });
});