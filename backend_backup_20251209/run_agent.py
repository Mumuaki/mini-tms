import asyncio
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.automation import (
    TranseuAgent, 
    AsyncAgentObserver, 
    AsyncPyautoguiActionHandler, 
    AsyncScreenshotMaker
)

# Default Todos if none provided
DEFAULT_TODOS = [
    "Открыть браузер и перейти на https://platform.trans.eu/exchange/offers",
    "Если требуется вход, ввести логин и пароль",
    "Установить фильтр 'Загрузка' (Loading) в значение '{origin}'",
    "Установить фильтр 'Разгрузка' (Unloading) в значение '{destination}'",
    "Нажать кнопку 'Поиск'",
    "Дождаться загрузки результатов",
    "Проанализировать первые 3 предложения (цена, расстояние)"
]

async def main():
    parser = argparse.ArgumentParser(description="Run Trans.eu Agentic Automation")
    
    parser.add_argument("--origin", "-o", default="Warszawa", help="Origin location")
    parser.add_argument("--destination", "-d", default="Berlin", help="Destination location")
    parser.add_argument("--model", default="gpt-4o", help="Vision Model Name")
    parser.add_argument("--max-steps", type=int, default=20, help="Max steps per run")
    parser.add_argument("--temperature", type=float, default=0.0, help="Model temperature")
    parser.add_argument("--output", default="agent_report.html", help="Output report file")
    parser.add_argument("--todos-file", help="Path to a JSON or text file containing custom todos")
    
    args = parser.parse_args()
    
    # Validate API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        print("Please set it to use the Vision Agent.")
        return

    print("=" * 60)
    print(f"Starting Trans.eu Agent ({args.model})")
    print(f"Task: Find freights {args.origin} -> {args.destination}")
    print("=" * 60)

    # 1. Initialize Components
    observer = AsyncAgentObserver()
    observer.set_agent_name("TransEuBot")
    
    action_handler = AsyncPyautoguiActionHandler()
    image_provider = AsyncScreenshotMaker(save_history=True)
    
    # 2. Initialize Agent
    agent = TranseuAgent(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model_name=args.model,
        step_observer=observer,
        max_steps=args.max_steps,
        temperature=args.temperature
    )
    
    # 3. Prepare Todos
    raw_todos = DEFAULT_TODOS
    
    # Load from file if provided
    if args.todos_file:
        file_path = args.todos_file
        if os.path.exists(file_path):
            try:
                if file_path.endswith('.json'):
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Support both list of strings or object with "todos" key
                        if isinstance(data, list):
                            raw_todos = data
                        elif isinstance(data, dict) and "todos" in data:
                            raw_todos = data["todos"]
                else:
                    # Text file: one todo per line
                    with open(file_path, 'r', encoding='utf-8') as f:
                        raw_todos = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print(f"Loaded {len(raw_todos)} todos from {file_path}")
            except Exception as e:
                print(f"Error loading todos file: {e}")
                return
        else:
            print(f"Error: Todos file not found: {file_path}")
            return

    # Inject variables into todos
    try:
        todos_text = [
            t.format(origin=args.origin, destination=args.destination) 
            for t in raw_todos
        ]
    except KeyError as e:
        print(f"Error: Your custom todos contain a placeholder {e} that is not supported.")
        print("Supported placeholders: {origin}, {destination}")
        return
    
    instruction = f"Find freight offers from {args.origin} to {args.destination} on Trans.eu."
    
    agent.set_task(instruction, todos_text)
    
    # 4. Execute
    try:
        # Give user 3 seconds to switch to the correct screen if needed
        print("\nWARNING: Automation starting in 3 seconds. Switch to the browser window if needed!")
        await asyncio.sleep(3)
        
        await agent.execute(action_handler, image_provider)
        
        print("\nExecution finished.")
        
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"\nCritical Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 5. Export Report
        await observer.export("html", args.output)
        print(f"Report saved to: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    # Note: WindowsProactorEventLoopPolicy is deprecated in Python 3.14+
    # Only set it if on older Python versions
    if sys.platform == 'win32' and sys.version_info < (3, 14):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
