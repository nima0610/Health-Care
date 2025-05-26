// Chatbot data is now embedded directly in JS
const chatbotData = {
  "intents": [
    {
      "tag": "greeting",
      "patterns": ["hi", "hello", "hey", "good morning", "good evening"],
      "responses": [
        "Hello! How can I help you today?",
        "Hi there! What can I assist you with?",
        "Hey! Need any medical advice?"
      ]
    },
    {
      "tag": "thanks",
      "patterns": ["thanks", "thank you", "thx", "thankyou"],
      "responses": [
        "You're welcome!",
        "Happy to help!",
        "Any time!"
      ]
    },
    {
      "tag": "goodbye",
      "patterns": ["bye", "goodbye", "see you", "take care"],
      "responses": [
        "Goodbye! Stay safe and healthy.",
        "Take care! Let me know if you need anything else.",
        "See you again soon!"
      ]
    },
    {
      "tag": "headache",
      "patterns": ["headache", "my head hurts"],
      "responses": [
        "For a headache, try resting in a quiet, dark room and drink plenty of water.",
        "Consider taking an over-the-counter pain reliever if the headache persists."
      ]
    },
    {
      "tag": "fever",
      "patterns": ["fever", "i have a fever"],
      "responses": [
        "Stay cool, hydrated, and rest. If your temperature goes above 102°F (38.9°C), consult a doctor.",
        "Fever may indicate an infection. Monitor symptoms and rest well."
      ]
    },
    {
      "tag": "cough",
      "patterns": ["cough", "i have a cough"],
      "responses": [
        "Try a warm drink with honey, and avoid cold air. If the cough lasts more than a few days, see a doctor.",
        "Persistent cough? Try lozenges or warm tea. Get medical help if it worsens."
      ]
    },
     {
      "tag": "swelling",
      "patterns": ["swelling"],
      "responses": [
        "Put ice on it and show it to doctor if the situation worsens"
      ]
    },
    {
      "tag": "sore_throat",
      "patterns": ["sore throat", "throat pain", "scratchy throat"],
      "responses": [
        "Try drinking warm liquids and avoid cold drinks. Gargling salt water can help too.",
        "A sore throat can be caused by a virus. If it lasts more than 3 days, consider seeing a doctor."
      ]
    },
    {
      "tag": "nausea",
      "patterns": ["nausea", "nauseous", "feel like vomiting"],
      "responses": [
        "Try sipping ginger tea or clear fluids. Avoid heavy meals until you feel better.",
        "Rest and stay hydrated. If nausea continues or worsens, talk to a doctor."
      ]
    }
  ]
};

// Helper function to check if a keyword is negated in the input
function isNegated(input, keyword) {
  const negations = ["no", "not", "don't", "never", "dont", "doesn't"];
  const words = input.split(/\s+/);
  const index = words.findIndex(word => word.includes(keyword));
  if (index === -1) return false;

  const start = Math.max(0, index - 3);
  const contextWords = words.slice(start, index);
  return contextWords.some(word => negations.includes(word));
}

// Main function to generate chatbot replies
function generateReply(userText) {
  const cleanedInput = normalize(userText);

  if (cleanedInput.includes("how are you")) {
    return "I'm just a chatbot, but I'm doing great! How can I assist you today?";
  }

  if (cleanedInput.includes("what are you")) {
    return "I'm a healthcare chatbot here to assist you with your questions.";
  }

  if (cleanedInput.includes("who are you")) {
    return "I'm your friendly healthcare assistant chatbot.";
  }

  // Check all intents
  for (const intent of chatbotData.intents) {       //loop to check for all symptoms or tags.
    for (const pattern of intent.patterns) {
      const normalizedPattern = normalize(pattern);
      if (cleanedInput.includes(normalizedPattern)) {
        // Check for negation if it's a symptom
        if (isNegated(cleanedInput, normalizedPattern)) {
          return `Okay, I understand you don’t have ${pattern}.`;
        }
        const responses = intent.responses;
        return responses[Math.floor(Math.random() * responses.length)];
      }
    }
  }

  // Fallback if no matches found
  return "I'm sorry, I didn't understand that. Could you please rephrase?";
}

// Function to handle user input and append messages
function getResponse() {
  const userInput = document.getElementById("userInput");
  const userText = userInput.value.trim();

  if (!userText) return;

  appendMessage("user", userText);
  userInput.value = "";

  const reply = generateReply(userText);
  setTimeout(() => appendMessage("bot", reply), 500);
}

// Append messages to chatbox
function appendMessage(sender, message) {
  const chatbox = document.getElementById("chatbox");
  const msg = document.createElement("div");
  msg.className = sender;
  msg.innerHTML = message.replace(/\n/g, "<br>");
  chatbox.appendChild(msg);
  chatbox.scrollTop = chatbox.scrollHeight;
}

// Normalize text for easier matching
function normalize(text) {
  return text.toLowerCase().replace(/[^a-z0-9\s]/gi, "").trim();
}

// Send message on Enter key
document.getElementById("userInput").addEventListener("keydown", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    getResponse();
  }
});

// Initial greeting
window.onload = () => {
  const greetings = [
    "Hi! I'm your healthcare assistant. How can I help you today?",
    "Hello! Tell me how you're feeling.",
    "Welcome! Let me know if you have any symptoms you'd like to discuss."
  ];
  appendMessage("bot", greetings[Math.floor(Math.random() * greetings.length)]);
};
