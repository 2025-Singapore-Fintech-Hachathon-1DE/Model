"""
시뮬레이션 API 단위 테스트 스크립트
시뮬레이션 기능의 각 부분을 테스트하여 문제점 파악
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from common.data_manager import get_data_manager
from api.data_aggregator import get_aggregator


def print_section(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_1_data_manager_initialization():
    """테스트 1: DataManager 초기화 및 상태 확인"""
    print_section("테스트 1: DataManager 초기화")
    
    try:
        dm = get_data_manager()
        print("✓ DataManager 인스턴스 생성 성공")
        
        # DuckDB 연결 확인
        con = dm.get_connection(persistent=True)
        print("✓ DuckDB 연결 성공")
        
        # 테이블 목록 확인
        tables = con.execute("SHOW TABLES").fetchall()
        print(f"✓ 현재 테이블 수: {len(tables)}")
        
        # simulaterTime 테이블 확인
        try:
            result = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
            if result:
                print(f"✓ 현재 시뮬레이션 시간: {result[0]}")
            else:
                print("⚠ simulaterTime 테이블이 비어있음")
        except Exception as e:
            print(f"✗ simulaterTime 테이블 조회 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ DataManager 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_simulation_status():
    """테스트 2: 시뮬레이션 상태 조회"""
    print_section("테스트 2: 시뮬레이션 상태 조회")
    
    try:
        aggregator = get_aggregator()
        status = aggregator.get_simulation_status()
        
        print(f"상태: {json.dumps(status, indent=2, default=str)}")
        
        if status.get('status') == 'running' and status.get('current_time'):
            print("✓ 시뮬레이션 상태 정상")
            return True
        else:
            print(f"⚠ 시뮬레이션 상태 이상: {status.get('status')}")
            return False
            
    except Exception as e:
        print(f"✗ 상태 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_advance_simulation():
    """테스트 3: 시뮬레이션 진행 (1일)"""
    print_section("테스트 3: 시뮬레이션 1일 진행")
    
    try:
        dm = get_data_manager()
        con = dm.get_connection(persistent=True)
        
        # 진행 전 시간
        before = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
        print(f"진행 전 시간: {before[0]}")
        
        # 1일 진행
        print("시뮬레이션 1일 진행 중...")
        dm.advance_model_by_days(days=1, hours=0)
        
        # 진행 후 시간
        after = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
        print(f"진행 후 시간: {after[0]}")
        
        # 시간 차이 확인
        from datetime import timedelta
        import pandas as pd
        before_dt = pd.to_datetime(before[0])
        after_dt = pd.to_datetime(after[0])
        diff = after_dt - before_dt
        
        if diff == timedelta(days=1):
            print("✓ 시뮬레이션 1일 진행 성공")
            return True
        else:
            print(f"⚠ 시간 차이가 예상과 다름: {diff}")
            return False
            
    except Exception as e:
        print(f"✗ 시뮬레이션 진행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_data_availability():
    """테스트 4: 데이터 가용성 확인"""
    print_section("테스트 4: 데이터 가용성 확인")
    
    try:
        dm = get_data_manager()
        con = dm.get_connection(persistent=True)
        
        # Trade 테이블 데이터 수 확인
        trade_count = con.execute('SELECT COUNT(*) FROM "Trade"').fetchone()[0]
        print(f"Trade 레코드 수: {trade_count}")
        
        # Funding 테이블 데이터 수 확인
        funding_count = con.execute('SELECT COUNT(*) FROM "Funding"').fetchone()[0]
        print(f"Funding 레코드 수: {funding_count}")
        
        # Reward 테이블 데이터 수 확인
        reward_count = con.execute('SELECT COUNT(*) FROM "Reward"').fetchone()[0]
        print(f"Reward 레코드 수: {reward_count}")
        
        if trade_count > 0 and funding_count > 0:
            print("✓ 데이터 가용성 정상")
            return True
        else:
            print("⚠ 데이터가 부족함")
            return False
            
    except Exception as e:
        print(f"✗ 데이터 확인 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_timeseries_data():
    """테스트 5: 시계열 데이터 생성"""
    print_section("테스트 5: 시계열 데이터 생성")
    
    try:
        aggregator = get_aggregator()
        
        # 강제 리로드
        aggregator.get_all_data(force_reload=True)
        
        # 시계열 데이터 가져오기
        timeseries = aggregator.get_timeseries_data()
        
        print(f"시계열 데이터 포인트 수: {len(timeseries)}")
        
        if len(timeseries) > 0:
            print("첫 5개 데이터 포인트:")
            for i, point in enumerate(timeseries[:5]):
                print(f"  {i+1}. {point}")
            
            print("\n마지막 5개 데이터 포인트:")
            for i, point in enumerate(timeseries[-5:]):
                print(f"  {len(timeseries)-4+i}. {point}")
            
            print("✓ 시계열 데이터 생성 성공")
            return True
        else:
            print("⚠ 시계열 데이터가 비어있음")
            
            # 원본 데이터 확인
            all_data = aggregator.get_all_data()
            
            print("\n디버깅 정보:")
            print(f"  Bonus trade pairs: {len(all_data['bonus'].get('trade_pairs', []))}")
            print(f"  Funding cases: {len(all_data['funding'].get('cases', []))}")
            print(f"  Cooperative pairs: {len(all_data['cooperative'].get('trade_pairs', []))}")
            
            # 샘플 데이터 확인
            bonus_pairs = all_data['bonus'].get('trade_pairs', [])
            if bonus_pairs:
                print(f"\n  첫 번째 Bonus pair 샘플:")
                sample = bonus_pairs[0]
                print(f"    Keys: {list(sample.keys())}")
                print(f"    loser_open_ts: {sample.get('loser_open_ts')}")
            
            return False
            
    except Exception as e:
        print(f"✗ 시계열 데이터 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_reset_simulation():
    """테스트 6: 시뮬레이션 리셋"""
    print_section("테스트 6: 시뮬레이션 리셋")
    
    try:
        dm = get_data_manager()
        con = dm.get_connection(persistent=True)
        
        # 리셋 전 시간
        before = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
        print(f"리셋 전 시간: {before[0]}")
        
        # 리셋
        print("시뮬레이션 리셋 중 (2025-02-01로)...")
        dm.seed_full_and_model(year=2025, month=2)
        
        # 리셋 후 시간
        after = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
        print(f"리셋 후 시간: {after[0]}")
        
        # 2025-03-01인지 확인 (2월 데이터 로드 후 3월 1일이 current_time)
        import pandas as pd
        after_dt = pd.to_datetime(after[0])
        expected = pd.to_datetime('2025-03-01')
        
        if after_dt == expected:
            print("✓ 시뮬레이션 리셋 성공")
            return True
        else:
            print(f"⚠ 리셋 후 시간이 예상과 다름: {after_dt} (예상: {expected})")
            return False
            
    except Exception as e:
        print(f"✗ 시뮬레이션 리셋 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "시뮬레이션 API 단위 테스트" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")
    
    tests = [
        ("DataManager 초기화", test_1_data_manager_initialization),
        ("시뮬레이션 상태 조회", test_2_simulation_status),
        ("데이터 가용성 확인", test_4_data_availability),
        ("시계열 데이터 생성", test_5_timeseries_data),
        ("시뮬레이션 진행", test_3_advance_simulation),
        ("시뮬레이션 리셋", test_6_reset_simulation),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ 테스트 '{name}' 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 결과 요약
    print_section("테스트 결과 요약")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {name}")
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠ {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
