import re


SCENESCRIPT_SYSTEM_PROMPT = """You are a Wallpaper Engine SceneScript code generator.
SceneScript is an ECMAScript 2018 subset for WE wallpapers.

Core APIs available:
- thisScene: access scene properties
- thisLayer: access current layer (opacity, x, y, scale, angles, color)
- input: user input (cursorWorldPosition, cursorScreenPosition, audioLevel)
- engine: runtime info (engine.runtime = elapsed seconds, engine.frametime = delta)

Rules:
- Export functions: export function init(), export function update(value)
- No DOM, no fetch, no eval, no require/import from external modules
- Keep code minimal and focused on the requested effect
- Use only known SceneScript APIs

Return ONLY the JavaScript code, no markdown fences or explanation."""

BLOCKED_APIS = ["fetch", "eval", "XMLHttpRequest", "require", "import(", "Function(", "setTimeout", "setInterval"]


class ScriptGenerator:
    def __init__(self, ai_engine, max_retries: int = 3):
        self.ai_engine = ai_engine
        self.max_retries = max_retries

    def generate(self, description: str, context: dict | None = None) -> str:
        ctx = context or {}
        user_msg = f"Generate SceneScript for: {description}"
        if ctx.get("layer_name"):
            user_msg += f"\nTarget layer: {ctx['layer_name']}"
        if ctx.get("api_hints"):
            user_msg += f"\nRelevant APIs: {', '.join(ctx['api_hints'])}"

        for attempt in range(self.max_retries):
            code = self.ai_engine.chat(
                system_prompt=SCENESCRIPT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0.3,
            )
            code = self._strip_fences(code)

            if self.validate_syntax(code):
                violations = self.check_api_usage(code)
                if not violations:
                    return code
                user_msg = f"Previous code used blocked APIs: {violations}. Fix and regenerate for: {description}"
            else:
                user_msg = f"Previous code had syntax errors. Fix and regenerate for: {description}"

        return code

    def validate_syntax(self, code: str) -> bool:
        cleaned = re.sub(r'\bexport\s+', '', code)
        try:
            brace_count = 0
            for ch in cleaned:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                if brace_count < 0:
                    return False
            return brace_count == 0 and ('function' in cleaned or '=>' in cleaned or '=' in cleaned)
        except Exception:
            return False

    def check_api_usage(self, code: str) -> list[str]:
        violations = []
        for api in BLOCKED_APIS:
            if api in code:
                violations.append(api.rstrip("("))
        return violations

    def _strip_fences(self, code: str) -> str:
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()
