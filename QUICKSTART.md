# Quick Reference Guide - Keithley LabNano3D v2.1

Guia rápido para desenvolvedores começarem a trabalhar no projeto.

## 🎉 Novidades v2.1

- ✅ Interface completamente redesenhada
- ✅ Gerenciamento de instrumentos integrado
- ✅ Editor de scripts com execução
- ✅ Exportação CSV com metadados completos
- ✅ Sistema de troca de usuário
- ✅ Organização automática de diretórios

## 🚀 Início Rápido

### Instalação
```bash
git clone https://github.com/LucJBQ/keithley-labnano3d.git
cd keithley-labnano3d
pip install -r requirements.txt
python main.py
```

### Estrutura Simplificada

```
keithley-labnano3d/
│
├── main.py                    ⭐ PONTO DE ENTRADA PRINCIPAL
├── startup_window.py          → Tela de login/registro
├── main_window_v2.py          → Janela principal (v2)
├── connection_window_v2.py    → Conexão de instrumentos (v2)
├── setup.py                   → Configuração inicial
│
├── core/                      📦 MÓDULOS CORE
│   ├── user_manager.py        → Gerenciamento de usuários
│   ├── data_export.py         → Exportação/importação CSV
│   ├── logger.py              → Sistema de logging
│   ├── config.py              → Configurações
│   ├── database.py            → Banco SQLite
│   ├── script_manager.py      → Scripts customizados
│   └── debug_mode.py          → Simuladores
│
├── widgets/                   🎛️ CONTROLES DE INSTRUMENTOS
│   ├── smu_2450/             → SMU 2450 (blocos de medição)
│   ├── pico_6487/            → Picoammeter 6487 (blocos de medição)
│   └── script_editor_widget.py → Editor de scripts (v2.1)
│
├── scripts/builtin/          📝 SCRIPTS DE MEDIÇÃO
│   ├── iv_curve.py           → Curva I-V
│   ├── resistance_time.py    → R vs Tempo
│   └── automated_sequence.py → Sequência automática
│
└── tests/                    🧪 TESTES
    ├── test_core_functionality.py
    ├── test_database.py
    ├── test_script_manager.py
    └── test_integration.py
```

## 📖 Fluxo de Trabalho da Aplicação v2.1

### 1. Inicialização (`main.py`)
```python
python main.py
```
- Verifica ambiente (Python 3.8+, GUI disponível)
- Se GUI disponível → abre `startup_window.py`
- Se não → executa testes em modo console

### 2. Login/Registro (`startup_window.py`)
- Login de usuário existente
- Registro de novo usuário (cria diretórios automaticamente)
- Acesso ao modo debug (senha: `debug123`)

### 3. Seleção de Modo (`main_window_v2.py`)
- **1 Instrumento**: Modo padrão recomendado
- **2 Instrumentos**: Em construção
- **Carregar Dados**: Importar medições salvas

### 4. Janela Principal v2.1
**Painel Esquerdo (400px)**:
- Gerenciamento de instrumentos (abas Real/Simulado)
- Seletor de instrumento ativo
- Status de instrumentos conectados

**Painel Direito (1000px)**:
- Widget de status da fonte (sempre visível)
- Seletor de tipo de medição (Resistência/I-V)
- Área de medição (parâmetros, leituras, gráfico)
- Abas avançadas:
  - 🔧 Comandos Manuais (console SCPI)
  - 📝 Editor de Scripts (editor + terminal)

### 5. Fluxo de Medição
1. Conecte instrumento no painel esquerdo
2. Selecione instrumento ativo no seletor
3. Verifique status da fonte
4. Escolha tipo de medição (Resistência ou I-V)
5. Configure parâmetros
6. Execute medição
7. Exporte dados com metadados completos

### 6. Fluxo de Scripts
1. Acesse aba "📝 Editor de Scripts"
2. Escreva ou carregue script SCPI
3. Execute e veja saída no terminal
4. Exporte resultados
5. Scripts salvos em `users/{username}/scripts/{instrument}/`

## 🔧 Adicionando Funcionalidades

### Novo Script de Medição
1. Crie arquivo em `scripts/builtin/` ou user scripts
2. Implemente classe com métodos:
   - `get_parameters()`: Retorna lista de parâmetros
   - `execute()`: Lógica de medição
   - `validate()`: Validação de parâmetros
3. Registre no `script_manager.py`

### Novo Instrumento
1. Crie widget em `widgets/{instrument_name}/`
2. Implemente controles específicos
3. Adicione simulador em `core/debug_mode.py`
4. Registre em `connection_window_v2.py`

### Nova Funcionalidade Core
1. Adicione módulo em `core/`
2. Escreva testes em `tests/`
3. Documente em `ARCHITECTURE_V2.md`
4. Atualize `IMPLEMENTATION_STATUS.md`

## 🧪 Testando

### Rodar Todos os Testes
```bash
python -m pytest tests/
```

### Testes Individuais
```bash
python tests/test_core_functionality.py
python tests/test_database.py
python tests/test_script_manager.py
python tests/test_integration.py
```

### Modo Debug (Desenvolvimento sem Hardware)
```bash
python main.py
# Na tela de startup: "Modo Debug" → senha: debug123
```

## 📊 Banco de Dados

### Localização
```
database/labnano3d.db
```

### Tabelas Principais
- `users`: Perfis de usuários
- `measurements`: Histórico de medições
- `instruments`: Configurações de instrumentos
- `exports`: Registros de exportação

### Acessar Banco
```python
from core.database import get_database_manager
db = get_database_manager()
measurements = db.get_measurements_for_user(user_id)
```

## 📁 Organização de Dados do Usuário v2.1

