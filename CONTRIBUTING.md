# Guia de Contribuição - Keithley LabNano3D

Obrigado pelo interesse em contribuir com o projeto! Este guia ajudará você a começar.

## 🚀 Começando

### Configuração do Ambiente

1. **Fork** o repositório
2. **Clone** seu fork:
   ```bash
   git clone https://github.com/seu-usuario/keithley-labnano3d.git
   cd keithley-labnano3d
   ```

3. **Configure** o ambiente:
   ```bash
   python setup.py
   ```

4. **Teste** a aplicação:
   ```bash
   python run.py
   ```

## 🔧 Desenvolvimento

### Estrutura de Branches

- `main`: Branch principal (stable)
- `develop`: Branch de desenvolvimento
- `feature/nome-da-feature`: Novas funcionalidades
- `bugfix/nome-do-bug`: Correções de bugs
- `docs/nome-da-doc`: Melhorias de documentação

### Workflow de Contribuição

1. **Crie uma branch** para sua contribuição:
   ```bash
   git checkout -b feature/minha-contribuicao
   ```

2. **Faça suas alterações** seguindo as boas práticas
3. **Teste** suas mudanças localmente
4. **Commit** com mensagens descritivas:
   ```bash
   git commit -m "feat: adiciona suporte ao modelo X"
   ```

5. **Push** para seu fork:
   ```bash
   git push origin feature/minha-contribuicao
   ```

6. **Abra um Pull Request** explicando suas mudanças

### Padrões de Código

#### Python
- **PEP 8**: Siga as convenções de estilo Python
- **Docstrings**: Documente funções e classes
- **Type hints**: Use quando possível
- **Nomes**: Use português para variáveis e comentários quando apropriado

#### Exemplo:
```python
def medir_corrente(tensao: float, timeout: int = 1000) -> float:
    """
    Mede a corrente para uma tensão específica.
    
    Args:
        tensao: Tensão a ser aplicada (V)
        timeout: Timeout da medição (ms)
        
    Returns:
        Corrente medida (A)
    """
    # Implementação...
    pass
```

#### Commits
Use o padrão [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Mudanças na documentação
- `style:` - Formatação de código
- `refactor:` - Refatoração sem mudança funcional
- `test:` - Adição ou correção de testes
- `chore:` - Manutenção geral

## 🧪 Testes

### Executando Testes
```bash
python -m pytest tests/
```

### Adicionando Testes
- Crie testes para novas funcionalidades
- Use mocks para instrumentos VISA
- Mantenha cobertura > 80%

### Exemplo de Teste:
```python
import pytest
from unittest.mock import Mock
from widgets.smu_2450.block_source_control import SourceControlBlock

def test_configurar_tensao():
    # Mock do instrumento
    mock_instrument = Mock()
    
    # Criar widget
    widget = SourceControlBlock(mock_instrument)
    
    # Testar configuração
    widget.configurar_tensao(5.0)
    
    # Verificar chamadas
    mock_instrument.write.assert_called_with("SOUR:VOLT 5.0")
```

## 📝 Documentação

### Atualizando Documentação
- Mantenha README.md atualizado
- Atualize STRUCTURE.md para novas funcionalidades
- Documente APIs e interfaces públicas

### Adicionando Exemplos
- Inclua exemplos de uso para novas funcionalidades
- Use casos reais quando possível
- Documente parâmetros e comportamentos especiais

## 🐛 Reportando Bugs

### Template de Bug Report
```markdown
**Descrição do Bug**
Uma descrição clara do que está acontecendo.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '....'
3. Veja erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
 - OS: [ex: Windows 10]
 - Python: [ex: 3.9.1]
 - Versão: [ex: v1.0.0]
 - Instrumento: [ex: SMU 2450]
```

## ✨ Sugestões de Funcionalidades

### Áreas que Precisam de Ajuda
- 🧪 **Testes**: Testes com instrumentos reais
- 🎨 **UI/UX**: Melhorias na interface
- 📖 **Documentação**: Guias e tutoriais
- 🔧 **Instrumentos**: Suporte a novos modelos
- 🌐 **Internacionalização**: Tradução para outros idiomas

### Template de Feature Request
```markdown
**Funcionalidade Desejada**
Uma descrição clara da funcionalidade.

**Problema que Resolve**
Qual problema esta funcionalidade resolve?

**Solução Proposta**
Como você imagina que isso funcione?

**Alternativas Consideradas**
Outras soluções que você considerou?

**Contexto Adicional**
Qualquer outro contexto ou screenshots.
```

## 🎯 Prioridades

### Alta Prioridade
- ✅ Correções de bugs críticos
- ✅ Melhorias de estabilidade
- ✅ Documentação essencial

### Média Prioridade  
- 🔄 Novas funcionalidades
- 🔄 Otimizações de performance
- 🔄 Melhorias de UI

### Baixa Prioridade
- 💡 Funcionalidades experimentais
- 💡 Refatorações grandes
- 💡 Features avançadas

## 📞 Contato

- **Issues**: Para bugs e sugestões
- **Discussions**: Para perguntas gerais
- **Pull Requests**: Para contribuições de código

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença do projeto.

---

*Obrigado por contribuir para o Keithley LabNano3D! 🚀*