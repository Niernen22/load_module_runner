document.getElementById('RunPlanButton').addEventListener('click', function(event) {
    event.preventDefault();

    const test_id = window.location.pathname.split('/').pop();

    fetch(`/run_test/${test_id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              alert(`Test started successfully! Refresh the page or check the logs for updates. Run ID: ${data.v_run_id}`);

              window.location.href =`/test_steps/${test_id}`;
          } else {
              alert('Error starting test: ' + data.error);
          }
      })
      .catch(error => {
          alert('An unexpected error occurred: ' + error);
      });
});
