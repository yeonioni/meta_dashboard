#!/usr/bin/env python3
"""
Meta 광고 성과 대시보드 런처
간편한 실행을 위한 스크립트 (가상환경 자동 설정 포함)
"""

import os
import sys
import subprocess
import logging
import platform
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_venv_paths():
    """운영체제별 가상환경 경로 반환"""
    venv_dir = Path("venv")
    
    if platform.system() == "Windows":
        return {
            'python': venv_dir / "Scripts" / "python.exe",
            'pip': venv_dir / "Scripts" / "pip.exe",
            'activate': venv_dir / "Scripts" / "activate.bat"
        }
    else:
        return {
            'python': venv_dir / "bin" / "python",
            'pip': venv_dir / "bin" / "pip",
            'activate': venv_dir / "bin" / "activate"
        }

def create_virtual_environment():
    """가상환경 생성"""
    venv_dir = Path("venv")
    
    if venv_dir.exists():
        logger.info("✅ 가상환경이 이미 존재합니다.")
        return True
    
    logger.info("가상환경을 생성하는 중...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
        logger.info("✅ 가상환경 생성 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"가상환경 생성 실패: {e}")
        return False

def check_requirements():
    """필수 요구사항 확인"""
    logger.info("필수 요구사항을 확인하는 중...")
    
    # Python 버전 확인
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 이상이 필요합니다.")
        return False
    
    # 필수 파일 확인
    required_files = [
        'requirements.txt',
        'config.py',
        'meta_api_client.py',
        'data_processor.py',
        'sheets_manager.py',
        'dashboard.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"필수 파일이 없습니다: {', '.join(missing_files)}")
        return False
    
    # .env 파일 확인
    if not Path('.env').exists():
        logger.warning(".env 파일이 없습니다. env_example.txt를 참고하여 생성해주세요.")
        logger.info("기본 설정으로 진행합니다.")
    
    logger.info("✅ 필수 요구사항 확인 완료")
    return True

def install_dependencies():
    """가상환경에 의존성 패키지 설치"""
    logger.info("가상환경에 의존성 패키지를 설치하는 중...")
    
    venv_paths = get_venv_paths()
    python_executable = str(venv_paths['python'])
    
    try:
        # pip 업그레이드 (python -m pip 방식 사용)
        subprocess.check_call([python_executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # requirements.txt 설치
        subprocess.check_call([python_executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        logger.info("✅ 의존성 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"패키지 설치 실패: {e}")
        # pip 업그레이드 실패해도 requirements.txt 설치는 시도
        try:
            logger.info("pip 업그레이드를 건너뛰고 패키지 설치를 진행합니다...")
            subprocess.check_call([python_executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            logger.info("✅ 의존성 패키지 설치 완료")
            return True
        except subprocess.CalledProcessError as e2:
            logger.error(f"패키지 설치 최종 실패: {e2}")
            return False

def check_venv_packages():
    """가상환경에 필수 패키지가 설치되어 있는지 확인"""
    venv_paths = get_venv_paths()
    python_executable = str(venv_paths['python'])
    
    required_packages = ['streamlit', 'pandas', 'plotly', 'facebook-business', 'gspread']
    
    try:
        for package in required_packages:
            result = subprocess.run([
                python_executable, '-c', f'import {package.replace("-", "_")}'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return False
        
        logger.info("✅ 필수 패키지가 가상환경에 설치되어 있습니다.")
        return True
    except Exception:
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    directories = ['daily_data', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    logger.info("✅ 디렉토리 생성 완료")

def run_dashboard():
    """가상환경에서 Streamlit 대시보드 실행"""
    logger.info("Meta 광고 성과 대시보드를 시작합니다...")
    logger.info("브라우저에서 http://localhost:8501 로 접속하세요.")
    logger.info("종료하려면 Ctrl+C를 누르세요.")
    
    venv_paths = get_venv_paths()
    python_executable = str(venv_paths['python'])
    
    try:
        subprocess.run([
            python_executable, '-m', 'streamlit', 'run', 'dashboard.py',
            '--server.port', '8501',
            '--server.address', 'localhost'
        ])
    except KeyboardInterrupt:
        logger.info("대시보드가 종료되었습니다.")
    except Exception as e:
        logger.error(f"대시보드 실행 중 오류: {e}")

def setup_virtual_environment():
    """가상환경 설정 및 패키지 설치"""
    # 1. 가상환경 생성
    if not create_virtual_environment():
        logger.error("가상환경 생성에 실패했습니다.")
        return False
    
    # 2. 가상환경에 패키지 설치 여부 확인
    if not check_venv_packages():
        logger.info("가상환경에 필수 패키지를 설치합니다...")
        if not install_dependencies():
            logger.error("패키지 설치에 실패했습니다.")
            return False
    
    return True

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🎯 Meta 광고 성과 대시보드")
    print("🔧 가상환경 자동 설정 포함")
    print("=" * 60)
    
    # 필수 요구사항 확인
    if not check_requirements():
        logger.error("필수 요구사항을 만족하지 않습니다. 설정을 확인해주세요.")
        sys.exit(1)
    
    # 가상환경 설정
    logger.info("가상환경을 설정하는 중...")
    if not setup_virtual_environment():
        logger.error("가상환경 설정에 실패했습니다.")
        sys.exit(1)
    
    # 디렉토리 생성
    create_directories()
    
    # 환경 변수 확인 안내
    if not Path('.env').exists():
        print("\n⚠️  설정 안내:")
        print("1. env_example.txt를 참고하여 .env 파일을 생성하세요.")
        print("2. Meta Marketing API 및 Google Sheets API 설정을 완료하세요.")
        print("3. 설정 완료 후 다시 실행해주세요.")
        
        response = input("\n설정을 완료하셨나요? (y/N): ")
        if response.lower() != 'y':
            print("설정 완료 후 다시 실행해주세요.")
            sys.exit(0)
    
    # 가상환경 정보 출력
    venv_paths = get_venv_paths()
    logger.info(f"🐍 가상환경 Python: {venv_paths['python']}")
    
    # 대시보드 실행
    run_dashboard()

if __name__ == "__main__":
    main() 