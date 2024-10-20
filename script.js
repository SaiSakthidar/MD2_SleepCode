document.addEventListener('DOMContentLoaded', async function () {
    try {
        // Fetch data from the Flask endpoint
        const response = await fetch('http://127.0.0.1:5000/optimize/indexes');
        const text = await response.text();  // Get the response as text
        console.log('Response:', text);  // Log the response

        // Check if the response is valid JSON
        let data;
        try {
            data = JSON.parse(text);  // Parse the JSON data
        } catch (e) {
            console.error('Error parsing JSON:', e);
            return;
        }

        // Display slow queries count
        document.getElementById('slowQueriesCount').textContent = `Slow Queries Count: ${data.slow_queries}`;

        // Display suggested indexes
        displaySuggestedIndexes(data.suggested_indexes);

        // Display unused indexes
        displayUnusedIndexes(data.unused_indexes);

        // Display used indexes in a chart
        displayUsedIndexesChart(data.used_indexes);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
});

// Function to display suggested indexes in the table
function displaySuggestedIndexes(suggestedIndexes) {
    const tableBody = document.querySelector('#suggestedIndexesTable tbody');
    tableBody.innerHTML = '';  // Clear any existing rows

    suggestedIndexes.forEach(index => {
        const row = document.createElement('tr');
        const fieldsCell = document.createElement('td');
        fieldsCell.textContent = index.fields.join(', ');
        row.appendChild(fieldsCell);
        tableBody.appendChild(row);
    });
}

// Function to display unused indexes in the table
function displayUnusedIndexes(unusedIndexes) {
    const tableBody = document.querySelector('#unusedIndexesTable tbody');
    tableBody.innerHTML = '';  // Clear any existing rows

    unusedIndexes.forEach(index => {
        const row = document.createElement('tr');
        const unusedIndexCell = document.createElement('td');
        unusedIndexCell.textContent = index;
        row.appendChild(unusedIndexCell);
        tableBody.appendChild(row);
    });
}

// Function to display used indexes in a bar chart
function displayUsedIndexesChart(usedIndexes) {
    const labels = Object.keys(usedIndexes);  // Index names
    const accessCounts = Object.values(usedIndexes);  // Access counts

    const ctx = document.getElementById('usedIndexesChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Access Count',
                data: accessCounts,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Index Name'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Access Count'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}