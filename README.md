# Keithley LabNano3D v2.1

Uma aplicação moderna de interface gráfica em Python para controle de instrumentos Keithley de laboratório, com sistema de gerenciamento de usuários, medições automatizadas, editor de scripts e análise de dados.

## 🎉 Novidades na v2.2

### Modo Instrumento + ESP32
- **Medições Combinadas**: Use instrumentos VISA em conjunto com ESP32/ADS1115
- **Leituras Simultâneas**: Capture dados do instrumento VISA e sensores externos simultaneamente
- **Gráfico com Dois Eixos Y**: Visualize ambas as leituras em tempo real
- **Calibração de Sensores**: Sistema completo de calibração para ADS1115
- **Exportação Integrada**: Dados exportados em três colunas (tempo, VISA, ESP32)

### Sistema ADS1115
- **16-bit ADC**: Leituras de alta precisão
- **4 Canais**: Suporte para até 4 sensores simultâneos (single-ended ou differential)
- **Calibração Flexível**: Suporte para leituras brutas ou escala percentual
- **Auto-inversão**: Detecta automaticamente sensores com leitura invertida
- **Múltiplos Tipos de Sensores**: Umidade, temperatura, pressão, etc.

### Interface Redesenhada
- **Seleção de Modo**: Escolha entre 1 instrumento, 2 instrumentos ou carregar dados
- **Gerenciamento Integrado**: Conexão de instrumentos sem janelas modais
- **Seletor de Instrumento Ativo**: Alterne facilmente entre instrumentos conectados
- **Layout Otimizado**: Interface single-window profissional

### Widgets Reorganizados
- **Visualização Direta**: Medições exibidas diretamente (sem abas aninhadas)
- **Status da Fonte**: Widget sempre visível mostrando estado ON/OFF
- **Seletor de Medição**: Troca rápida entre Resistência e I-V

### Gerenciamento de Dados Aprimorado
- **Exportação CSV Profissional**: Metadados completos (usuário, instrumento, parâmetros)
- **Importação com Filtros**: Carregue apenas arquivos compatíveis
- **Estrutura de Diretórios Organizada**: Pastas por tipo de medição e instrumento
- **Troca de Usuário**: Botão para logout e retorno ao login

### Editor de Scripts
- **Editor Completo**: Crie, edite, salve e execute scripts SCPI
- **Terminal de Saída**: Feedback em tempo real da execução
- **Organização por Instrumento**: Scripts salvos por tipo de equipamento
- **Exportação de Resultados**: Salve a saída do terminal

## 📋 Descrição

O Keithley LabNano3D v2.0 é uma plataforma completa de controle e automação para instrumentos de medição Keithley, oferecendo:

- **Gerenciamento de Usuários**: Sistema completo de registro e login de usuários
- **Modo Debug**: Ambiente de desenvolvimento com instrumentos simulados
- **Scripts de Medição**: Biblioteca de scripts built-in e sistema de scripts customizados
- **Banco de Dados**: Armazenamento local de medições, configurações e histórico
- **Exportação Avançada**: CSV com metadados completos, compatível com Origin
- **Interface Moderna**: UI redesenhada com suporte multi-instrumento

## 🚀 Funcionalidades

### Instrumentos Suportados
- ✅ Keithley SMU 2450
- ✅ Keithley Picoammeter 6487
- ✅ ESP32 + ADS1115 (para sensores externos)

### Sistema de Medição
- **Curva I-V**: Sweeps de tensão configuráveis
- **Resistência vs Tempo**: Monitoramento temporal com análise de estabilidade
- **Sequências Automatizadas**: Combinação de medições com tempos de descanso configuráveis
- **Scripts Customizados**: Crie, edite e execute scripts personalizados
- **Medições Combinadas**: Instrumento VISA + sensores via ESP32/ADS1115

### Gerenciamento de Dados
- **Banco SQLite**: Histórico completo de medições
- **Exportação CSV**: Metadados completos e compatibilidade com Origin
- **Organização Automática**: Diretórios específicos por usuário
- **Sistema de Logs**: Logging abrangente de todas as operações

### Modo Debug
- Ambiente de desenvolvimento completo
- Instrumentos simulados de alta fidelidade
- Teste sem hardware físico
- Senha de acesso: `debug123`

## 🛠️ Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Driver VISA instalado (NI-VISA ou Keithley IO Layer)

