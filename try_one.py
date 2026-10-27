"""Run ONE agent on ONE task, verbosely. The cheapest way to learn how CrewAI behaves before running the Flow.
python try_one.py   (needs ANTHROPIC_API_KEY and SERPER_API_KEY in .env)"""
from dotenv import load_dotenv; load_dotenv()
from crewai import Crew, Task, Process
from matrix_flow.agents import source_watcher
from matrix_flow.models import SourceCheck

task = Task(
    description=(
        "Source S04: EN 18286:2026. Status on record: 'Harmonised standard cited in the OJ'. "
        "Confirm on EUR-Lex whether Commission Implementing Decision (EU) 2026/2274 still cites it. Fill every field of the schema."
    ),
    expected_output="A SourceCheck JSON object.",
    agent=source_watcher, output_pydantic=SourceCheck,
)
out = Crew(agents=[source_watcher], tasks=[task], process=Process.sequential, verbose=True).kickoff()
print(out.pydantic)
