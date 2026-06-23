import urllib.parse
import yfinance as yf
import requests
from tavily import TavilyClient
from googlesearch import search
from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump  # Importing functions to read and write JSON files.
import datetime  # Importing the datetime module for real-time date and time information.
from dotenv import dotenv_values  # Importing dotenv_values to read environment variables from a .env file.

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

# Retrieve environment variables for the chatbot configuration.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client with the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define the system instructions for the chatbot (Strict Identity & Control Rules)
System = f"""Hello, I am Nishant Chaudhary. You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
CRITICAL INSTRUCTION: You have access to real-time search engine data inside [start] and [end] blocks. Always extract and prioritize the exact numbers, digits, figures, stock prices, weather degrees, or networth values provided in the search context. Do not make excuses.
*** Provide Answers In A Professional Way, make sure to add full stops, commas, question marks, and use proper grammar. ***"""

# Try to load the chat log from a JSON file, or create an empty one if it doesn't exist.
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)

# Function to perform a Google search and format the results.
def _wmo_code(code):
    table = {
        0:"Clear sky", 1:"Mainly clear", 2:"Partly cloudy", 3:"Overcast",
        45:"Fog", 48:"Icy fog",
        51:"Light drizzle", 53:"Moderate drizzle", 55:"Heavy drizzle",
        61:"Light rain", 63:"Moderate rain", 65:"Heavy rain",
        71:"Light snow", 73:"Moderate snow", 75:"Heavy snow",
        80:"Light showers", 81:"Moderate showers", 82:"Heavy showers",
        95:"Thunderstorm", 96:"Thunderstorm with hail",
    }
    return table.get(code, f"Code {code}")