### Instalação das Dependências

1. Clone o repositório:
```bash
git clone https://github.com/LucJBQ/keithley-labnano3d.git
cd keithley-labnano3d
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 📖 Como Usar

### Iniciando a Aplicação

Execute o arquivo principal:
```bash
python main.py
```

### Primeiro Acesso

1. Na tela de inicialização, clique em "Novo Usuário"
2. Preencha seu nome e sobrenome
3. Faça login com o usuário criado
4. Selecione o modo de operação (1 Instrumento recomendado)

### Conectando Instrumentos

1. No painel esquerdo, acesse a aba "Instrumentos Reais" ou "Simulados"
2. Clique em "Identificar Instrumentos" para buscar dispositivos VISA
3. Selecione o instrumento na lista
4. Clique em "Conectar"
5. O instrumento aparecerá no seletor de instrumento ativo

### Realizando Medições

1. Selecione o instrumento ativo no seletor superior
2. Verifique o status da fonte (ON/OFF)
3. Escolha o tipo de medição no seletor (Resistência ou I-V)
4. Configure os parâmetros na área de parâmetros
5. Inicie a medição e acompanhe em tempo real
6. Exporte os dados com metadados completos

### Modo Instrumento + ESP32

Este modo permite medições simultâneas de um instrumento VISA e sensores conectados via ESP32/ADS1115.

#### Preparação do Hardware

1. **Prepare o ESP32**:
   - Siga as instruções em `firmware/README.md`
   - Carregue o firmware `esp32_ads1115.ino`
   - Conecte o ADS1115 ao ESP32 (I2C)
   - Conecte seus sensores ao ADS1115

2. **Conecte ao PC**:
   - Conecte o instrumento VISA via USB/Ethernet
   - Conecte o ESP32 via USB

#### Usando o Modo Combinado

1. **Selecione o Modo**:
   - Após login, selecione "Instrumento + ESP32"
   
2. **Conecte o Instrumento VISA**:
   - Aba "Instrumentos Reais" ou "Simulados"
   - Busque e conecte o instrumento normalmente

3. **Conecte o ESP32**:
   - Aba "ESP32"
   - Clique "Buscar Dispositivos"
   - Selecione a porta do ESP32
   - Clique "Conectar Selecionado"

4. **Calibre o ADS1115**:
   - Clique "⚙️ Calibrar ADS1115"
   - Selecione o canal (A0-A3)
   - Escolha o tipo de leitura:
     - **Leitura Bruta**: Valor ADC direto (0-32767)
     - **Percentual**: Escala 0-100% (ideal para sensores)
   - Configure min/max:
     - Coloque sensor na condição mínima
     - Clique "Atualizar Leitura" → "Definir como Mín"
     - Coloque sensor na condição máxima
     - Clique "Atualizar Leitura" → "Definir como Máx"
   - Clique "Aplicar Calibração"

5. **Realize Medições Combinadas**:
   - Configure parâmetros do instrumento VISA
   - Defina intervalo e duração
   - Clique "Iniciar Medição"
   - Observe ambos os gráficos em tempo real:
     - Eixo Y esquerdo (azul): Instrumento VISA
     - Eixo Y direito (laranja): ESP32/ADS1115
   - Clique "Parar Medição" quando concluir

6. **Exporte os Dados**:
   - Clique "Exportar Dados"
   - Arquivo CSV com 3 colunas:
     - Tempo (s)
     - Corrente VISA (A)
     - Leitura ESP32 (calibrada)

#### Exemplo: Monitoramento de Umidade Durante Medição Elétrica

```
Aplicação: Medir corrente em dispositivo enquanto monitora umidade ambiente

Hardware:
- SMU 2450 conectado ao dispositivo
- Sensor de umidade capacitivo no canal A0 do ADS1115

Calibração:
1. Sensor seco (ar): 28000 → Definir como Máx (0%)
2. Sensor úmido (água): 14000 → Definir como Mín (100%)
3. Sistema detecta inversão automaticamente

