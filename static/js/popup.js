// popup.js

// Function to show the pop-up
function showPopup(type, message) {
    var popup = document.getElementById('popup');
    var overlay = document.getElementById('overlay');
    var popupIcon = document.getElementById('popup-icon');
    var popupTitle = document.getElementById('popup-title');
    var popupMessage = document.getElementById('popup-message');
    var popupButton = document.getElementById('popup-button');

    // Reset classes for both success and error
    popup.classList.remove('success', 'error');

    if (type === 'success') {
        // Show success pop-up
        popup.classList.add('success');
        popupIcon.innerHTML = '✔';  // Success checkmark icon
        popupTitle.textContent = 'SUCCESS';
        popupMessage.textContent = message;
        popupButton.style.backgroundColor = '#4CAF50';
    } else if (type === 'error') {
        // Show error pop-up
        popup.classList.add('error');
        popupIcon.innerHTML = 'X';  // Error cross icon
        popupTitle.textContent = 'ERROR';
        popupMessage.textContent = message;
        popupButton.style.backgroundColor = '#f44336';
    }

    // Show the pop-up and overlay
    popup.style.display = 'block';
    overlay.style.display = 'block';
}

// Function to close the pop-up
function closePopup() {
    document.getElementById('popup').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

// Function to check for messages and display the appropriate pop-up
function checkMessages() {
    var successMessage = document.getElementById('success-message') ? document.getElementById('success-message').innerText.trim() : '';
    var errorMessage = document.getElementById('error-message') ? document.getElementById('error-message').innerText.trim() : '';

    // Trigger the popup based on the message
    if (successMessage) {
        showPopup('success', successMessage);
    } else if (errorMessage) {
        showPopup('error', errorMessage);
    }
}
