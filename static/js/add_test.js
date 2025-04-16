function openTestPopup() {
    var modal = document.getElementById("TestModal");
    modal.style.display = "block";

    var span = document.getElementsByClassName("close")[0];
    span.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
}

function submitFormData() {
    var form = document.getElementById("testForm");
    var formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.text();
        }
    })
    .then(result => {
        console.log('Success:', result);
        document.getElementById("TestModal").style.display = "none";
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
