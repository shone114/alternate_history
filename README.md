# Alternate History Engine

An AI-powered engine for generating and evolving alternate history timelines through a multi-model debate system. Features a retro CRT-style terminal interface for interacting with the timeline.

## 🌟 Features

- **Multi-Model AI Pipeline**: Uses 4 different AI models (Qwen/Grok, Gemini, DeepSeek, Llama 3.3) to generate, propose, and judge historical events
- **Daily Simulation**: Automated scheduler generates new timeline events daily
- **Terminal Interface**: Retro CRT-style terminal with green phosphor effects
- **RESTful API**: FastAPI backend with public and admin endpoints
- **MongoDB Storage**: Persistent storage for timeline, proposals, and judgements

## 🏗️ Architecture

### Backend (FastAPI + MongoDB)

The system operates on a daily cycle using a 4-step pipeline:

1. **Subtopic Generation (Qwen/Grok)**: Selects a specific focus for the day's event
2. **Model A Proposal (Gemini)**: Proposes a creative, narrative-driven event
3. **Model B Proposal (DeepSeek)**: Proposes a grounded, realistic event
4. **Model C Judgment (Groq/Llama)**: Evaluates both proposals and selects/merges the best

### Frontend (React + Vite)

- Terminal-style interface with CRT effects (scanlines, phosphor glow, flicker)
- Command-based interaction system
- Real-time API communication
- Auto-focus and loading states

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (local or remote)
- API Keys for: Qwen/Grok, Gemini, DeepSeek, Groq

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd alternate_history
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Frontend Setup**
   ```bash
   cd "alt history frontend"
   npm install
   ```

4. **Configure Environment**
   
   Create a `.env` file in the root directory:
   ```ini
   # AI Model API Keys
   AI_ML=your_qwen_api_key
   Gemini_Key=your_gemini_api_key
   OpenRouter=your_openrouter_key
   Groq=your_groq_api_key
   
   # Database
   MONGO_URI=mongodb://localhost:27017
   DB_NAME=alternate_history
   UNIVERSE_ID=cold_war_no_moon_landing
   
   # Security
   ADMIN_API_KEY=secret-admin-key
   
   # Scheduler
   ENABLE_SCHEDULER=True
   SCHEDULE_TIME=09:51
   TIMEZONE=Asia/Kolkata
   API_BASE_URL=http://localhost:8000
   ```

### Running the Application

