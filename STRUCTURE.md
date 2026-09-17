# Estrutura do Código - Keithley LabNano3D

Este documento detalha a organização e funcionalidades do código do projeto Keithley LabNano3D.

## 📁 Organização dos Arquivos

### Arquivos Principais

#### `main.py`
- **Função**: Ponto de entrada principal da aplicação
- **Tecnologia**: PyQt5
- **Responsabilidades**:
  - Inicialização da aplicação Qt
  - Criação da janela de conexão
  - Gerenciamento do loop principal da aplicação

#### `app.py`
- **Função**: Entrada alternativa usando tkinter (não utilizada atualmente)
- **Status**: Backup/alternativa
- **Tecnologia**: tkinter

#### `connection_window.py`
- **Função**: Interface de descoberta e conexão com instrumentos
- **Funcionalidades**:
  - Escaneamento automático de dispositivos VISA
  - Identificação automática de modelos Keithley
  - Thread separada para evitar bloqueio da UI
  - Validação de conexão antes de prosseguir
- **Classes principais**:
  - `ConnectionWindow`: Janela principal de conexão
  - `ScanThread`: Thread para busca de dispositivos
  - `WorkerSignals`: Sinais para comunicação thread-safe

#### `main_window.py`
- **Função**: Janela principal da aplicação após conexão
- **Responsabilidades**:
  - Carregamento dinâmico de widgets específicos do dispositivo
  - Gerenciamento da conexão VISA
  - Cleanup adequado ao fechar aplicação
- **Fluxo**:
  1. Recebe informações do dispositivo conectado
  2. Carrega widget apropriado (SMU 2450 ou Pico 6487)
  3. Gerencia ciclo de vida da conexão

#### `tests.py`
- **Função**: Script de teste básico para comunicação VISA
- **Uso**: Validação rápida de conectividade
- **Funcionalidades**:
  - Teste de sweep de tensão simples
  - Medição de corrente
  - Exemplo de uso básico da API VISA

### Diretório `widgets/`

Contém todos os widgets de interface específicos para cada instrumento.

#### `widgets/smu_2450/`

Widgets específicos para o Source Measure Unit 2450.

##### `main_2450.py`
- **Função**: Widget principal com abas para diferentes funções
- **Estrutura**: Implementa `QTabWidget` com três abas principais
- **Abas**:
  - Resistência: Medições de resistência vs tempo
  - I x V: Curvas características I-V
  - Fonte: Controle direto de tensão/corrente

##### `block_source_control.py`
- **Função**: Controle de fonte de tensão/corrente
- **Funcionalidades**:
  - Configuração de tensão/corrente de saída
  - Limites de proteção
  - Controle de habilitação/desabilitação da saída
  - Monitoramento em tempo real

##### `block_resistance_time.py`
- **Função**: Medições de resistência em função do tempo
- **Funcionalidades**:
  - Configuração de parâmetros de medição
  - Plotagem em tempo real
  - Controle de duração e intervalos
  - Exportação de dados

##### `block_iv_measurement.py`
- **Função**: Medições de curvas I-V
- **Funcionalidades**:
  - Configuração de sweep de tensão
  - Medição de corrente correspondente
  - Plotagem automática de curvas
  - Análise básica de características

#### `widgets/pico_6487/`

Widgets específicos para o Picoamperímetro 6487.

##### `main_6487.py`
- **Função**: Widget principal para controle do picoamperímetro
- **Características**: Interface otimizada para medições de alta precisão

##### `block_source_control.py`
- **Função**: Controle de fonte específico para 6487
- **Diferenças**: Otimizado para correntes baixas

##### `block_resistance_time.py`
- **Função**: Medições temporais específicas para picoamperímetro
- **Características**: Precisão em escala pico/nano

##### `block_iv_measurement.py`
- **Função**: Curvas I-V para picoamperímetro
- **Especialização**: Medições de alta resolução

