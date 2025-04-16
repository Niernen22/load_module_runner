function showParametersForm() {
    let selectedType = document.getElementById('step_type').value;
    if (selectedType === 'LM_JOB') {
        document.getElementById('LMparametersForm').style.display = 'block';
    } else {
        document.getElementById('LMparametersForm').style.display = 'none';
    }
}

function getNamesForModule(selectedModule) {
    var nameSelect = document.getElementById('name');
    fetch('/get_names_for_module', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module: selectedModule })
    })
    .then(response => response.json())
    .then(data => {
        nameSelect.innerHTML = '';
        data.forEach(function(name) {
            var option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            nameSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}

function getTypesForModule(selectedModule) {
    var typeSelect = document.getElementById('type');
    fetch('/get_types_for_module', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ module: selectedModule })
    })
    .then(response => response.json())
    .then(data => {
        typeSelect.innerHTML = '';
        data.forEach(function(type) {
            var option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeSelect.appendChild(option);
        });
    })
    .catch(error => console.error('Error:', error));
}

function openPopup() {
    var modal = document.getElementById("myModal");
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
    let formData = {
        new_step_name: document.getElementById('new_step_name').value.trim(),
        step_type: 'LM_JOB',
        module: null,
        type: null,
        name: null
    };

    formData.module = document.getElementById('module').value.trim();
    formData.type = document.getElementById('type').textContent.trim();
    formData.name = document.getElementById('name').value.trim();
    submitFormDataToServer(formData);
}


function submitFormDataToServer(formData) {
    fetch('/add_step/' + test_id, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Step successfully added!");
            window.location.href = data.redirect_url;
        } else {
            alert("Error: " + data.error);
        }
    })
    .catch(error => {
        console.error('Error during AJAX submission:', error);
        alert("There was an error submitting the form. Please try again.");
    });
}


function enableDragAndDrop() {
    const rows = document.querySelectorAll('tbody tr');
    let draggingRow = null;

    rows.forEach(row => {
        row.draggable = true;

        row.addEventListener('dragstart', (event) => {
            draggingRow = row;
            row.classList.add('dragging');
            event.dataTransfer.setData('text/plain', row.rowIndex);
        });

        row.addEventListener('dragover', (event) => {
            event.preventDefault();
            const currentRow = event.target.closest('tr');

            if (draggingRow && draggingRow !== currentRow) {
                currentRow.classList.add('drop-target');
            }
        });

        row.addEventListener('dragleave', () => {
            row.classList.remove('drop-target');
        });

        row.addEventListener('drop', (event) => {
            event.preventDefault();
            const currentRow = event.target.closest('tr');

            if (draggingRow && draggingRow !== currentRow) {
                const tbody = document.querySelector('tbody');

                if (draggingRow.rowIndex < currentRow.rowIndex) {
                    tbody.insertBefore(draggingRow, currentRow.nextSibling);
                } else {
                    tbody.insertBefore(draggingRow, currentRow);
                }

                draggingRow.classList.remove('moving-up', 'moving-down', 'dragging');
                currentRow.classList.remove('drop-target');
            }

            draggingRow = null;
        });

        row.addEventListener('dragend', () => {
            row.classList.remove('dragging', 'moving-up', 'moving-down');
        });
    });
}



function finishEditing() {
    const rows = document.querySelectorAll('tbody tr');
    const data = [];

    rows.forEach((row, index) => {
        const id = row.querySelector('input[name="id"]').value;
        data.push({ id: id, order_number: index + 1 });
    });

    fetch('/update_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href =`/test_steps/${test_id}`;
        } else {
            alert('Error updating order');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', enableDragAndDrop);

