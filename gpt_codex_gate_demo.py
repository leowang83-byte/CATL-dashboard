import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from agents import Agent, Runner, set_default_openai_api, set_default_openai_key
from agents.mcp import MCPServerStdio


PROJECT_DIR = r"C:\lithium_news_system"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plan with GPT first; call Codex only after explicit approval."
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="Natural-language task for GPT to plan.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Allow the script to start Codex MCP after planning.",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Required together with --execute. This is the explicit approval gate.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Planner model override. Defaults to GPT_PLANNER_MODEL, then OPENAI_MODEL, then gpt-5.5.",
    )
    parser.add_argument(
        "--offline-demo",
        action="store_true",
        help="Show the approval gate without calling the OpenAI API. Codex still will not start unless approved.",
    )
    return parser.parse_args()


def configure_openai():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from the environment or .env file.")
    set_default_openai_key(api_key)
    set_default_openai_api("responses")


async def make_plan(task, model):
    planner = Agent(
        name="GPT Planner",
        model=model,
        instructions=(
            "You are a planning agent for a local Streamlit dashboard project. "
            "You must not claim that code was changed. You only decide whether Codex execution is needed. "
            "If execution is useful, produce one consolidated Codex task, not a stream of small commands. "
            "Keep the plan scoped to C:\\lithium_news_system. "
            "Respect these project rules: dashboard.py is the production entrypoint; avoid side copies; "
            "preserve calculations and CSV/schema assumptions unless the user asks for logic changes; "
            "prefer python -m py_compile dashboard.py as a quick verification for dashboard edits."
        ),
    )

    prompt = f"""
User task:
{task}

Return in Chinese with exactly these five sections:
1. Is Codex execution needed?
2. Why?
3. Single task proposed for Codex
4. Risk notice before execution
5. Suggested command if the user approves

The suggested command must use this shape:
python gpt_codex_gate_demo.py --execute --approve "<task>"
"""
    result = await Runner.run(planner, prompt)
    return result.final_output


def make_offline_demo_plan(task):
    return f"""1. 是否需要 Codex 执行
需要，但只在你确认后执行。当前演示模式不会启动 Codex。

2. 原因
这个任务涉及本地项目 C:\\lithium_news_system 的文件检查或修改，适合交给 Codex 读取代码、执行命令和验证结果。

3. 拟交给 Codex 的单条任务
{task}

4. 执行前风险提示
Codex 可能读取项目文件、运行检查命令，若任务包含修改，则可能改动 dashboard.py 或相关文件。脚本会要求显式 --execute --approve 才进入 Codex 阶段。

5. 如果用户确认，建议运行的命令
python gpt_codex_gate_demo.py --execute --approve "{task}"
"""


async def execute_with_codex(task, model):
    async with MCPServerStdio(
        name="Codex Executor",
        params={
            "command": "codex",
            "args": ["mcp-server"],
        },
        client_session_timeout_seconds=360000,
    ) as codex_mcp:
        executor = Agent(
            name="Codex Executor Controller",
            model=model,
            instructions=(
                "You control Codex through MCP. Call the Codex MCP tool only once. "
                "The Codex session must use cwd=C:\\lithium_news_system, sandbox=workspace-write, "
                "and approval-policy=on-request. Ask Codex to implement or inspect exactly the approved task. "
                "Do not add unrelated refactors. Tell Codex to report files changed and verification results."
            ),
            mcp_servers=[codex_mcp],
        )

        result = await Runner.run(
            executor,
            (
                "Approved Codex task:\n"
                f"{task}\n\n"
                "Call Codex once with this task. Use cwd=C:\\lithium_news_system, "
                "sandbox=workspace-write, approval-policy=on-request."
            ),
        )
        return result.final_output


async def main():
    args = parse_args()

    task = " ".join(args.task).strip()
    if not task:
        task = "Check whether this project is ready for GPT-to-Codex handoff. Explain only; do not edit files."

    model = args.model or os.getenv("GPT_PLANNER_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.5"

    print("=== GPT planning phase ===")
    print(f"Project: {PROJECT_DIR}")
    print(f"Model: {model}")
    print("Codex MCP started: no")
    print()

    if args.offline_demo:
        plan = make_offline_demo_plan(task)
    else:
        configure_openai()
        try:
            plan = await make_plan(task, model)
        except Exception as exc:
            print("GPT planning failed before Codex was started.")
            print(f"Error type: {type(exc).__name__}")
            print(f"Error: {exc}")
            print("\n=== Gate ===")
            print("Codex was not started. Fix the API issue or rerun with --offline-demo to inspect the approval flow.")
            return

    print(plan)

    if not args.execute:
        print("\n=== Gate ===")
        print("Codex was not started. Add --execute --approve if you want to run the approved Codex task.")
        return

    if not args.approve:
        print("\n=== Gate ===")
        print("--execute was provided, but --approve is missing. Codex will not start.")
        sys.exit(2)

    print("\n=== Codex execution phase ===")
    print("Codex MCP started: yes")
    execution_result = await execute_with_codex(task, model)
    print(execution_result)


if __name__ == "__main__":
    asyncio.run(main())
