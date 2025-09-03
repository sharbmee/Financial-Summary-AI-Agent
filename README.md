# 📊 Financial Markets CrewAI  

An AI-powered **multi-agent system** that fetches financial news, summarizes it, formats it for Telegram, and translates it into multiple languages using **CrewAI**.  

This project is designed to automate **daily financial market summaries** with insights from major indices, corporate news, and Federal Reserve updates — all delivered directly to a Telegram channel.  

---

## 🚀 Features  
- 🔍 **Web Search Agent** (Tavily) → Finds latest U.S. financial market news  
- 📝 **Summary Agent** → Creates concise under-500-word daily market summaries  
- 🎨 **Formatting Agent** → Optimizes summaries for Telegram with HTML + emojis  
- 🌐 **Translation Agent** → Translates content into **Arabic, Hindi, and Hebrew**  
- 📲 **Telegram Bot Integration** → Auto-posts updates to a channel  
- 🛡️ Logging system with fallback **sample output** if API calls fail  

---

## 🛠️ Tech Stack  
- **Language:** Python  
- **Framework:** [CrewAI](https://github.com/joaomdmoura/crewai)  
- **LLM Provider:** Any supported via litellm / OpenAI  
- **Search API:** [Tavily](https://tavily.com/)  
- **Messaging:** Telegram Bot API  
- **Logging:** Python logging module  

---

## 📂 Project Structure  
```

financial-markets-crew/
│── financial\_crew\.py   # Main implementation with agents, tasks, and workflow
│── requirements.txt    # Dependencies
│── .env.example        # Example environment variables
│── README.md           # Project documentation
│── financial\_markets\_summary.log  # Runtime logs (generated)

````

---

## ⚡ Quick Start  

### 1️⃣ Clone the Repo  
```bash
git clone https://github.com/sharbmee/Financial-Summary-AI-Agent.git
cd financial-markets-crew
````

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Environment Variables

Create a `.env` file with the following:

```ini
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHANNEL_ID=@your-channel-id
```

### 4️⃣ Run the Workflow

```bash
python financial_crew.py
```

---

## 📖 Example Output

When executed, the system generates a summary like this:

```
📊 Daily Financial Markets Summary
December 15, 2023 | US Markets Close

📈 Market Overview:
U.S. stocks closed mixed on Thursday as investors digested the Fed’s policy decision. 
Dow +0.4%, S&P 500 +0.1%, Nasdaq -0.3%.

🔑 Key News:
• Fed holds rates steady, signals cuts in 2024  
• Retail sales rose 0.6% in November  
• Adobe shares fell 6% on weak forecast  
• Oil +2.3% amid supply concerns  

🔮 Outlook:
Markets remain volatile; focus shifts to housing and consumer sentiment.
```

It also includes translations in **Arabic, Hindi, Hebrew** and is formatted with **Telegram HTML + emojis**.

---

## 🔮 Future Enhancements

* 🌍 More translation languages
* 📈 Integration with real-time stock/crypto APIs (Yahoo Finance, Alpha Vantage)
* 🌐 Web dashboard for viewing summaries
* ⏱️ Scheduler for automatic daily execution

---

## 🤝 Contributing

Pull requests are welcome! Please fork the repo and submit a PR.

---

## 📜 License

MIT License © 2025 \Arabaj Hashmee

