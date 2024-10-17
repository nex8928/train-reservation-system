document.addEventListener('DOMContentLoaded', function() {
    const trainNumberInput = document.getElementById('trainNumber');
    const trainNameInput = document.getElementById('trainName');

    trainNumberInput.addEventListener('blur', function() {
        const trainNumber = trainNumberInput.value;
        if (trainNumber) {
            fetch(`/get_train_name?train_number=${trainNumber}`)
                .then(response => response.json())
                .then(data => {
                    if (data.train_name) {
                        trainNameInput.value = data.train_name;
                    } else {
                        trainNameInput.value = 'Train not found';
                    }
                })
                .catch(error => {
                    console.error('Error fetching train name:', error);
                    trainNameInput.value = 'Error fetching train name';
                });
        }
    });
});