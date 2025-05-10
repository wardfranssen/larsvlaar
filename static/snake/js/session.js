async function getSession(sessionId) {
    const response = await fetch(`/api/admin/sessions/${sessionId}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    return await handleJsonResponse(response);
}


async function updateChart() {
    const responseJson = await getSession(sessionId);
    const timestamps = responseJson["data"]["requests"]["total"];
    if (timestamps.length === 0) return;


    let binSize, labelFormat;

    if (currentPeriod === "1h") {
        binSize = 60 * 1000;
        labelFormat = { hour: '2-digit', minute: '2-digit' };
    } else if (currentPeriod === "24h") {
        binSize = 60 * 60 * 1000;
        labelFormat = { hour: '2-digit' };
    } else if (currentPeriod === "7d") {
        binSize = 24 * 60 * 60 * 1000;
        labelFormat = { weekday: 'short', hour: '2-digit' };
    }

    const binned = {};
    for (const ts of timestamps) {
        const bucket = Math.floor(ts / binSize) * binSize;
        binned[bucket] = (binned[bucket] || 0) + 1;
    }

    const labels = [];
    const data = [];

    for (const [timestamp, count] of Object.entries(binned)) {
        labels.push(formatLabel(Number(timestamp), labelFormat));
        data.push(count);
    }

    rpsChart.data.labels = labels;
    rpsChart.data.datasets[0].data = data;
    rpsChart.update();
}

function formatLabel(timestamp, labelFormat) {
    return new Intl.DateTimeFormat('default', labelFormat).format(new Date(timestamp));
}

function setPeriod(period) {
    currentPeriod = period;
    updateChart();
}

// Example: Add buttons to allow users to switch between periods
document.getElementById('period-1h').addEventListener('click', () => setPeriod('1h'));
document.getElementById('period-24h').addEventListener('click', () => setPeriod('24h'));
document.getElementById('period-7d').addEventListener('click', () => setPeriod('7d'));




const sessionId = window.location.toString().split("/")[window.location.toString().split("/").length-1]
let currentPeriod = "1h";

const ctx = document.getElementById('rps-chart').getContext('2d');
const rpsChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // we fill this dynamically
        datasets: [{
            label: 'Requests per bin',
            data: [],
            borderColor: 'orange',
            fill: true,
        }]
    },
    options: {
        responsive: false,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: 'category', // 🔁 CHANGED from 'time' to 'category'
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Requests'
                },
                beginAtZero: true
            }
        }
    }
});

setInterval(updateChart, 1000);
