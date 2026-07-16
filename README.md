# Weather-Chat-Bot
AI-powered Weather Chatbot built with Flask, Groq NLP, and Open Weather API that provides real-time weather updates through a conversational chat interface.

🌦 Weather Chatbot

This project is an AI-powered Weather Chatbot that allows users to check weather conditions through a conversational interface.

The chatbot understands natural language queries such as:

"What's the weather in Delhi?"

"Do I need an umbrella today?"

"Is it good weather for a walk?"


It uses Groq's LLM (Llama3) for natural language understanding and OpenWeather API to fetch real-time weather data.


---

⚙️ Features

💬 Conversational weather chatbot

🌍 Detects city names from user messages

☔ Umbrella recommendation based on rain conditions

🚶 Suggests if weather is suitable for a walk

📊 Displays temperature, humidity, and wind speed

🧠 Uses Groq NLP for intent and entity extraction

🧭 Remembers the last city mentioned in the chat



---

🛠 Tech Stack

Backend: Python (Flask)

Frontend: HTML, CSS, JavaScript

AI/NLP: Groq API (Llama3 model)

Weather Data: OpenWeather API

Environment Management: python-dotenv



---

🔄 How It Works

1. User sends a message in the chatbot interface.


2. Flask backend receives the message.


3. Groq NLP analyzes the message to detect intent and city name.


4. The backend fetches weather data from the OpenWeather API.


5. The chatbot formats the response and sends it back to the user.




---

🚀 Example Queries

weather in Mumbai

forecast for London

should I take an umbrella?

is it good weather for a walk?



---

🔑 Environment Variables

Create a .env file with:

OPENWEATHER_API_KEY=your_openweather_api_key
GROQ_API_KEY=your_groq_api_key


---

▶️ Run the Project

pip install flask requests python-dotenv groq
python backend.py

Then open:

http://127.0.0.1:5000
