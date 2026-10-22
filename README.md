# Study Group Crew

Study Group Crew is a Streamlit study assistant powered by a sequential CrewAI workflow. It researches a topic, explains it in beginner-friendly language, creates a multiple-choice quiz, and checks the complete guide for accuracy and consistency.

## Requirements

- Python 3.10 through 3.13 (CrewAI does not currently support Python 3.14)
- A Google AI Studio API key with access to the configured Gemini model
- Network access for DuckDuckGo and Wikipedia searches

## Setup

1. Create and activate a virtual environment:

	```bash
	python -m venv .venv
	source .venv/bin/activate
	```

	On Windows, activate it with `.venv\Scripts\activate`.

2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Add your key to the local `.env` file:

	```env
	GOOGLE_API_KEY=your_google_api_key
	GEMINI_MODEL=gemini/gemini-2.5-flash
	```

	`.env` is ignored by Git. Never commit API keys. The model identifier is configurable; use a Gemini model currently supported by your Google API account.

4. Run the app:

	```bash
	streamlit run app.py
	```

## Workflow

The application runs four tasks with `Process.sequential`:

1. Topic Researcher searches the web and Wikipedia for relevant information.
2. Explainer uses the research task output to create accessible notes.
3. Quiz Maker uses the explanation task output to create multiple-choice questions and an answer key.
4. Fact Checker receives the research, explanation, and quiz task outputs, checks consistency, and produces the final study guide.

The page displays each intermediate result and the final combined guide. Use **Download Study Guide** to download a text file or **Save Output** to write `study_guide.txt` in the project directory. Saving overwrites the previous generated guide.

## Project Files

- `app.py`: Streamlit interface, progress reporting, downloads, and local save action.
- `crew.py`: CrewAI agents, LangChain search tools, tasks, and workflow configuration.
- `requirements.txt`: Python dependencies.
- `.env.example`: Environment variable template.
- `reflection.txt`: Project reflection and known limitations.
- `study_guide.txt`: Output destination, populated when Save Output is used.

## Notes

Search results and model responses can be incomplete or incorrect. The fact-checking agent is a review step, not a guarantee of correctness. Verify important academic material against primary or instructor-approved sources. Search tools require network access, and Google API usage may incur charges or be subject to account quotas.