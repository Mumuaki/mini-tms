import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiofiles

class AsyncAgentObserver:
    """
    Asynchronous observer that records the execution history of an automation agent.
    It tracks steps, logs, screenshots, and errors, and can export this history to HTML/JSON.
    """
    
    def __init__(self):
        self.steps: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.agent_name = "UnknownAgent"
        
    def set_agent_name(self, name: str):
        self.agent_name = name

    async def observe_step(self, step_name: str, details: Dict[str, Any] = None, screenshot: str = None, status: str = "success"):
        """
        Record a single step in the agent's execution.
        
        Args:
            step_name: Short description of the step (e.g., "Click Login Button").
            details: Dictionary with additional context (e.g., {"selector": "#btn", "retries": 1}).
            screenshot: Base64 encoded screenshot string (optional).
            status: Status of the step ("success", "failed", "running", "info").
        """
        step_record = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "details": details or {},
            "screenshot": screenshot  # Base64 string
        }
        self.steps.append(step_record)
        
        # Optional: Print to console for real-time feedback
        symbol = "✓" if status == "success" else "✗" if status == "failed" else "ℹ"
        print(f"[{self.agent_name}] {symbol} {step_name}")

    async def export(self, format_type: str = "html", output_file: str = "agent_history.html"):
        """
        Export the recorded history to a file.
        
        Args:
            format_type: "html" or "json".
            output_file: Path to the output file.
        """
        if format_type.lower() == "json":
            await self._export_json(output_file)
        elif format_type.lower() == "html":
            await self._export_html(output_file)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    async def _export_json(self, output_file: str):
        data = {
            "agent": self.agent_name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "steps": self.steps
        }
        async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"History exported to JSON: {output_file}")

    async def _export_html(self, output_file: str):
        """Generates a self-contained HTML report with embedded screenshots."""
        
        duration = datetime.now() - self.start_time
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Agent Execution Report - {self.agent_name}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; color: #333; }}
                .container {{ max_width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ margin-top: 0; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                .meta {{ color: #7f8c8d; margin-bottom: 20px; font-size: 0.9em; }}
                .step {{ border-left: 4px solid #ddd; padding: 15px; margin-bottom: 20px; background: #fafafa; }}
                .step.success {{ border-left-color: #2ecc71; }}
                .step.failed {{ border-left-color: #e74c3c; }}
                .step.info {{ border-left-color: #3498db; }}
                .step-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .step-title {{ font-weight: bold; font-size: 1.1em; }}
                .step-time {{ color: #999; font-size: 0.8em; }}
                .step-details {{ font-family: monospace; background: #eee; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.9em; }}
                .screenshot {{ margin-top: 15px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }}
                .screenshot img {{ max-width: 100%; display: block; }}
                .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; color: white; }}
                .status-success {{ background: #2ecc71; }}
                .status-failed {{ background: #e74c3c; }}
                .status-info {{ background: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Execution Report: {self.agent_name}</h1>
                <div class="meta">
                    <p><strong>Start Time:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Duration:</strong> {duration}</p>
                    <p><strong>Total Steps:</strong> {len(self.steps)}</p>
                </div>
                
                <div class="steps">
        """
        
        for i, step in enumerate(self.steps):
            status_class = step['status']
            details_json = json.dumps(step['details'], indent=2, ensure_ascii=False) if step['details'] else ""
            
            # Embed image if present
            img_html = ""
            if step.get('screenshot'):
                img_html = f"""
                <div class="screenshot">
                    <img src="data:image/jpeg;base64,{step['screenshot']}" alt="Screenshot step {i+1}" />
                </div>
                """
            
            html_content += f"""
                    <div class="step {status_class}">
                        <div class="step-header">
                            <span class="step-title">#{i+1} {step['step']}</span>
                            <span class="status-badge status-{status_class}">{step['status']}</span>
                        </div>
                        <div class="step-time">{step['timestamp']}</div>
                        {f'<div class="step-details"><pre>{details_json}</pre></div>' if details_json else ''}
                        {img_html}
                    </div>
            """
            
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        
        async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
            await f.write(html_content)
        print(f"History exported to HTML: {output_file}")
