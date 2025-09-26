#!/usr/bin/env python3
"""
캠페인 '[엠아트]250922' 추적 시스템 실행 스크립트

이 스크립트를 실행하면 캠페인 '[엠아트]250922'와 그 하위 광고 세트들의 
성과 데이터를 1시간 주기로 수집하여 구글 스프레드시트에 업데이트합니다.

사용법:
    python run_campaign_tracker.py          # 스케줄러 실행 (1시간 주기)
    python run_campaign_tracker.py once     # 한 번만 실행
    python run_campaign_tracker.py status   # 상태 확인
"""

import sys
import os
import subprocess
import venv
from pathlib import Path

def setup_virtual_environment():
    """가상환경 자동 설정"""
    venv_path = Path("campaign_env")
    requirements_file = Path("requirements.txt")
    
    print("🔧 가상환경 설정을 확인합니다...")
    
    # 가상환경이 없으면 생성
    if not venv_path.exists():
        print("📦 가상환경을 생성합니다...")
        try:
            venv.create(venv_path, with_pip=True)
            print("✅ 가상환경 생성 완료")
        except Exception as e:
            print(f"❌ 가상환경 생성 실패: {e}")
            return False
    else:
        print("✅ 가상환경이 이미 존재합니다")
    
    # 가상환경의 Python 경로
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # macOS/Linux
        python_path = venv_path / "bin" / "python"
        pip_path = venv_path / "bin" / "pip"
    
    # 패키지 설치 확인
    if requirements_file.exists():
        print("📋 필요한 패키지를 확인합니다...")
        try:
            # pip list로 설치된 패키지 확인
            result = subprocess.run([str(pip_path), "list"], 
                                  capture_output=True, text=True, check=True)
            installed_packages = result.stdout.lower()
            
            # 주요 패키지들이 설치되어 있는지 확인
            required_packages = ['facebook-business', 'gspread', 'pandas', 'schedule']
            missing_packages = []
            
            for package in required_packages:
                if package not in installed_packages:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"📦 누락된 패키지를 설치합니다: {', '.join(missing_packages)}")
                subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], 
                             check=True)
                print("✅ 패키지 설치 완료")
            else:
                print("✅ 모든 패키지가 설치되어 있습니다")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ 패키지 설치 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ 패키지 확인 중 오류: {e}")
            return False
    
    return str(python_path)

def check_environment_variables():
    """환경 변수 확인"""
    required_env_vars = [
        'META_APP_ID', 'META_APP_SECRET', 'META_ACCESS_TOKEN', 
        'META_AD_ACCOUNT_ID', 'GOOGLE_SHEET_ID'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 다음 환경 변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("env_example.txt 파일을 참고하여 .env 파일을 생성해주세요.")
        return False
    
    print("✅ 환경 변수 확인 완료")
    return True

def run_in_venv(python_path, script_args):
    """가상환경에서 스크립트 실행"""
    try:
        # 현재 스크립트의 경로
        current_script = Path(__file__).resolve()
        
        # 가상환경의 Python으로 campaign_tracker 실행
        cmd = [python_path, "-c", f"""
import sys
sys.path.insert(0, '{current_script.parent}')
from campaign_tracker import CampaignTracker

tracker = CampaignTracker()

if len({script_args}) > 1:
    command = {script_args}[1].lower()
    
    if command == "once":
        print("🔄 단일 실행 모드")
        print("캠페인 데이터를 한 번만 수집하여 스프레드시트에 업데이트합니다.")
        print()
        tracker.run_once()
        
    elif command == "status":
        print("📊 상태 확인 모드")
        print()
        try:
            tracker.initialize()
            status = tracker.get_status()
            
            print(f"캠페인명: {{status.get('campaign_name', 'N/A')}}")
            print(f"캠페인 ID: {{status.get('campaign_id', 'N/A')}}")
            print(f"광고 세트 수: {{status.get('adset_count', 'N/A')}}개")
            print(f"상태: {{status.get('status', 'N/A')}}")
            
            if status.get('sheets_url'):
                print(f"스프레드시트: {{status['sheets_url']}}")
                
        except Exception as e:
            print(f"❌ 상태 확인 실패: {{e}}")
            
    elif command == "schedule":
        print("⏰ 스케줄러 모드")
        print("1시간 주기로 캠페인 데이터를 수집하여 스프레드시트에 업데이트합니다.")
        print("Ctrl+C로 중지할 수 있습니다.")
        print()
        tracker.run_scheduler()
        
    else:
        print("❌ 알 수 없는 명령어입니다.")
        print()
        print("사용법:")
        print("  python run_campaign_tracker.py          # 스케줄러 실행")
        print("  python run_campaign_tracker.py once     # 한 번만 실행")
        print("  python run_campaign_tracker.py status   # 상태 확인")
        print("  python run_campaign_tracker.py schedule # 스케줄러 실행")
else:
    print("⏰ 기본 모드: 스케줄러 실행")
    print("1시간 주기로 캠페인 데이터를 수집하여 스프레드시트에 업데이트합니다.")
    print("Ctrl+C로 중지할 수 있습니다.")
    print()
    
    # 사용자 확인
    try:
        response = input("계속하시겠습니까? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("취소되었습니다.")
            exit()
    except KeyboardInterrupt:
        print("\\n취소되었습니다.")
        exit()
    
    print()
    tracker.run_scheduler()
"""]
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 실행 실패: {e}")
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중지되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

def main():
    print("=" * 60)
    print("캠페인 '[엠아트]250922' 추적 시스템")
    print("=" * 60)
    print()
    
    # 1. 가상환경 설정
    python_path = setup_virtual_environment()
    if not python_path:
        print("❌ 가상환경 설정에 실패했습니다.")
        return
    
    print()
    
    # 2. 환경 변수 확인 (가상환경에서)
    print("🔍 환경 변수를 확인합니다...")
    try:
        # 가상환경에서 환경 변수 확인
        result = subprocess.run([python_path, "-c", """
import os
from dotenv import load_dotenv

load_dotenv()

required_vars = ['META_APP_ID', 'META_APP_SECRET', 'META_ACCESS_TOKEN', 'META_AD_ACCOUNT_ID', 'GOOGLE_SHEET_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print("MISSING:" + ",".join(missing_vars))
else:
    print("OK")
"""], capture_output=True, text=True, check=True)
        
        if result.stdout.strip().startswith("MISSING:"):
            missing_vars = result.stdout.strip().replace("MISSING:", "").split(",")
            print("❌ 다음 환경 변수가 설정되지 않았습니다:")
            for var in missing_vars:
                print(f"   - {var}")
            print()
            print("env_example.txt 파일을 참고하여 .env 파일을 생성해주세요.")
            return
        else:
            print("✅ 환경 변수 확인 완료")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 환경 변수 확인 실패: {e}")
        return
    
    print()
    
    # 3. 가상환경에서 실행
    print("🚀 가상환경에서 캠페인 추적 시스템을 실행합니다...")
    print()
    run_in_venv(python_path, sys.argv)

if __name__ == "__main__":
    main()
