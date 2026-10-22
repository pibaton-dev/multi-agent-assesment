"""CrewAI agents, LangChain search tools, and sequential study-guide workflow."""

from __future__ import annotations

import os
from typing import Any, Callable

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


load_dotenv()

_duckduckgo = DuckDuckGoSearchRun()
_wikipedia = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=4000)
)


@tool("DuckDuckGoSearchRun")
def duckduckgo_search(query: str) -> str:
    """Search the web for current, relevant information about an educational topic."""
    return _duckduckgo.run(query)


@tool("WikipediaQueryRun")
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for background information about an educational topic."""
    return _wikipedia.run(query)


def _output_text(task_output: Any) -> str:
    raw = getattr(task_output, "raw", None)
    return str(raw if raw is not None else task_output).strip()


def generate_study_guide(
    topic: str,
    on_task_complete: Callable[[Any], None] | None = None,
) -> dict[str, str]:
    """Run all study-guide tasks and return each task's text output."""
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("A study topic is required.")

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to your local .env file.")

    llm = LLM(
        model=os.getenv("GEMINI_MODEL", "gemini/gemini-3.8-flash"),
        api_key=api_key,
        temperature=0.2,
    )
    tools = [duckduckgo_search, wikipedia_search]

    researcher = Agent(
        role="Topic Researcher",
        goal="Gather accurate, relevant educational information about {topic}.",
        backstory="You are an academic researcher skilled at finding and comparing trustworthy sources.",
        llm=llm,
        tools=tools,
        verbose=True,
    )
    explainer = Agent(
        role="Explainer",
        goal="Convert technical content about {topic} into beginner-friendly notes.",
        backstory="You are an experienced teacher who makes complex concepts clear without distorting them.",
        llm=llm,
        verbose=True,
    )
    quiz_maker = Agent(
        role="Quiz Maker",
        goal="Create a useful multiple-choice quiz that tests understanding of {topic}.",
        backstory="You are an educational assessment specialist who writes fair questions and clear answer explanations.",
        llm=llm,
        verbose=True,
    )
    fact_checker = Agent(
        role="Fact Checker",
        goal="Verify accuracy and consistency across the study material about {topic}.",
        backstory="You are a meticulous quality assurance reviewer who distinguishes supported facts from uncertainty.",
        llm=llm,
        tools=tools,
        verbose=True,
    )

    research_task = Task(
        description=(
            "Research {topic} using DuckDuckGo and Wikipedia. Summarize core concepts, key terms, "
            "important facts, and useful examples. Prefer information supported by reliable sources; "
            "include source names and URLs when available, and flag conflicting or uncertain claims."
        ),
        expected_output="Organized research notes with key facts, definitions, examples, and available source references.",
        agent=researcher,
        callback=on_task_complete,
    )
    explanation_task = Task(
        description=(
            "Using the research task output, explain {topic} to a beginner. Define unfamiliar terms, "
            "use a logical structure and concrete examples, and preserve important qualifications. "
            "Do not add unsupported facts."
        ),
        expected_output="A clear, structured, student-friendly explanation grounded in the research notes.",
        agent=explainer,
        context=[research_task],
        callback=on_task_complete,
    )
    quiz_task = Task(
        description=(
            "Using the explanation task output, write 5 multiple-choice questions about {topic}. "
            "Each question must have four labeled options, exactly one correct answer, and a brief "
            "answer explanation. Keep every answer supported by the study material."
        ),
        expected_output="Five numbered MCQs, each with options A-D, the correct answer, and a short rationale.",
        agent=quiz_maker,
        context=[explanation_task],
        callback=on_task_complete,
    )
    fact_check_task = Task(
        description=(
            "Fact-check the research notes, explanation, and quiz for {topic}. Use the research notes "
            "as the primary reference and search tools to investigate consequential uncertainties. "
            "Correct errors, remove unsupported claims, and ensure the quiz answer key agrees with the "
            "corrected explanation. Return a concise Fact Check Summary followed by a polished final "
            "study guide with sections named Research Section, Explanation Section, and Quiz Section. "
            "Mention unresolved uncertainty instead of presenting it as fact."
        ),
        expected_output="A fact-check summary and corrected, complete study guide with all requested sections.",
        agent=fact_checker,
        context=[research_task, explanation_task, quiz_task],
        callback=on_task_complete,
    )

    crew = Crew(
        agents=[researcher, explainer, quiz_maker, fact_checker],
        tasks=[research_task, explanation_task, quiz_task, fact_check_task],
        process=Process.sequential,
        verbose=True,
    )
    crew_result = crew.kickoff(inputs={"topic": normalized_topic})
    task_outputs = getattr(crew_result, "tasks_output", []) or []
    if len(task_outputs) != 4:
        raise RuntimeError("The CrewAI workflow did not return all four task outputs.")

    research, explanation, quiz, fact_check = map(_output_text, task_outputs)
    study_guide = f"# Study Guide: {normalized_topic}\n\n{fact_check}"
    return {
        "research": research,
        "explanation": explanation,
        "quiz": quiz,
        "fact_check": fact_check,
        "study_guide": study_guide,
    }