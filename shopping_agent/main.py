"""
main.py
-------
Simple CLI chat loop for the AI Shopping Recommendation Agent.

Usage:
    python main.py
"""

import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from agent import ShoppingAgentSession

load_dotenv()
console = Console()


def main():
    console.print("[bold cyan]ShopScout — AI Shopping Recommendation Agent[/bold cyan]")
    console.print(
        "Tell me what you want to buy (category, budget, must-have features). "
        "Type 'exit' to quit.\n"
    )

    try:
        session = ShoppingAgentSession()
    except RuntimeError as e:
        console.print(f"[bold red]Setup error:[/bold red] {e}")
        sys.exit(1)

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            console.print("Goodbye!")
            break
        if not user_input.strip():
            continue

        with console.status("[cyan]ShopScout is thinking...[/cyan]"):
            try:
                reply = session.ask(user_input)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue

        console.print("\n[bold magenta]ShopScout:[/bold magenta]")
        console.print(Markdown(reply))
        console.print()


if __name__ == "__main__":
    main()
