document.addEventListener('DOMContentLoaded', function() {
    const clockInButton = document.getElementById('clockInButton');
    const clockOutButton = document.getElementById('clockOutButton');
  
    clockInButton.addEventListener('click', function() {
      fetch('/clock_in', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'user_id=123&timestamp=' + new Date().toISOString()
      })
      .then(function(response) {
        if (response.ok) {
          console.log('Clocked in successfully');
        } else {
          console.error('Failed to clock in');
        }
      })
      .catch(function(error) {
        console.error('An error occurred while clocking in:', error);
      });
    });
  
    clockOutButton.addEventListener('click', function() {
      fetch('/clock_out', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'user_id=123&timestamp=' + new Date().toISOString()
      })
      .then(function(response) {
        if (response.ok) {
          console.log('Clocked out successfully');
        } else {
          console.error('Failed to clock out');
        }
      })
      .catch(function(error) {
        console.error('An error occurred while clocking out:', error);
      });
    });
  });
  