Resultado:
- Gráfico mostra corrente do dispositivo vs umidade em tempo real
- Exportação inclui timestamp, corrente e % umidade
```

### Editor de Scripts

1. Acesse a aba "📝 Editor de Scripts" abaixo das medições
2. Escreva seu script SCPI ou carregue um existente
3. Clique em "Executar Script"
4. Acompanhe a saída no terminal
5. Exporte os resultados se necessário

Scripts são salvos em: `users/{seu_usuario}/scripts/{tipo_instrumento}/`

### Console de Comandos Manuais

1. Acesse a aba "🔧 Comandos Manuais"
2. Selecione o instrumento alvo
3. Digite comandos SCPI individuais
4. Veja as respostas em tempo real

### Modo Debug (Desenvolvimento)

1. Na tela de inicialização, clique em "Modo Debug"
2. Digite a senha: `debug123`
3. Use os instrumentos simulados para testes

### Conectando Instrumentos

1. Após o login, selecione "1 Instrumento" na tela de seleção de modo
2. No painel esquerdo, use a aba "Instrumentos Reais" para dispositivos físicos ou "Simulados" para testes
3. Clique em "Identificar Instrumentos"
4. Selecione o instrumento e clique em "Conectar"

### Usando o Editor de Scripts

O editor permite automação completa das medições:

```scpi
# Exemplo de script para SMU 2450
*RST
:SOUR:FUNC VOLT
:SOUR:VOLT 1.0
:SOUR:VOLT:LIM 10
:OUTP ON
:READ?
```

**Funcionalidades**:
- Syntax highlighting para comandos SCPI
- Execução linha por linha
- Terminal mostrando resultados
- Exportação de saída
- Salvamento organizado por instrumento

### Estrutura de Dados do Usuário

```
users/{seu_usuario}/
├── measurements/
│   ├── resistance/    # Medições de resistência
│   ├── current/       # Medições de corrente
│   └── iv/           # Curvas I-V
├── scripts/
│   ├── smu_2450/     # Scripts para SMU
│   └── pico_6487/    # Scripts para Picoamperímetro
├── exports/          # Dados exportados
├── configs/          # Configurações salvas
└── presets/          # Presets de medição
```

### Exportação de Dados

Os dados são exportados em formato CSV com metadados completos:

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

Compatível com Origin e outros softwares de análise.

## 🏗️ Arquitetura v2.1

### Fluxo da Aplicação

```
main.py 
  ↓
startup_window.py (Login/Registro)
  ↓
main_window_v2.py (Janela Principal)
  ├─ [Painel Esquerdo]
  │   ├─ Mode Selection (1/2 instrumentos, carregar dados)
  │   ├─ Instrument Management (Real/Simulado)
  │   └─ Active Instrument Selector
  │
  └─ [Painel Direito]
      ├─ Source Status Widget (sempre visível)
      ├─ Measurement Type Selector
      ├─ Measurement Widgets (Resistance/I-V)
      └─ Advanced Tabs
          ├─ 🔧 Comandos Manuais
          └─ 📝 Editor de Scripts
```

### Módulos Core

- `core/user_manager.py` - Gerenciamento de usuários e diretórios
- `core/data_export.py` - Exportação/importação CSV com metadados
- `core/logger.py` - Sistema de logging com rotação
- `core/config.py` - Gerenciamento de configurações
- `core/debug_mode.py` - Instrumentos simulados
- `core/database.py` - Banco de dados SQLite
- `core/script_manager.py` - Gerenciamento de scripts

### Widgets v2.1

- `main_window_v2.py` - Janela principal redesenhada
- `connection_window_v2.py` - Gerenciamento de instrumentos integrado
- `widgets/script_editor_widget.py` - Editor de scripts completo
- `widgets/smu_2450/` - Widgets de medição SMU 2450
- `widgets/pico_6487/` - Widgets de medição Picoamperímetro 6487

## 📚 Documentação Completa

- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)**: Plano detalhado v2.1 (100% completo)
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)**: Status de implementação
- **[QUICKSTART.md](QUICKSTART.md)**: Guia rápido para desenvolvedores
- **[ROADMAP.md](ROADMAP.md)**: Roadmap de desenvolvimento
- **[RESTRUCTURING_SUMMARY.md](RESTRUCTURING_SUMMARY.md)**: Resumo da reestruturação

## 🧪 Testes

Execute os testes automatizados:

```bash
# Testes core
python tests/test_core_functionality.py

# Testes de database
python tests/test_database.py

# Testes de integração
python tests/test_integration.py