```
users/{username}/
├── measurements/
│   ├── resistance/   → Medições de resistência
│   ├── current/      → Medições de corrente
│   └── iv/          → Curvas I-V
├── scripts/
│   ├── smu_2450/    → Scripts para SMU 2450
│   └── pico_6487/   → Scripts para Picoamperímetro
├── exports/         → Dados exportados (CSV com metadados)
├── configs/         → Configurações pessoais
└── presets/         → Presets de medição

logs/{username}/     → Logs específicos do usuário
```

### Exportação de Dados v2.1
Os dados são exportados em CSV com metadados completos:
```csv
# Keithley LabNano3D - Medição de Resistência
# Usuário: João Silva
# Equipamento: SMU 2450 (Serial: 12345)
# Endereço: GPIB0::1::INSTR
# Data: 2025-10-14 10:30:00
#
# Parâmetros de Medição:
# Tensão Aplicada: 1.0 V
# Compliance: 10 mA
# ---
Tempo (s), Resistência (Ohm), Corrente (A)
...
```

## 🔍 Debugging

### Logs
```bash
# Logs do usuário
cat logs/{username}/app_YYYY-MM-DD.log

# Logs de instrumentos
cat logs/{username}/instrument_YYYY-MM-DD.log

# Logs de medições
cat logs/{username}/measurements_YYYY-MM-DD.log
```

### Modo Debug
- Instrumentos simulados de alta fidelidade
- Dados realistas para testes
- Sem necessidade de hardware físico
- Senha: `debug123`

## 🎨 Modificando a UI v2.1

### Arquivos Principais
- `startup_window.py`: Tela inicial de login
- `main_window_v2.py`: Janela principal redesenhada
  - Mode Selection Widget
  - Instrument Management (integrado)
  - Source Status Widget
  - Measurement widgets (QStackedWidget)
- `connection_window_v2.py`: Componente de conexão integrado
- `widgets/script_editor_widget.py`: Editor de scripts
- Widgets específicos em `widgets/smu_2450/` e `widgets/pico_6487/`

### Padrão PyQt5
```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        # Adicionar componentes
        self.setLayout(layout)
```

## 📚 Documentação

- `README.md`: Overview geral e guia do usuário (v2.1)
- `REFACTORING_PLAN.md`: Plano detalhado v2.1 (100% completo)
- `ARCHITECTURE_V2.md`: Arquitetura detalhada
- `IMPLEMENTATION_STATUS.md`: Status de implementação (v2.1)
- `ROADMAP.md`: Plano de desenvolvimento (~85% completo)
- `QUICKSTART.md`: Este guia
- `STRUCTURE.md`: Estrutura de arquivos
- `RESTRUCTURING_SUMMARY.md`: Resumo da reestruturação
- `CONTRIBUTING.md`: Guia de contribuição

## ⚡ Dicas de Performance

### Threading
```python
from PyQt5.QtCore import QThread

class MeasurementThread(QThread):
    def run(self):
        # Código de medição pesada
        pass
```

### Logging Eficiente
```python
from core.logger import get_logger

logger = get_logger(__name__)
logger.info("Mensagem")
```

### Banco de Dados
```python
# Use context manager
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Operações
```

## 🐛 Problemas Comuns

### Erro: "No module named PyQt5"
```bash
pip install PyQt5
```

### Erro: "No module named pyvisa"
```bash
pip install pyvisa
```

### GUI não disponível
```bash
# Rode em modo console
python tests/test_integration.py
```

### Instrumento não encontrado
1. Verifique driver VISA instalado
2. Confirme instrumento conectado
3. Use modo debug para testar sem hardware

## 🔄 Workflow de Desenvolvimento

### 1. Nova Feature
```bash
git checkout -b feature/nova-funcionalidade
# Desenvolva
# Teste
git commit -m "Add: nova funcionalidade"
git push origin feature/nova-funcionalidade
# Abra Pull Request
```

### 2. Bug Fix
```bash
git checkout -b fix/correcao-bug
# Corrija
# Teste
git commit -m "Fix: descrição do bug"
git push origin fix/correcao-bug
# Abra Pull Request
```

### 3. Teste Antes de Commit
```bash
python -m pytest tests/
python main.py  # Teste manual
```

## 📞 Onde Obter Ajuda

1. **Documentação**: Leia `ARCHITECTURE_V2.md` e `IMPLEMENTATION_STATUS.md`
2. **Issues**: Abra issue no GitHub
3. **Código**: Veja exemplos em `tests/` e `scripts/builtin/`
4. **Logs**: Consulte logs em `logs/{username}/`

## 🎯 Checklist para Contribuidores

- [ ] Li `CONTRIBUTING.md`
- [ ] Entendi a arquitetura em `ARCHITECTURE_V2.md`
- [ ] Ambiente configurado (`pip install -r requirements.txt`)
- [ ] Testes passando (`python -m pytest tests/`)
- [ ] Código documentado (docstrings)
- [ ] Logs apropriados adicionados
- [ ] README atualizado se necessário
- [ ] Testes para nova funcionalidade escritos

## 🚀 Próximos Passos Recomendados

1. **Para novos desenvolvedores**:
   - Execute `python main.py` em modo debug
   - Explore os scripts built-in
   - Leia `ARCHITECTURE_V2.md`

2. **Para contribuir**:
   - Veja `IMPLEMENTATION_STATUS.md` para features pendentes
   - Consulte `ROADMAP.md` para prioridades
   - Leia `CONTRIBUTING.md` para diretrizes

3. **Para testar**:
   - Use modo debug (sem hardware)
   - Execute suite de testes
   - Crie scripts customizados

---

*Última atualização: Outubro 2025 - v2.1*
*v2.1 UX Redesign Complete - All 4 core phases implemented*