##### `block_graph.py`
- **Função**: Componente de plotagem especializado
- **Responsabilidades**:
  - Gráficos em tempo real
  - Múltiplas escalas (linear/log)
  - Zoom e navegação
  - Exportação de gráficos

#### Arquivos Compartilhados

##### `widgets/measurement.py`
- **Função**: Utilitários comuns de medição
- **Conteúdo**:
  - Funções de conversão de unidades
  - Algoritmos de processamento de dados
  - Validação de parâmetros

##### `widgets/readings.py`
- **Função**: Gerenciamento de leituras e dados
- **Responsabilidades**:
  - Buffer de dados
  - Formatação de resultados
  - Estatísticas básicas

##### `widgets/source_control.py`
- **Função**: Controles de fonte compartilhados
- **Conteúdo**:
  - Classes base para controle de fonte
  - Validações comuns
  - Interface padronizada

## 🔧 Arquitetura do Sistema

### Padrões de Design Utilizados

#### 1. **Model-View-Controller (MVC)**
- **Model**: Classes de comunicação VISA
- **View**: Widgets PyQt5
- **Controller**: Lógica de controle em cada widget

#### 2. **Factory Pattern**
- `main_window.py` seleciona dinamicamente o widget apropriado baseado no modelo do instrumento

#### 3. **Observer Pattern**
- Sinais e slots do PyQt5 para comunicação entre componentes
- Threads separadas para operações não-bloqueantes

### Fluxo de Dados

```
Usuário → Interface PyQt5 → Comandos VISA → Instrumento Keithley
                                ↓
Dados de Medição ← Processamento ← Resposta VISA ← Instrumento
                                ↓
Gráficos/Tabelas ← Formatação ← Dados Processados
```

### Gerenciamento de Threads

1. **Thread Principal (GUI)**: Interface do usuário
2. **Thread de Scan**: Descoberta de dispositivos
3. **Threads de Medição**: Operações de longa duração (quando implementadas)

### Comunicação VISA

- **Protocolo**: SCPI (Standard Commands for Programmable Instruments)
- **Transporte**: USB, Ethernet (via driver VISA)
- **Timeout**: Configurável por operação
- **Terminação**: Adaptável por instrumento

## 🔍 Funcionalidades Específicas

### SMU 2450
- **Fonte de Tensão**: 0-200V
- **Fonte de Corrente**: 0-1A
- **Medição**: 4-wire, 2-wire
- **Resolução**: 6.5 dígitos

### Picoamperímetro 6487
- **Corrente**: 2fA a 20mA
- **Tensão**: ±500V
- **Resolução**: Ultra-alta para nano/picoampères
- **Filtragem**: Avançada para redução de ruído

## 🧪 Extensibilidade

### Adicionando Novos Instrumentos

1. Criar diretório em `widgets/novo_instrumento/`
2. Implementar `main_novo_instrumento.py`
3. Adicionar detecção em `connection_window.py`
4. Atualizar `main_window.py` para carregar novo widget

### Adicionando Novas Funcionalidades

1. Criar novo `block_*.py` no diretório do instrumento
2. Adicionar aba no widget principal
3. Implementar interface de medição específica

### Padrões de Código

- **Nomenclatura**: snake_case para funções, PascalCase para classes
- **Documentação**: Docstrings em português
- **Tratamento de Erros**: Try-catch com logging adequado
- **Threading**: Uso de signals para comunicação thread-safe

## 📊 Dependências Técnicas

### Principais
- **PyQt5**: Interface gráfica
- **PyVISA**: Comunicação com instrumentos
- **NumPy**: Processamento numérico
- **Matplotlib**: Plotagem (quando necessário)

### Opcionais
- **pyvisa-py**: Backend VISA puro Python (alternativa ao NI-VISA)

---

*Esta estrutura garante modularidade, manutenibilidade e fácil extensão para novos instrumentos e funcionalidades.*