def GoogleSearch(query):
    try:
        query_lower = query.lower().strip()
        ticker = None                  # ← YEH LINE ADD KARO
        headers = {
            "User-Agent": "Mozilla/5.0 ...",
            "Accept": "application/json"
        }

        TICKER_MAP = {
    "nifty":       "%5ENSEI",
    "sensex":      "%5EBSESN",
    "nsei":        "%5ENSEI",     # ← Zomato ab Eternal Ltd hai
    "eternal":     "ETERNAL.NS",
    "tata motors": "TTM",            # ← US listed ticker works better
    "tata":        "TTM",
    "reliance":    "RELIANCE.NS",
    "mrf":         "MRF.NS",         # ← naya add kiya
    "infy":        "INFY.NS",
    "infosys":     "INFY.NS",
    "wipro":       "WIPRO.NS",
    "hdfc":        "HDFCBANK.NS",
    "tesla":       "TSLA",
    "apple":       "AAPL",
    "elon":        "TSLA",
    "tata":        "TATAMOTORS.BO",   # ← BSE symbol, yfinance pe kaam karta hai
"tata motors": "TATAMOTORS.BO",
"zomato":      "ETERNAL.BO",      # ← BSE symbol try karo
"eternal":     "ETERNAL.BO",
}

        PRICE_KEYWORDS = ["price", "stock", "share", "index", "market", "trading",
                          "nifty", "sensex", "networth", "worth", "rate"]

        if any(kw in query_lower for kw in PRICE_KEYWORDS):
         ticker = None                    # ← pehle se hai
         for keyword, sym in TICKER_MAP.items():
          if keyword in query_lower:
            ticker = sym
            break

        if ticker is not None:                          # ← same level as 'for' loop
            try:
                stock    = yf.Ticker(ticker)
                info     = stock.fast_info
                price    = info.last_price
                currency = info.currency
                if price and price > 1.0:
                    return (f"The search results for '{query}' are:\n[start]\n"
                            f"Live Market Data: The current price of {ticker} "
                            f"is {currency} {price:,.2f}.\n[end]")
            except Exception as ex:
                pass

            if ".NS" in ticker or "NSEI" in ticker or "BSESN" in ticker:
                    nse_sym = ticker.replace(".NS", "").replace("%5E", "")
                    nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={nse_sym}"
                    nse_headers = {**headers, "Referer": "https://www.nseindia.com"}
                    try:
                        rs = requests.get(nse_url, headers=nse_headers, timeout=5)
                        if rs.status_code == 200:
                            lp = rs.json().get("priceInfo", {}).get("lastPrice")
                            if lp:
                                return (f"The search results for '{query}' are:\n[start]\n"
                                        f"NSE Live: Current price of {nse_sym} is ₹{lp:,.2f}.\n[end]")
                    except:
                        pass

        CITY_COORDS = {
            "meerut":    (28.98, 77.70),
            "delhi":     (28.61, 77.20),
            "mumbai":    (19.07, 72.87),
            "kolkata":   (22.57, 88.36),
            "bangalore": (12.97, 77.59),
            "hyderabad": (17.38, 78.49),
            "pune":      (18.52, 73.86),
            "chennai":   (13.08, 80.27),
        }

        if any(w in query_lower for w in ["weather", "temperature", "temp", "forecast"]):
            city = "meerut"
            for c in CITY_COORDS:
                if c in query_lower:
                    city = c
                    break
            lat, lon = CITY_COORDS[city]
            w_url = (f"https://api.open-meteo.com/v1/forecast"
                     f"?latitude={lat}&longitude={lon}"
                     f"&current_weather=true&forecast_days=1")
            wd = requests.get(w_url, timeout=5).json()
            cw   = wd.get("current_weather", {})
            temp = cw.get("temperature")
            wind = cw.get("windspeed")
            cond = _wmo_code(cw.get("weathercode", 0))
            if temp is not None:
                return (f"The search results for '{query}' are:\n[start]\n"
                        f"Live Weather ({city.title()}): Temperature {temp}°C, "
                        f"wind {wind} km/h, condition: {cond}.\n[end]")

        if any(w in query_lower for w in ["usd", "dollar", "rupee", "inr", "eur",
                                           "forex", "exchange rate", "currency"]):
            pair = "USDINR=X"
            if "eur" in query_lower:  pair = "EURINR=X"
            elif "gbp" in query_lower: pair = "GBPINR=X"
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}?interval=1m&range=1d"
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                meta  = r.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                if price:
                    return (f"The search results for '{query}' are:\n[start]\n"
                            f"Live Forex: {pair.replace('=X','')} rate is ₹{price:.4f}.\n[end]")

        ddg_url = (f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}"
                   f"&format=json&no_html=1&skip_disambig=1")
        r = requests.get(ddg_url, headers=headers, timeout=6)
        if r.status_code == 200:
            jd      = r.json()
            snippet = jd.get("Answer", "").strip() or jd.get("AbstractText", "").strip()
            if len(snippet) > 30:
                return (f"The search results for '{query}' are:\n[start]\n"
                        f"{snippet}\n[end]")

        # Tavily fallback
        try:
            tavily = TavilyClient(api_key=env_vars.get("TavilyAPIKey"))
            results = tavily.search(
                query=query,
                search_depth="basic",
                max_results=3
            )
            snippets = [r.get("content", "") for r in results.get("results", []) if r.get("content")]
            if snippets:
                combined = " ".join(snippets[:3])
                return (f"The search results for '{query}' are:\n[start]\n"
                        f"{combined}\n[end]")
        except:
            pass

    except Exception as e:
        return (f"The search results for '{query}' are:\n[start]\n"
                f"Error fetching data: {e}\n[end]")
    

# Function to clean up the answer by removing empty lines.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

# Predefined chatbot conversation system message and an initial user message.
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Function to get real-time information like the current date and time.
def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data += f"Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data

# Function to handle real-time search and response generation.
def RealtimeSearchEngine(prompt):
    global SystemChatBot, messages

    # Load the chat log from the JSON file.
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
    messages.append({"role": "user", "content": f"{prompt}"})

    # Add Google search results to the system chatbot messages.
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    # Generate a response using the Groq client.
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        temperature=0.4,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = ""

    # Concatenate response chunks from the streaming output.
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    # Clean up the response.
    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    # Save the updated chat log back to the JSON file.
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    # Remove the most recent system message from the chatbot conversation.
    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)

# Main entry point of the program for interactive querying.
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))
        

    