"""
시뮬레이션 초기화 스크립트
DB를 초기 상태(2025-02-01)로 설정
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from common.data_manager import get_data_manager


def main():
    print("=" * 80)
    print("시뮬레이션 초기화 시작")
    print("=" * 80)
    
    dm = get_data_manager()
    
    print("\n2025년 2월로 시뮬레이션 초기화 중...")
    dm.seed_full_and_model(year=2025, month=2)
    
    # 상태 확인
    con = dm.get_connection(persistent=True)
    result = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
    
    if result:
        print(f"\n✓ 시뮬레이션 초기화 완료!")
        print(f"✓ 현재 시뮬레이션 시간: {result[0]}")
    else:
        print("\n✗ 초기화 실패")
        return 1
    
    # 테이블 확인
    tables = con.execute("SHOW TABLES").fetchall()
    print(f"\n✓ 생성된 테이블 수: {len(tables)}")
    print("테이블 목록:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "=" * 80)
    print("초기화 완료!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
