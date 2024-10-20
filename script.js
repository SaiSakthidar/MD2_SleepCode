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
        displaySuggestedIndexes(data.suggested_indexes, data.tradeoffs);

        // Display unused indexes
        displayUnusedIndexes(data.unused_indexes, data.tradeoffs);

        // Display used indexes in a chart
        displayUsedIndexesChart(data.used_indexes);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
});

// Function to display suggested indexes in the table
function displaySuggestedIndexes(suggestedIndexes, tradeoffs) {
    const tableBody = document.querySelector('#suggestedIndexesTable tbody');
    tableBody.innerHTML = '';  // Clear any existing rows

    suggestedIndexes.forEach(index => {
        const row = document.createElement('tr');
        const fieldsCell = document.createElement('td');
        fieldsCell.textContent = index.fields.join(', ');
        row.appendChild(fieldsCell);

        // Add performance indicator and storage required
        const tradeoff = tradeoffs.find(t => t.index === index.fields.join(', '));
        const performanceCell = document.createElement('td');
        performanceCell.textContent = tradeoff ? tradeoff.performance_measure : 'N/A';
        row.appendChild(performanceCell);

        const storageCell = document.createElement('td');
        storageCell.textContent = tradeoff ? tradeoff.storage_extra_required : 'N/A';
        row.appendChild(storageCell);

        // Add button to add index
        const addButtonCell = document.createElement('td');
        const addButton = document.createElement('button');
        addButton.textContent = 'Add Index';
        addButton.onclick = () => addIndex(index.fields);
        addButtonCell.appendChild(addButton);
        row.appendChild(addButtonCell);

        tableBody.appendChild(row);
    });
}

// Function to display unused indexes in the table
function displayUnusedIndexes(unusedIndexes, tradeoffs) {
    const tableBody = document.querySelector('#unusedIndexesTable tbody');
    tableBody.innerHTML = '';  // Clear any existing rows

    unusedIndexes.forEach(index => {
        const row = document.createElement('tr');
        const unusedIndexCell = document.createElement('td');
        unusedIndexCell.textContent = index;
        row.appendChild(unusedIndexCell);

        // Add performance indicator and storage saved
        const tradeoff = tradeoffs.find(t => t.index === index);
        const performanceCell = document.createElement('td');
        performanceCell.textContent = tradeoff ? tradeoff.performance_measure : 'N/A';
        row.appendChild(performanceCell);

        const storageCell = document.createElement('td');
        storageCell.textContent = tradeoff ? tradeoff.storage_saved : 'N/A';
        row.appendChild(storageCell);

        // Add button to remove index
        const removeButtonCell = document.createElement('td');
        const removeButton = document.createElement('button');
        removeButton.textContent = 'Remove Index';
        removeButton.onclick = () => removeIndex(index);
        removeButtonCell.appendChild(removeButton);
        row.appendChild(removeButtonCell);

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

// Function to add an index
async function addIndex(fields) {
    try {
        const response = await fetch('http://127.0.0.1:5000/add_index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ fields })
        });

        const result = await response.json();
        if (response.ok) {
            alert('Index added successfully');
        } else {
            alert(`Error adding index: ${result.message}`);
        }
    } catch (error) {
        console.error('Error adding index:', error);
        alert('Error adding index');
    }
}

// Function to remove an index
async function removeIndex(indexName) {
    try {
        const response = await fetch('http://127.0.0.1:5000/remove_index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ index_name: indexName })
        });

        const result = await response.json();
        if (response.ok) {
            alert('Index removed successfully');
        } else {
            alert(`Error removing index: ${result.message}`);
        }
    } catch (error) {
        console.error('Error removing index:', error);
        alert('Error removing index');
    }
}