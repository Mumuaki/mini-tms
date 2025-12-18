import asyncio
import json
import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from .observer import AsyncAgentObserver
from .action_handler import AsyncPyautoguiActionHandler
from .screenshot_maker import AsyncScreenshotMaker
from .tools import AutomationTools
from .ocr_helper import OCRHelper

class TranseuAgent:
    """
    Agent for automating desktop browser tasks using Vision LLMs + OCR.
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str, 
        model_name: str, 
        step_observer: AsyncAgentObserver,
        max_steps: int = 50,
        temperature: float = 0.0,
        use_ocr: bool = True
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.observer = step_observer
        self.max_steps = max_steps
        self.temperature = temperature
        self.use_ocr = use_ocr
        
        self.instruction: str = ""
        self.todos: List[Dict[str, Any]] = []
        self.memory: List[Dict[str, Any]] = []
        self.current_step = 0
        
        # Initialize tools
        self.tools = AutomationTools()
        self.tool_output: Optional[str] = None
        
        # Initialize OCR
        self.ocr = OCRHelper() if use_ocr else None
        
    def set_task(self, instruction: str, todos: List[str]):
        """
        Set the task for the agent.
        
        Args:
            instruction: High-level goal.
            todos: List of specific steps to execute.
        """
        self.instruction = instruction
        self.todos = [{"id": i, "task": t, "status": "pending"} for i, t in enumerate(todos)]
        self.current_step = 0
        self.memory = []
        self.tool_output = None
        
        # Log initialization
        asyncio.create_task(self.observer.observe_step(
            "Agent Initialized", 
            details={"instruction": instruction, "todos_count": len(todos)},
            status="info"
        ))

    def get_memory(self) -> List[Dict[str, Any]]:
        return self.memory

    async def execute(
        self, 
        action_handler: AsyncPyautoguiActionHandler, 
        image_provider: AsyncScreenshotMaker
    ):
        """
        Execute the task loop.
        """
        print(f"[{self.model_name}] Starting execution...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            while self.current_step < self.max_steps:
                # 1. Check if all todos are done
                pending_todos = [t for t in self.todos if t["status"] == "pending"]
                if not pending_todos:
                    print("All todos completed!")
                    await self.observer.observe_step("Task Completed", status="success")
                    break
                
                current_todo = pending_todos[0]
                print(f"\n--- Step {self.current_step + 1} ---")
                print(f"Current Goal: {current_todo['task']}")
                
                # 2. Capture State (Screenshot)
                try:
                    b64_img = await image_provider.take_screenshot(save_tag=f"step_{self.current_step}")
                except Exception as e:
                    print(f"Screenshot failed: {e}")
                    await self.observer.observe_step("Screenshot Failed", details={"error": str(e)}, status="failed")
                    break

                # 3. Decide Action (Call LLM)
                try:
                    response_data = await self._query_model(client, b64_img, current_todo)
                    
                    action = response_data.get("action")
                    reason = response_data.get("reason", "No reason provided")
                    params = response_data.get("params", {})
                    
                    print(f"Model decision: {action} ({reason})")
                    
                    # Log the decision
                    await self.observer.observe_step(
                        f"Decided: {action}", 
                        details={"reason": reason, "params": params, "todo": current_todo['task']},
                        screenshot=b64_img,
                        status="running"
                    )
                    
                except Exception as e:
                    print(f"Model query failed: {e}")
                    await self.observer.observe_step("Model Error", details={"error": str(e)}, status="failed")
                    break

                # 4. Execute Action
                try:
                    # Reset tool output unless we just called a tool
                    if action != "call_tool":
                        self.tool_output = None
                        
                    await self._perform_action(action_handler, action, params)
                    
                    # 5. Update Memory & State
                    self.memory.append({
                        "step": self.current_step,
                        "todo": current_todo['task'],
                        "action": action,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Check if model thinks the todo is done
                    if action == "finish_todo":
                        current_todo["status"] = "completed"
                        print(f"Todo completed: {current_todo['task']}")
                        await self.observer.observe_step(f"Completed: {current_todo['task']}", status="success")
                    
                except Exception as e:
                    print(f"Action execution failed: {e}")
                    await self.observer.observe_step("Action Failed", details={"error": str(e)}, status="failed")
                
                self.current_step += 1
                await asyncio.sleep(1)  # Brief pause between steps

    async def _query_model(self, client: httpx.AsyncClient, b64_img: str, current_todo: Dict) -> Dict:
        """
        Sends the screenshot and context to the Vision LLM.
        Expected to return a JSON with 'action', 'params', and 'reason'.
        """
        
        # Get tool definitions
        tool_defs = json.dumps(self.tools.get_tool_definitions(), indent=2)
        
        tool_context = ""
        if self.tool_output:
            tool_context = f"\nPREVIOUS TOOL OUTPUT: {self.tool_output}\nUse this information to decide the next action."
        
        system_prompt = f"""
        You are a GUI automation agent. Your goal is to complete the current task: "{current_todo['task']}".
        The overall instruction is: "{self.instruction}".
        
        Analyze the screenshot and decide the next action.
        
        AVAILABLE ACTIONS:
        - click(x, y): Click at coordinates.
        - find_text(text, offset_x, offset_y): Use OCR to find text on screen and click near it. offset_x and offset_y are pixel offsets from the found text (e.g., offset_y=30 clicks 30 pixels below the text).
        - type(text): Type text.
        - press(key): Press a key (enter, tab, esc).
        - scroll(clicks): Scroll mouse wheel.
        - call_tool(name, args): Call a helper tool (e.g. calculate distance).
        - finish_todo(): Mark the current task as completed if the screen shows it's done.
        - wait(): Wait for a moment (if loading).
        
        AVAILABLE TOOLS:
        {tool_defs}
        
        {tool_context}
        
        Return ONLY a JSON object in this format:
        {{
            "action": "click",
            "params": {{"x": 100, "y": 200}},
            "reason": "Clicking the search button to find freights."
        }}
        OR for tools:
        {{
            "action": "call_tool",
            "params": {{"name": "calculate_distance", "args": {{"origin": "Warsaw", "destination": "Berlin"}}}},
            "reason": "Calculating distance to verify the offer."
        }}
        """
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Current Task: {current_todo['task']}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "temperature": self.temperature,
            "max_tokens": 300,
            "response_format": {"type": "json_object"}
        }
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON from content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback if model didn't return pure JSON (sometimes happens)
            # Try to find JSON block
            if "```json" in content:
                import re
                match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            raise Exception(f"Failed to parse JSON from model response: {content}")

    async def _perform_action(self, handler: AsyncPyautoguiActionHandler, action: str, params: Dict):
        """Executes the chosen action using the handler."""
        if action == "click":
            await handler.click(params.get("x", 0), params.get("y", 0))
        elif action == "type":
            await handler.type_text(params.get("text", ""))
        elif action == "press":
            await handler.press_key(params.get("key", "enter"))
        elif action == "scroll":
            await handler.scroll(params.get("clicks", 0))
        elif action == "wait":
            await asyncio.sleep(2)
        elif action == "finish_todo":
            pass
        elif action == "call_tool":
            tool_name = params.get("name")
            tool_args = params.get("args", {})
            print(f"Executing tool: {tool_name} with {tool_args}")
            
            if tool_name == "get_my_location":
                self.tool_output = self.tools.get_my_location(tool_args.get("vehicle_id"))
            elif tool_name == "calculate_distance":
                self.tool_output = self.tools.calculate_distance(tool_args.get("origin"), tool_args.get("destination"))
            elif tool_name == "calculate_profit":
                self.tool_output = self.tools.calculate_profit(
                    tool_args.get("price_eur", 0), 
                    tool_args.get("distance_km", 0),
                    tool_args.get("cost_per_km", 1.0)
                )
            else:
                self.tool_output = f"Error: Unknown tool {tool_name}"
                
            print(f"Tool Output: {self.tool_output}")
            await self.observer.observe_step(
                f"Tool Result: {tool_name}", 
                details={"output": self.tool_output, "args": tool_args},
                status="info"
            )
        else:
            print(f"Unknown action: {action}")
