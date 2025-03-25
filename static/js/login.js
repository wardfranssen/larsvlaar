async function login(e){
    // Prevent the default form submission
    e.preventDefault();

    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;

    // Send a POST request to the server
    let headers = new Headers();
    headers.append('Content-Type', 'application/json');
    headers.append('Accept', 'application/json');

    const response = await fetch('/login', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({username, password})
    });

    const text = await response.text();

    if (text.includes('Error: ')) {
        const error = text.split('Error: ')[1];
        var dangerAlerts = document.getElementsByClassName('alert-danger');
        if (dangerAlerts.length > 0) {
            if (vibrateAlreadyExistingAlert(dangerAlerts, error)) {
                return;
            }
        }
        deletePopupsByCategory('danger');
        createPopup(error, 'danger');
    } else {
        deletePopupsByCategory('danger');
        createPopup('You have been successfully logged in!', 'success');
        window.location.reload();
    }
}