# Testes de script manager
python tests/test_script_manager.py
```

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para guidelines de contribuição.

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🆘 Suporte

Para problemas, sugestões ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação completa
- Revise os logs em `logs/{seu_usuario}/`

## 🔄 Changelog

### v2.1 (2025-10-14)
- ✨ Interface completamente redesenhada
- ✨ Seleção de modo de operação
- ✨ Gerenciamento de instrumentos integrado
- ✨ Editor de scripts com execução
- ✨ Exportação CSV com metadados completos
- ✨ Sistema de troca de usuário
- ✨ Organização automática de diretórios
- 🐛 Correção de crash no Windows (QApplication)

### v2.0 (Initial Release)
- Sistema de usuários
- Instrumentos simulados
- Database SQLite
- Scripts built-in
- Logging robusto

## 🏗️ Estrutura do Projeto

```
keithley-labnano3d/
├── main.py                    # Ponto de entrada principal (v2.0)
├── startup_window.py          # Interface de login/registro
├── main_window_v2.py          # Janela principal moderna
├── connection_window_v2.py    # Janela de conexão de instrumentos
├── setup.py                   # Script de configuração
│
├── core/                      # Núcleo do sistema
│   ├── user_manager.py        # Gerenciamento de usuários
│   ├── logger.py              # Sistema de logging
│   ├── config.py              # Gerenciamento de configurações
│   ├── database.py            # Banco de dados SQLite
│   ├── script_manager.py      # Gerenciador de scripts
│   └── debug_mode.py          # Instrumentos simulados
│
├── widgets/                   # Widgets de controle
│   ├── smu_2450/             # Controles para SMU 2450
│   └── pico_6487/            # Controles para Picoammeter 6487
│
├── scripts/                   # Scripts de medição
│   └── builtin/              # Scripts built-in
│       ├── iv_curve.py
│       ├── resistance_time.py
│       └── automated_sequence.py
│
├── tests/                     # Suíte de testes
│   ├── test_core_functionality.py
│   ├── test_database.py
│   ├── test_script_manager.py
│   └── test_integration.py
│
├── config/                    # Configurações
│   └── app_config.json
│
├── database/                  # Banco de dados (criado automaticamente)
│   └── labnano3d.db
│
├── users/                     # Dados dos usuários (criado automaticamente)
│   └── {username}/
│       ├── measurements/
│       ├── scripts/
│       ├── exports/
│       └── configs/
│
├── logs/                      # Arquivos de log (criado automaticamente)
│   └── {username}/
│
├── README.md                  # Este arquivo
├── IMPLEMENTATION_STATUS.md   # Status da implementação
├── ARCHITECTURE_V2.md         # Documentação da arquitetura
├── STRUCTURE.md               # Estrutura detalhada
├── ROADMAP.md                 # Plano de desenvolvimento
└── CONTRIBUTING.md            # Guia de contribuição
```

## 🧪 Testes

Execute a suíte completa de testes:

```bash
# Todos os testes
python -m pytest tests/

# Testes específicos
python tests/test_core_functionality.py
python tests/test_database.py
python tests/test_script_manager.py
python tests/test_integration.py
```

**Modo Console** (sem GUI):
```bash
python tests/test_integration.py
```

## 📊 Status de Implementação

Veja [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) para um overview completo do que está implementado versus o que está planejado.

**Resumo**: ~60% das funcionalidades planejadas estão implementadas
- Core Architecture: 95% ✅
- User Interface: 70% 🔄
- Measurement System: 85% ✅
- Data Management: 75% ✅
- Testing: 80% ✅
- Documentation: 90% ✅

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no GitHub
- Consulte a [documentação de arquitetura](ARCHITECTURE_V2.md)
- Veja o [status de implementação](IMPLEMENTATION_STATUS.md)

## 🔗 Links Úteis

- [Documentação PyVISA](https://pyvisa.readthedocs.io/)
- [Manuais Keithley](https://www.tek.com/en/support/software)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython-5/)

## 📈 Roadmap

Veja [ROADMAP.md](ROADMAP.md) para o plano completo de desenvolvimento.

### Próximas Prioridades
1. Integração completa dos widgets v1 no main_window_v2
2. Melhorias na visualização de dados
3. Atalhos de teclado e tooltips
4. Pipeline CI/CD

---

*Desenvolvido para aplicações de nanotecnologia e caracterização de dispositivos eletrônicos.*
