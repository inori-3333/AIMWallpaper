import pytest
from unittest.mock import MagicMock
from app.core.script_generator import ScriptGenerator


class TestScriptGenerator:
    def test_generate_script(self):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = '''export function update(value) {
    thisLayer.opacity = Math.sin(engine.runtime * 2) * 0.5 + 0.5;
}'''
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Make the layer pulse in opacity")
        assert "update" in result
        assert "thisLayer" in result

    def test_generate_with_context(self):
        mock_engine = MagicMock()
        mock_engine.chat.return_value = 'export function update() { thisLayer.x = input.cursorWorldPosition.x; }'
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Follow mouse cursor", context={"layer_name": "particle", "api_hints": ["input.cursorWorldPosition"]})
        assert "cursorWorldPosition" in result
        mock_engine.chat.assert_called_once()
        call_args = mock_engine.chat.call_args
        assert "cursorWorldPosition" in str(call_args)

    def test_validate_syntax_valid(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        code = 'export function update() { return 1; }'
        assert gen.validate_syntax(code) is True

    def test_validate_syntax_invalid(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        code = 'function { broken syntax ((('
        assert gen.validate_syntax(code) is False

    def test_validate_api_whitelist(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        safe_code = 'thisLayer.opacity = 1; engine.runtime; input.cursorWorldPosition;'
        assert gen.check_api_usage(safe_code) == []

    def test_validate_api_blacklist(self):
        gen = ScriptGenerator(ai_engine=MagicMock())
        unsafe_code = 'fetch("http://evil.com"); eval("code");'
        violations = gen.check_api_usage(unsafe_code)
        assert "fetch" in violations
        assert "eval" in violations

    def test_generate_with_retry_on_invalid(self):
        mock_engine = MagicMock()
        mock_engine.chat.side_effect = [
            'function { broken',
            'export function update() { thisLayer.opacity = 1; }',
        ]
        gen = ScriptGenerator(ai_engine=mock_engine)
        result = gen.generate("Set opacity to 1")
        assert "update" in result
        assert mock_engine.chat.call_count == 2
