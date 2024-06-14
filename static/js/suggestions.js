async function submitSuggestion(e) {
    e.preventDefault();
    console.log('submitting suggestion');
    let suggestion = document.getElementById('suggestionInput').value;
    const response = await fetch('/suggestions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({suggestion}),
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
        createPopup('Suggestion has been successfully submitted!', 'success');
    }
}