1. **Start MongoDB** (if running locally)
   ```bash
   mongod
   ```
   
   **OR use MongoDB Atlas** (cloud)
   - Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Get your connection string from Atlas dashboard
   - Update `.env` with your Atlas URI:
     ```ini
     MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
     ```
   - See [Migration Guide](#migrating-to-mongodb-atlas) below for migrating existing data

2. **Start Backend**
   ```bash
   uvicorn app.main:app --reload
   ```
   Backend runs on `http://localhost:8000`

3. **Start Frontend**
   ```bash
   cd "alt history frontend"
   npm run dev
   ```
   Frontend runs on `http://localhost:5173`

## 🎮 Terminal Commands

### Public Commands

```bash
help                    # Show all commands
clear                   # Clear terminal
about                   # About the engine
date                    # Current date/time
info                    # Show admin key and usage

timeline [limit]        # Show recent events (default: 10)
timeline day <number>   # Show specific day's event
latest                  # Show most recent event

status                  # Show scheduler status
health                  # Show system health
```

### Admin Commands

```bash
simulate <admin-key>    # Trigger daily simulation
reset <admin-key>       # Reset universe (DESTRUCTIVE)
```

### Secret Commands (Hidden)

```bash
subtopics [limit]       # Show recent subtopics
proposals [limit]       # Show recent proposals
judgements [limit]      # Show recent judgements
```

## 📡 API Endpoints

### Public Endpoints

- `GET /timeline` - Get paginated timeline events
- `GET /timeline/latest` - Get most recent event
- `GET /timeline/{day_index}` - Get specific day's event
- `GET /subtopics` - Get paginated subtopics
- `GET /proposals` - Get paginated proposals
- `GET /judgements` - Get paginated judgements
- `GET /health` - System health check
- `GET /health/scheduler` - Scheduler status

### Admin Endpoints (Require `x-admin-key` header)

- `POST /admin/simulate/day` - Trigger simulation
- `POST /admin/reset` - Reset universe data

## 🗄️ Database Schema

### Collections

- **timeline**: Accepted events that form the canonical timeline
- **subtopics**: Daily focus areas selected by Model 0
- **proposals**: Event proposals from Models A and B
- **judgements**: Decisions from Model C
- **scheduled_jobs**: APScheduler job persistence

## 🎨 Current Universe

**Cold War Without Apollo 11 Moon Landing**

- **Divergence Point**: July 16, 1969
- **Event**: Apollo 11 launch suffers catastrophic engine failure
- **Consequence**: USSR dominates space race, US pivots to military/cyber R&D

## 🛠️ Tech Stack

### Backend
- FastAPI
- MongoDB (local or Atlas cloud)
- APScheduler
- Pydantic

### Frontend
- React 19
- Vite
- Vanilla CSS (CRT effects)

### AI Models
- Qwen/Grok (via OpenRouter)
- Google Gemini Flash
- DeepSeek (via OpenRouter)
- Llama 3.3 70B (via Groq)

## 📝 Development

### Project Structure

```
alternate_history/
├── app/
│   ├── routers/          # API route handlers
│   ├── services/         # Business logic (pipeline, LLM, scheduler)
│   ├── utils/            # Utilities (logging, prompts)
│   ├── config.py         # Configuration management
│   ├── database.py       # MongoDB connection
│   ├── dependencies.py   # FastAPI dependencies
│   ├── models.py         # Pydantic models
│   └── main.py           # FastAPI app entry point
├── alt history frontend/
│   ├── src/
│   │   ├── App.jsx       # Main terminal component
│   │   ├── api.js        # API service layer
│   │   ├── App.css       # Component styles
│   │   └── index.css     # Global styles + CRT effects
│   └── package.json
├── universe/
│   ├── universe_seed.json      # Universe configuration
│   ├── subtopic_prompt.txt     # Model 0 prompt
│   ├── model_A_prompt.txt      # Model A prompt
│   ├── model_B_prompt.txt      # Model B prompt
│   └── model_C_prompt.txt      # Model C prompt
├── .env                  # Environment variables (not in repo)
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔒 Security Notes

- **Admin Key**: Change `ADMIN_API_KEY` in production
- **CORS**: Currently allows all origins - restrict in production
- **API Keys**: Never commit `.env` file to version control
- **Rate Limiting**: Not implemented - add for production

## 📦 Migrating to MongoDB Atlas

If you're currently using local MongoDB and want to migrate to MongoDB Atlas (cloud):

### Step 1: Export Local Data

```bash
python migrate_to_atlas.py --export
```

This creates a `mongodb_export/` directory with JSON files containing all your data.

### Step 2: Update .env with Atlas URI

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Get your connection string from the Atlas dashboard
3. Update your `.env` file:
   ```ini
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace `<username>`, `<password>`, and `<cluster>` with your actual values

### Step 3: Import to Atlas

```bash
python migrate_to_atlas.py --import
```

This uploads all your data to MongoDB Atlas.

### Step 4: Verify Migration

```bash
python migrate_to_atlas.py --verify
```

This compares document counts between local and Atlas to ensure everything migrated correctly.

### Quick Migration (All Steps)

```bash
python migrate_to_atlas.py --full
```

Runs export, import, and verification in one command.

### Troubleshooting

**Connection Timeout**
- Check your Atlas cluster is running
- Verify your IP address is whitelisted in Atlas Network Access
- Ensure your connection string is correct

**Authentication Failed**
- Double-check username and password in connection string
- Ensure the database user has read/write permissions

**Import Errors**
- Make sure you ran `--export` first
- Check that `mongodb_export/` directory exists with JSON files

## 📄 License

MIT License - feel free to use and modify

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🐛 Known Issues

- No rate limiting on API endpoints
- CORS allows all origins
- No user authentication system
- Scheduler runs in single thread

## 🚀 Future Enhancements

- [ ] User authentication and multi-user support
- [ ] Multiple universe support
- [ ] Timeline branching and parallel universes
- [ ] Export timeline to PDF/ePub
- [ ] WebSocket for real-time updates
- [ ] Timeline visualization graphs
- [ ] Command history (up/down arrows)
- [ ] Auto-complete for commands

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for exploring what-if scenarios**
