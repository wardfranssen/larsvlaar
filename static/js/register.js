async function register(e){
    // Prevent the default form submission
    e.preventDefault();

    if (!arePasswordsMatching()) {return;}

    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;

    // Send a POST request to the server
    let headers = new Headers();
    headers.append('Content-Type', 'application/json');
    headers.append('Accept', 'application/json');

    const response = await fetch('/register', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({username, password})
    });

    const text = await response.text();

    if (text.includes('Error: ')) {
        const error = text.split('Error: ')[1];
        let dangerAlerts = document.getElementsByClassName('alert-danger');
        if (dangerAlerts.length > 0) {
            if (vibrateAlreadyExistingAlert(dangerAlerts, error)) {
                return;
            }
        }
        deletePopupsByCategory('danger');
        createPopup(error, 'danger');
    } else {
        deletePopupsByCategory('danger');
        createPopup('You have been successfully registered!', 'success');
        window.location.reload();
    }
}


function arePasswordsMatching() {
    let password = document.getElementById('passwordInput').value;
    let repeatPassword = document.getElementById('repeatInput').value;
    let dangerAlerts = document.getElementsByClassName('alert-danger');
    
    if (password !== repeatPassword) {
        if (vibrateAlreadyExistingAlert(dangerAlerts, 'Passwords don\'t match')) {
            return false;
        }
        deletePopupsByCategory('danger');
        createPopup('Passwords don\'t match', 'danger');
        return false;
    }
    return true;
}