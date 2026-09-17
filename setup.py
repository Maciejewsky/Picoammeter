#!/usr/bin/env python3
"""
Setup script for Keithley LabNano3D
Validates environment and provides helpful setup information
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário")
        print(f"   Versão atual: {sys.version}")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('pyvisa', 'pyvisa'),
        ('numpy', 'numpy'),
        ('matplotlib', 'matplotlib'),
        ('pyqtgraph', 'pyqtgraph'),
        ('pyserial', 'serial')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name}")
            missing_packages.append(package_name)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("\n🔧 Instalando dependências...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependências instaladas com sucesso")
            return True
        else:
            print("❌ Erro na instalação:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def check_visa_backend():
    """Check VISA backend availability"""
    try:
        import pyvisa
        rm = pyvisa.ResourceManager()
        backends = rm.list_backends()
        print(f"✅ VISA backends disponíveis: {len(backends)}")
        for backend in backends:
            print(f"   - {backend}")
        rm.close()
        return True
    except Exception as e:
        print(f"⚠️  VISA backend: {e}")
        print("   Nota: É normal não ter instrumentos conectados durante o setup")
        return True

def main():
    """Main setup function"""
    print("🔬 Keithley LabNano3D - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print("\n📦 Verificando dependências:")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠️  Dependências não encontradas: {', '.join(missing)}")
        response = input("Deseja instalar agora? (s/N): ").lower()
        
        if response in ['s', 'sim', 'y', 'yes']:
            if not install_dependencies():
                sys.exit(1)
        else:
            print("Para instalar manualmente: pip install -r requirements.txt")
            sys.exit(1)
    
    print("\n🔌 Verificando backend VISA:")
    check_visa_backend()
    
    print("\n✅ Setup concluído!")
    print("\n🚀 Para iniciar a aplicação:")
    print("   python main.py")
    print("\n📚 Documentação:")
    print("   README.md - Guia completo")
    print("   STRUCTURE.md - Estrutura do código")
    print("   ROADMAP.md - Plano de desenvolvimento")

if __name__ == "__main__":
    main()