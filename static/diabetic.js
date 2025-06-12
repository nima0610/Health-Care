document.getElementById('diabetesForm').addEventListener('submit', async function(e) {
  e.preventDefault();

  const formData = new FormData(e.target);
  const data = Object.fromEntries(formData.entries());

  // Convert all form input values to float
  for (let key in data) {
    data[key] = parseFloat(data[key]);
  }

  const resultElement = document.getElementById('result');
  resultElement.style.color = "#000"; // Reset color
  resultElement.innerText = "Predicting..."; // Optional loading indicator

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Server returned an error');
    }

    const result = await response.json();

    if (result.prediction === 1) {
      resultElement.innerText = "Prediction: You likely have diabetes.";
      resultElement.style.color = "#c62828"; // red
    } else if (result.prediction === 0) {
      resultElement.innerText = "Prediction: You are likely not diabetic.";
      resultElement.style.color = "#2e7d32"; // green
    } else {
      resultElement.innerText = "Unexpected result from server.";
      resultElement.style.color = "#ff9800"; // orange
    }

  } catch (error) {
    console.error('Error during prediction:', error);
    resultElement.innerText = "An error occurred. Please try again.";
    resultElement.style.color = "#ff9800"; // orange
  }
});
