# backend.py
import os
import re
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv
from groq import Groq

# ---------------------- Load environment variables ----------------------
load_dotenv()
print("Loaded API key:", os.getenv("OPENWEATHER_API_KEY"))

app = Flask(__name__)

OWM_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OWM_KEY:
    raise RuntimeError("Set OPENWEATHER_API_KEY in environment or .env")

OWM_BASE = "https://api.openweathermap.org/data/2.5"

# ---------------------- Initialize Groq NLP ----------------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------------- Utilities ----------------------
def k_to_c(k):
    """Convert Kelvin to Celsius."""
    return round(k - 273.15, 1)


def parse_message(msg: str):
    """Fallback parser (regex-based)."""
    msg = msg.strip().lower()

    city_match = re.search(r'in ([a-zA-Z\s\-]+)$', msg)
    if city_match:
        city = city_match.group(1).strip()
    else:
        city = None
        for t in reversed(msg.split()):
            if re.match(r'^[a-zA-Z\-]+$', t):
                city = t
                break

    if "forecast" in msg or "tomorrow" in msg or "next" in msg:
        intent = "forecast"
    else:
        intent = "current"

    return {"city": city, "intent": intent}


def groq_understand_message(message):
    """Use Groq NLP to extract intent and entities (like city names)."""
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intelligent NLP processor for a weather chatbot. "
                        "Extract the user's intent (current weather, forecast, walk, umbrella) "
                        "and the city name if mentioned. If the word is not a valid city, return City: None."
                    ),
                },
                {"role": "user", "content": message},
            ],
            temperature=0.2,
        )

        response = completion.choices[0].message.content
        city_match = re.search(r'city\s*:\s*([A-Za-z\s\-]+)', response, re.I)
        intent_match = re.search(r'intent\s*:\s*([A-Za-z\s\-]+)', response, re.I)

        return {
            "city": city_match.group(1).strip() if city_match else None,
            "intent": intent_match.group(1).strip().lower() if intent_match else None,
        }
    except Exception as e:
        print("Groq NLP error:", e)
        return None


def get_current_weather(city: str):
    url = f"{OWM_BASE}/weather"
    params = {"q": city, "appid": OWM_KEY}
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
    return resp.json()


def get_forecast(city: str):
    url = f"{OWM_BASE}/forecast"
    params = {"q": city, "appid": OWM_KEY}
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
    return resp.json()


@app.route('/')
def home():
    return render_template('index.html')


chat_memory = {"last_city": None}


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True)
    user_msg = body.get("message", "").lower()
    if not user_msg:
        return jsonify({"reply": "Weather info here"})

    # 🧠 Groq NLP understanding
    groq_result = groq_understand_message(user_msg)
    if groq_result and groq_result.get("city"):
        parsed = groq_result
    else:
        parsed = parse_message(user_msg)

    city = parsed.get("city")
    intent = parsed.get("intent") or "current"

    # 🧭 Basic sanity check for city names
    if city and len(city) < 3:
        city = None
    elif city and city.lower() in ["walk","wind", "weather", "rain"]:
        city = None

    if not city:
        # try to remember last known city
        city = chat_memory.get("last_city")

    # If still no valid city and not a greeting/walk intent
    if not city and not any(w in user_msg for w in ["hi", "hello", "walk","outside"]):
        return jsonify({
            "reply": "That doesn’t seem like a valid city. Try asking like 'weather in Delhi' or 'forecast for London'."
        })

    # 💬 Handle greetings
    if "hi" in user_msg or "hello" in user_msg:
        return jsonify({
            "reply": "Hello there! You can ask me 'What's the weather in Delhi?' or 'Forecast for London'."
        })

    # 🚶 Walk intent
    if "walk" in user_msg or "outside" in user_msg:
        if not city:
            return jsonify({"reply": "Tell me your city first, and I’ll check if it’s a good time for a walk 🚶‍♀️"})
        try:
            data = get_current_weather(city)
            desc = data["weather"][0]["description"].lower()
            temp = k_to_c(data["main"]["temp"])
            if "rain" in desc or "storm" in desc:
                reply = f"Better stay in — it's {desc} in {city.title()} ☔"
            elif temp < 15:
                reply = f"It’s a bit chilly in {city.title()} ({temp}°C). Take a jacket if you go for a walk 🧥"
            else:
                reply = f"Looks great for a walk! It’s {desc} and {temp}°C in {city.title()} 🌤️"
        except Exception:
            reply = f"Sorry, I couldn't check the weather in {city.title()} right now."
        return jsonify({"reply": reply})

    # ☔ Umbrella intent
        # ☔ Umbrella intent (fixed)
    if "umbrella" in user_msg or "rain" in user_msg:
        # Avoid treating "umbrella" or "rain" as city
        if city and city.lower() in ["umbrella", "rain", "raining"]:
            city = chat_memory.get("last_city")

        # If still no valid city
        if not city:
            return jsonify({
                "reply": "Tell me your city first — for example, 'weather in Chennai' — then I’ll tell you if you need an umbrella ☔."
            })

        try:
            data = get_current_weather(city)
            desc = data["weather"][0]["description"].lower()

            if any(w in desc for w in ["rain", "drizzle", "thunderstorm"]):
                reply = f"Yes, you should take an umbrella — it's {desc} in {city.title()} ☔"
            else:
                reply = f"No umbrella needed — it's {desc} in {city.title()} 🌤️"
        except Exception as e:
            print("Umbrella intent error:", e)
            reply = f"Sorry, I couldn't check the weather in {city.title()} right now."

        return jsonify({"reply": reply})

    # 🌤️ Normal weather queries
    if not city:
        return jsonify({"reply": "Please tell me which city to check (e.g. 'weather in Mumbai')."})

    chat_memory["last_city"] = city

    try:
        if intent == "current":
            data = get_current_weather(city)
            desc = data["weather"][0]["description"].capitalize()
            temp_c = k_to_c(data["main"]["temp"])
            feels = k_to_c(data["main"].get("feels_like", data["main"]["temp"]))
            humidity = data["main"]["humidity"]
            wind = data["wind"].get("speed", 0)
            reply = (
                f"Current weather in {data['name']}: {desc}. "
                f"Temp: {temp_c}°C (feels like {feels}°C). "
                f"Humidity: {humidity}%. Wind: {wind} m/s."
            )
            return jsonify({"reply": reply, "source": "openweathermap", "raw": data})
        else:
            data = get_forecast(city)
            city_name = data["city"]["name"]
            items = data.get("list", [])[:3]
            summary_parts = []
            for it in items:
                dt_txt = it["dt_txt"]
                desc = it["weather"][0]["description"]
                temp = k_to_c(it["main"]["temp"])
                summary_parts.append(f"{dt_txt}: {desc}, {temp}°C")
            reply = f"Forecast for {city_name} (next entries):\n" + "\n".join(summary_parts)
            return jsonify({"reply": reply, "source": "openweathermap", "raw": data})
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        if code == 404:
            return jsonify({"reply": f"Sorry, '{city}' not found. Try asking about another city."}), 404
        return jsonify({"reply": "Sorry — I couldn't fetch weather right now."}), 500
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500


# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
