"""Streamlit interface for the Study Group Crew application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from crew import generate_study_guide


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "study_guide.txt"

AGENT_DESCRIPTIONS = (
    ("Topic Researcher", "Finds relevant educational information using web search and Wikipedia."),
    ("Explainer", "Turns technical material into clear, beginner-friendly notes."),
    ("Quiz Maker", "Creates multiple-choice questions with answers and explanations."),
    ("Fact Checker", "Reviews the source material and prior outputs for accuracy and consistency."),
)


def _task_progress(task_output: Any) -> str:
    description = getattr(task_output, "description", "")
    first_line = description.strip().splitlines()[0] if description else "Workflow task"
    return first_line[:100]


def main() -> None:
    load_dotenv(PROJECT_DIR / ".env")
    st.set_page_config(page_title="Study Group Crew", page_icon="📚", layout="wide")

    with st.sidebar:
        st.title("Study Group Crew")
        st.caption("A four-agent educational assistant")
        st.subheader("Agents")
        for name, description in AGENT_DESCRIPTIONS:
            st.markdown(f"**{name}**")
            st.caption(description)

    st.title("Build a Study Guide")
    st.write("Enter a topic to generate research notes, an explanation, a quiz, and a fact-checked guide.")
    topic = st.text_input("Study topic", placeholder="For example: photosynthesis")

    if st.button("Generate Study Guide", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Enter a study topic before generating a guide.")
        else:
            try:
                with st.status("Preparing your study guide...", expanded=True) as status:
                    status.write("Running the research, explanation, quiz, and fact-check tasks in sequence.")
                    result = generate_study_guide(topic.strip(), on_task_complete=lambda output: status.write(
                        f"Completed: {_task_progress(output)}"
                    ))
                    st.session_state["study_guide_result"] = result
                    status.update(label="Study guide generated", state="complete", expanded=False)
            except Exception as exc:  # Streamlit should show a useful error instead of crashing.
                st.error(f"Could not generate the study guide: {exc}")

    result = st.session_state.get("study_guide_result")
    if not result:
        return

    st.subheader("Research Notes")
    st.markdown(result["research"])
    st.subheader("Explanation")
    st.markdown(result["explanation"])
    st.subheader("Quiz")
    st.markdown(result["quiz"])
    st.subheader("Final Study Guide")
    st.markdown(result["study_guide"])

    download_col, save_col = st.columns(2)
    with download_col:
        st.download_button(
            "Download Study Guide",
            data=result["study_guide"],
            file_name="study_guide.txt",
            mime="text/plain; charset=utf-8",
            use_container_width=True,
        )
    with save_col:
        if st.button("Save Output", use_container_width=True):
            try:
                OUTPUT_PATH.write_text(result["study_guide"], encoding="utf-8")
                st.success(f"Study guide saved to {OUTPUT_PATH.name}.")
            except OSError as exc:
                st.error(f"Could not save the study guide: {exc}")


if __name__ == "__main__":
    main()