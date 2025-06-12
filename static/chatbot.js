// Display a welcome message on page load
document.addEventListener('DOMContentLoaded', () => {
  appendMessage('HealthBot', 'Welcome! Please provide your symptoms.');

  // Enable sending message with Enter key
  document.getElementById('userInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      getResponse();
    }
  });

  // Clear chat on Clear button click
  document.getElementById('clearBtn').addEventListener('click', () => {
    const chatbox = document.getElementById('chatbox');
    chatbox.innerHTML = '';  // Clear chat messages
    appendMessage('HealthBot', 'Welcome! Please provide your symptoms.');
  });
});

// State to track follow-up questions
let followUpQuestions = [];
let collectedSymptoms = [];

// Main function to get response from backend
async function getResponse(userInputOverride) {
  const inputBox = document.getElementById('userInput');
  const userMessage = userInputOverride !== undefined ? userInputOverride : inputBox.value.trim();
  if (!userMessage) return;

  appendMessage('User', userMessage);

  // Clear input box if normal input
  if (userInputOverride === undefined) inputBox.value = '';

  // If user mentions diabetes, trigger diabetes form
  if (userMessage.toLowerCase().includes("diabetes") && followUpQuestions.length === 0) {
    appendMessage('HealthBot', 'Please fill in your details to assess diabetes risk.');
    showDiabetesForm();  // Show form for diabetes input
    return;
  }

  // Prepare message to send including previously collected symptoms
  let messageToSend = userMessage.toLowerCase();

  // If follow-up questions active, treat userMessage as answer to symptom(s)
  if (followUpQuestions.length > 0) {
    // Parse answers by splitting by comma and trimming
    const answers = userMessage.toLowerCase().split(',').map(s => s.trim());
    collectedSymptoms.push(...answers);

    // Remove duplicates
    collectedSymptoms = [...new Set(collectedSymptoms)];

    // Combine original user symptoms + collected symptoms into one message string
    messageToSend = collectedSymptoms.join(' ');
  }

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'illness', message: messageToSend })
    });

    const data = await response.json();

    if (data.follow_up) {
      // Backend wants to ask follow-up questions
      followUpQuestions = data.questions;
      appendMessage('HealthBot', `${data.message} <br> Please reply with symptoms you have from: <strong>${followUpQuestions.join(', ')}</strong>`);
    } else {
      // Reset follow-up state on normal response
      followUpQuestions = [];
      collectedSymptoms = [];

      if (data.prediction) {
        let reply = data.prediction;

        if (
          reply.toLowerCase().startsWith("sorry") ||
          reply.toLowerCase().includes("hello") ||
          reply.toLowerCase().includes("bot") ||
          reply.toLowerCase().includes("please") ||
          reply.toLowerCase().includes("welcome")
        ) {
          appendMessage('HealthBot', reply);
        } else {
          if (data.precautions && typeof data.precautions === 'string' && data.precautions.trim().length > 0) {
            const points = data.precautions.split('\n').filter(p => p.trim() !== '');
            const listHtml = '<ul>' + points.map(p => `<li>${p.trim()}</li>`).join('') + '</ul>';
            appendMessage('HealthBot', `Predicted Disease: ${reply}<br>Precautions: ${listHtml}`);
          } else {
            appendMessage('HealthBot', `Predicted Disease: ${reply}`);
          }
          if(data.plot_img_base64){
            appendMessage('HealthBot', `<img src="data:image/png;base64,${data.plot_img_base64}" alt="SVM plot" style="max-width:300px; margin-top:10px; border:1px solid #ccc;">`);
          }
        }
      } else if (data.error) {
        appendMessage('HealthBot', `Error: ${data.error}`);
      }
    }
  } catch (error) {
    console.error(error);
    appendMessage('HealthBot', 'Something went wrong. Please try again.');
  }
}

function appendMessage(sender, text) {
  const chatbox = document.getElementById('chatbox');
  const messageElem = document.createElement('div');
  messageElem.classList.add('message');
  messageElem.innerHTML = `<strong>${sender}:</strong> <span>${text}</span>`;
  chatbox.appendChild(messageElem);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// 🩺 Diabetes form logic
function showDiabetesForm() {
  // Avoid adding multiple forms
  if (document.getElementById('diabetes-form')) return;

  const formHtml = `
    <div id="diabetes-form" style="margin-top:10px; border:1px solid #ccc; padding:10px; max-width:300px;">
      <h4>Enter Diabetes Details:</h4>
      <input type="number" placeholder="Pregnancies" id="Pregnancies" min="0" /><br><br>
      <input type="number" placeholder="Glucose" id="Glucose" min="0" /><br><br>
      <input type="number" placeholder="Blood Pressure" id="BloodPressure" min="0" /><br><br>
      <input type="number" placeholder="Skin Thickness" id="SkinThickness" min="0" /><br><br>
      <input type="number" placeholder="Insulin" id="Insulin" min="0" /><br><br>
      <input type="number" placeholder="BMI" id="BMI" min="0" step="0.1" /><br><br>
      <input type="number" placeholder="Diabetes Pedigree Function" id="DiabetesPedigreeFunction" min="0" step="0.01" /><br><br>
      <input type="number" placeholder="Age" id="Age" min="0" /><br><br>
      <button onclick="submitDiabetes()">Submit</button>
    </div>
  `;
  appendMessage('HealthBot', formHtml);
}

// 🧬 Send diabetes form data to backend
async function submitDiabetes() {
  const getVal = id => parseFloat(document.getElementById(id).value);

  // Validate inputs
  const requiredFields = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'];
  for (const field of requiredFields) {
    const val = document.getElementById(field).value;
    if (val === '' || isNaN(parseFloat(val))) {
      appendMessage('HealthBot', `Please enter a valid value for ${field}.`);
      return;
    }
  }

  const data = {
    type: "diabetes",
    Pregnancies: getVal("Pregnancies"),
    Glucose: getVal("Glucose"),
    BloodPressure: getVal("BloodPressure"),
    SkinThickness: getVal("SkinThickness"),
    Insulin: getVal("Insulin"),
    BMI: getVal("BMI"),
    DiabetesPedigreeFunction: getVal("DiabetesPedigreeFunction"),
    Age: getVal("Age")
  };

  try {
    const response = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();
    if (result.prediction) {
      let reply = result.prediction;
      if (result.precautions) {
        const points = result.precautions.split('\n').filter(p => p.trim() !== '');
        const listHtml = '<ul>' + points.map(p => `<li>${p.trim()}</li>`).join('') + '</ul>';
        reply += `<br>Precautions: ${listHtml}`;
      }
      appendMessage('HealthBot', reply);
    } else if (result.error) {
      appendMessage('HealthBot', `Error: ${result.error}`);
    } else {
      appendMessage('HealthBot', 'No prediction returned.');
    }
  } catch (error) {
    console.error(error);
    appendMessage('HealthBot', 'Error during diabetes prediction.');
  }

  // Clear form from chat after submission
  const form = document.getElementById('diabetes-form');
  if (form) form.remove();
}
