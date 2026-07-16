import ast
from pathlib import Path
import pytest
AGENTS=['interpreter','retriever','summarizer','evaluator','critic','improver']
@pytest.mark.parametrize('name',AGENTS)
def test_agent_file_exists(name): assert (Path(__file__).parents[1]/'agents'/f'{name}.py').exists()
@pytest.mark.parametrize('name',AGENTS)
def test_agent_syntax(name): ast.parse((Path(__file__).parents[1]/'agents'/f'{name}.py').read_text(encoding='utf-8'))
