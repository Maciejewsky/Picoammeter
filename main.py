#!/usr/bin/env python3
"""
Main entry point for Keithley LabNano3D v2.0
Launches the modern startup interface with user management and comprehensive measurement system
"""

import sys
import os
from pathlib import Path

def main():
    """Main application entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 ou superior é necessário")
            print(f"   Versão atual: {sys.version}")
            return 1
        
        # Check if running in GUI environment
        gui_available = True
        try:
            # Check if DISPLAY is available (Linux/Unix)
            if os.name == 'posix' and 'DISPLAY' not in os.environ:
                raise Exception("No DISPLAY environment variable")
            
            # Just try to import PyQt5 - don't create QApplication yet
            from PyQt5.QtWidgets import QApplication
        except Exception as e:
            gui_available = False
            print("⚠️  Interface gráfica não disponível.")
            print(f"   Erro: {e}")
            print("\n🔧 Executando testes do sistema em modo console...")
            
            # Run console tests instead
            from tests.test_integration import test_complete_workflow
            success = test_complete_workflow()
            return 0 if success else 1
        
        if gui_available:
            print("🚀 Iniciando Keithley LabNano3D v2.0...")
            
            # Import and run startup window - it will create the QApplication
            from startup_window import main as startup_main
            return startup_main()
        
        return 0
        
    except ImportError as e:
        print(f"❌ Dependência não encontrada: {e}")
        print("\n📦 Para instalar as dependências:")
        print("   pip install -r requirements.txt")
        print("\n🔧 Para testar sem interface gráfica:")
        print("   python tests/test_integration.py")
        return 1
    
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

