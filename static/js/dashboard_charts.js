// BAR CHART - Time Spendings
const timeCtx = document.getElementById('timeChart');

if (timeCtx) {
  new Chart(timeCtx, {
    type: 'bar',
    data: {
      labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      datasets: [{
        label: 'Hours Spent',
        data: [1, 2, 3, 8, 2, 3, 1],
        backgroundColor: '#000'
      }]
    },
    options: {
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: '#eee' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}


// DONUT CHART - Course Statistics
const courseCtx = document.getElementById('courseChart');

if (courseCtx) {
  new Chart(courseCtx, {
    type: 'doughnut',
    data: {
      labels: ['Completed', 'In Progress', 'Incomplete'],
      datasets: [{
        data: [30, 20, 50],
        backgroundColor: ['#000', '#777', '#ddd']
      }]
    },
    options: {
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      cutout: '65%'
    }
  });
}
