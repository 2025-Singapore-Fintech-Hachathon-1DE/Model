"""
Data Aggregator for Detection System
모든 모델의 output을 읽어서 통합하는 레이어
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict


class DataAggregator:
    """모든 탐지 모델의 output 데이터를 통합"""
    
    def __init__(self, output_base_dir: str = "output"):
        self.output_base_dir = Path(output_base_dir)
        self.bonus_dir = self.output_base_dir / "bonus"
        self.funding_dir = self.output_base_dir / "funding_fee"
        self.cooperative_dir = self.output_base_dir / "cooperative"
        
        # 캐시
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    def _read_json(self, filepath: Path) -> Optional[Dict]:
        """JSON 파일 읽기"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return None
    
    def _read_csv(self, filepath: Path) -> Optional[pd.DataFrame]:
        """CSV 파일 읽기"""
        try:
            if filepath.exists():
                return pd.read_csv(filepath, encoding='utf-8-sig')
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return None
    
    def get_all_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """모든 데이터를 통합하여 반환"""
        
        # 캐시 확인 (5분 이내면 캐시 사용)
        if not force_reload and self._cache and self._cache_timestamp:
            elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
            if elapsed < 300:  # 5분
                return self._cache
        
        print("Loading all detection data...")
        
        # 각 모델 데이터 로드
        bonus_data = self._load_bonus_data()
        funding_data = self._load_funding_data()
        cooperative_data = self._load_cooperative_data()
        
        # 데이터 통합
        integrated_data = {
            'bonus': bonus_data,
            'funding': funding_data,
            'cooperative': cooperative_data,
            'timestamp': datetime.now().isoformat(),
        }
        
        # 캐시 업데이트
        self._cache = integrated_data
        self._cache_timestamp = datetime.now()
        
        print("Data loading complete!")
        
        return integrated_data
    
    def _load_bonus_data(self) -> Dict[str, Any]:
        """Bonus Laundering 데이터 로드"""
        print("  - Loading bonus data...")
        
        data = {
            'config': self._read_json(self.bonus_dir / 'detection_config.json'),
            'visualization': self._read_json(self.bonus_dir / 'visualization_data.json'),
            'sanctions': self._read_json(self.bonus_dir / 'sanction_cases.json'),
            'trade_pairs': None,
        }
        
        # CSV 데이터
        trade_pairs_df = self._read_csv(self.bonus_dir / 'trade_pairs_detailed.csv')
        if trade_pairs_df is not None:
            data['trade_pairs'] = trade_pairs_df.to_dict('records')
        
        return data
    
    def _load_funding_data(self) -> Dict[str, Any]:
        """Funding Fee Hunter 데이터 로드"""
        print("  - Loading funding fee data...")
        
        data = {
            'config': self._read_json(self.funding_dir / 'detection_config.json'),
            'visualization': self._read_json(self.funding_dir / 'visualization_data.json'),
            'sanctions': self._read_json(self.funding_dir / 'sanction_accounts.json'),
            'cases': None,
            'account_summaries': None,
        }
        
        # CSV 데이터
        cases_df = self._read_csv(self.funding_dir / 'funding_hunter_cases.csv')
        if cases_df is not None:
            data['cases'] = cases_df.to_dict('records')
        
        account_df = self._read_csv(self.funding_dir / 'account_summaries.csv')
        if account_df is not None:
            data['account_summaries'] = account_df.to_dict('records')
        
        return data
    
    def _load_cooperative_data(self) -> Dict[str, Any]:
        """Cooperative Trading 데이터 로드"""
        print("  - Loading cooperative trading data...")
        
        data = {
            'config': self._read_json(self.cooperative_dir / 'detection_config.json'),
            'visualization': self._read_json(self.cooperative_dir / 'visualization_data.json'),
            'sanctions': self._read_json(self.cooperative_dir / 'sanction_groups.json'),
            'trade_pairs': None,
            'groups': None,
        }
        
        # CSV 데이터
        trade_pairs_df = self._read_csv(self.cooperative_dir / 'trade_pairs_detailed.csv')
        if trade_pairs_df is not None:
            data['trade_pairs'] = trade_pairs_df.to_dict('records')
        
        groups_df = self._read_csv(self.cooperative_dir / 'cooperative_groups.csv')
        if groups_df is not None:
            data['groups'] = groups_df.to_dict('records')
        
        return data
    
    def get_stats(self) -> Dict[str, Any]:
        """전체 통계 반환"""
        all_data = self.get_all_data()
        
        bonus_vis = all_data['bonus'].get('visualization', {})
        funding_vis = all_data['funding'].get('visualization', {})
        coop_vis = all_data['cooperative'].get('visualization', {})
        
        bonus_summary = bonus_vis.get('summary', {}) if bonus_vis else {}
        funding_summary = funding_vis.get('summary', {}) if funding_vis else {}
        coop_summary = coop_vis.get('summary', {}) if coop_vis else {}
        
        return {
            'total_detections': (
                bonus_summary.get('total_pairs', 0) +
                funding_summary.get('total_cases', 0) +
                coop_summary.get('total_pairs', 0)
            ),
            'wash_trading': bonus_summary.get('total_pairs', 0),
            'funding_fee': funding_summary.get('total_cases', 0),
            'cooperative': coop_summary.get('total_pairs', 0),
            'total_sanctions': (
                bonus_summary.get('total_sanctions', 0) +
                funding_summary.get('total_sanction_accounts', 0) +
                coop_summary.get('total_groups', 0)
            ),
            'bonus_details': {
                'bot_tier': bonus_summary.get('bot_tier', 0),
                'manual_tier': bonus_summary.get('manual_tier', 0),
                'suspicious': bonus_summary.get('suspicious', 0),
            },
            'funding_details': {
                'critical': funding_summary.get('critical', 0),
                'high': funding_summary.get('high', 0),
                'medium': funding_summary.get('medium', 0),
            },
            'cooperative_details': {
                'critical': coop_summary.get('critical', 0),
                'high': coop_summary.get('high', 0),
                'medium': coop_summary.get('medium', 0),
            },
        }
    
    def get_sanctions(self) -> List[Dict[str, Any]]:
        """모든 제재 케이스 통합 반환"""
        all_data = self.get_all_data()
        sanctions = []
        
        # Bonus sanctions
        bonus_sanctions = all_data['bonus'].get('sanctions', {})
        if bonus_sanctions and 'cases' in bonus_sanctions:
            for case in bonus_sanctions['cases']:
                sanctions.append({
                    'id': case.get('case_id', ''),
                    'model': 'wash',
                    'timestamp': case.get('detection_timestamp', ''),
                    'type': case.get('sanction_type', ''),
                    'accounts': case.get('account_ids', []),
                    'score': case.get('total_score', 0),
                    'tier': case.get('tier', ''),
                    'details': case.get('evidence_summary', ''),
                    'laundered_amount': case.get('total_laundered_amount', 0),
                    'trade_pair_ids': case.get('trade_pair_ids', []),
                    'raw': case,
                })
        
        # Funding sanctions
        funding_sanctions = all_data['funding'].get('sanctions', {})
        if funding_sanctions and 'accounts' in funding_sanctions:
            for account in funding_sanctions['accounts']:
                sanctions.append({
                    'id': f"FUNDING_{account.get('account_id', '')}",
                    'model': 'funding',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'SANCTION_ACCOUNT',
                    'accounts': [account.get('account_id', '')],
                    'score': account.get('avg_score', 0),
                    'details': f"반복 펀딩비 악용 ({account.get('total_cases', 0)}건)",
                    'total_funding_profit': account.get('total_funding_profit', 0),
                    'critical_count': account.get('critical_count', 0),
                    'high_count': account.get('high_count', 0),
                    'raw': account,
                })
        
        # Cooperative sanctions
        coop_sanctions = all_data['cooperative'].get('sanctions', {})
        if coop_sanctions and 'groups' in coop_sanctions:
            for group in coop_sanctions['groups']:
                sanctions.append({
                    'id': group.get('group_id', ''),
                    'model': 'cooperative',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'COOPERATIVE_GROUP',
                    'accounts': group.get('members', []),
                    'score': group.get('avg_score', 0),
                    'risk_level': group.get('risk_level', ''),
                    'details': f"공모 그룹 ({len(group.get('members', []))}명, {group.get('trade_count', 0)}건 거래)",
                    'pnl_total': group.get('pnl_total', 0),
                    'shared_ip_count': group.get('shared_ip_count', 0),
                    'raw': group,
                })
        
        return sanctions
    
    def get_timeseries_data(self) -> List[Dict[str, Any]]:
        """시계열 데이터 생성 - 데이터베이스에서 직접 조회"""
        from common.data_manager import get_data_manager
        import pandas as pd
        
        timeseries = defaultdict(lambda: {'WASH_TRADING': 0, 'FUNDING_FEE': 0, 'COOPERATIVE': 0})
        
        try:
            dm = get_data_manager()
            con = dm.get_connection(persistent=True)
            
            # 1. Wash Trading (Bonus) - Trade 테이블에서 보너스 관련 거래 조회
            try:
                # Reward 테이블과 조인하여 보너스 후 거래 찾기
                # Reward 테이블에는 position_side가 없으므로 단순히 시간 조건만 체크
                wash_query = """
                SELECT 
                    DATE_TRUNC('hour', CAST(t.ts AS TIMESTAMP)) as hour,
                    COUNT(*) as count
                FROM Trade t
                INNER JOIN Reward r ON t.account_id = r.account_id
                WHERE CAST(t.ts AS TIMESTAMP) > CAST(r.ts AS TIMESTAMP)
                    AND CAST(t.ts AS TIMESTAMP) <= CAST(r.ts AS TIMESTAMP) + INTERVAL '72 hours'
                GROUP BY DATE_TRUNC('hour', CAST(t.ts AS TIMESTAMP))
                """
                wash_df = con.execute(wash_query).fetchdf()
                
                for _, row in wash_df.iterrows():
                    if pd.notna(row['hour']):
                        hour_key = int(pd.to_datetime(row['hour']).timestamp())
                        timeseries[hour_key]['WASH_TRADING'] += int(row['count'])
            except Exception as e:
                print(f"Warning: Wash trading timeseries query failed: {e}")
            
            # 2. Funding Fee - Funding 테이블에서 조회
            try:
                funding_query = """
                SELECT 
                    DATE_TRUNC('hour', CAST(ts AS TIMESTAMP)) as hour,
                    COUNT(*) as count
                FROM Funding
                WHERE funding_fee != 0
                GROUP BY DATE_TRUNC('hour', CAST(ts AS TIMESTAMP))
                """
                funding_df = con.execute(funding_query).fetchdf()
                
                for _, row in funding_df.iterrows():
                    if pd.notna(row['hour']):
                        hour_key = int(pd.to_datetime(row['hour']).timestamp())
                        timeseries[hour_key]['FUNDING_FEE'] += int(row['count'])
            except Exception as e:
                print(f"Warning: Funding fee timeseries query failed: {e}")
            
            # 3. Cooperative Trading - Trade 테이블에서 동시 거래 찾기
            try:
                # 간단히 모든 거래를 시간별로 집계 (실제로는 쌍을 이루는 거래만 계산해야 하지만, 근사치로 사용)
                coop_query = """
                SELECT 
                    DATE_TRUNC('hour', CAST(ts AS TIMESTAMP)) as hour,
                    COUNT(DISTINCT position_id) as count
                FROM Trade
                WHERE position_id IS NOT NULL
                GROUP BY DATE_TRUNC('hour', CAST(ts AS TIMESTAMP))
                HAVING COUNT(DISTINCT account_id) > 1
                """
                coop_df = con.execute(coop_query).fetchdf()
                
                for _, row in coop_df.iterrows():
                    if pd.notna(row['hour']):
                        hour_key = int(pd.to_datetime(row['hour']).timestamp())
                        # 협력 거래는 과대 계산되지 않도록 조정
                        timeseries[hour_key]['COOPERATIVE'] += max(1, int(row['count']) // 10)
            except Exception as e:
                print(f"Warning: Cooperative timeseries query failed: {e}")
                
        except Exception as e:
            print(f"Error generating timeseries data: {e}")
        
        # 정렬 및 포맷
        result = []
        for timestamp in sorted(timeseries.keys()):
            result.append({
                'time': int(timestamp * 1000),  # JavaScript timestamp (milliseconds)
                'WASH_TRADING': timeseries[timestamp]['WASH_TRADING'],
                'FUNDING_FEE': timeseries[timestamp]['FUNDING_FEE'],
                'COOPERATIVE': timeseries[timestamp]['COOPERATIVE'],
            })
        
        return result
    
    def get_top_accounts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """상위 위반 계정 리스트"""
        all_data = self.get_all_data()
        account_map = defaultdict(lambda: {
            'account_id': '',
            'total_cases': 0,
            'total_profit_loss': 0.0,
            'profits': {'funding': 0.0, 'wash': 0.0, 'cooperative': 0.0},
            'avg_score': 0.0,
            'max_score': 0.0,
            'critical_count': 0,
            'high_count': 0,
            'scores': [],
        })
        
        # Funding accounts
        funding_accounts = all_data['funding'].get('account_summaries', [])
        if funding_accounts:
            for acc in funding_accounts:
                account_id = acc.get('account_id', '')
                if account_id:
                    account_map[account_id]['account_id'] = account_id
                    account_map[account_id]['total_cases'] += acc.get('total_cases', 0)
                    account_map[account_id]['profits']['funding'] += acc.get('total_funding_profit', 0)
                    account_map[account_id]['total_profit_loss'] += acc.get('total_funding_profit', 0)
                    account_map[account_id]['critical_count'] += acc.get('critical_count', 0)
                    account_map[account_id]['high_count'] += acc.get('high_count', 0)
                    avg_score = acc.get('avg_score', 0)
                    if avg_score:
                        account_map[account_id]['scores'].append(avg_score)
        
        # Bonus pairs - winner accounts
        bonus_pairs = all_data['bonus'].get('trade_pairs', [])
        if bonus_pairs:
            for pair in bonus_pairs:
                winner = pair.get('winner_account', '')
                if winner:
                    account_map[winner]['account_id'] = winner
                    account_map[winner]['total_cases'] += 1
                    account_map[winner]['profits']['wash'] += pair.get('laundered_amount', 0)
                    account_map[winner]['total_profit_loss'] += pair.get('laundered_amount', 0)
                    score = pair.get('total_score', 0)
                    if score:
                        account_map[winner]['scores'].append(score)
        
        # Cooperative groups - all members
        coop_groups = all_data['cooperative'].get('groups', [])
        if coop_groups:
            for group in coop_groups:
                members_str = group.get('members', '')
                if isinstance(members_str, str):
                    members = [m.strip() for m in members_str.split(',')]
                else:
                    members = []
                
                pnl_per_member = group.get('pnl_total', 0) / len(members) if members else 0
                
                for member in members:
                    if member:
                        account_map[member]['account_id'] = member
                        account_map[member]['total_cases'] += 1
                        account_map[member]['profits']['cooperative'] += pnl_per_member
                        account_map[member]['total_profit_loss'] += pnl_per_member
                        score = group.get('avg_score', 0)
                        if score:
                            account_map[member]['scores'].append(score)
        
        # 평균 점수 계산
        for acc in account_map.values():
            if acc['scores']:
                acc['avg_score'] = sum(acc['scores']) / len(acc['scores'])
                acc['max_score'] = max(acc['scores'])
            del acc['scores']  # 최종 결과에서 제외
        
        # 정렬 및 제한
        accounts = sorted(
            account_map.values(),
            key=lambda x: x['total_profit_loss'],
            reverse=True
        )[:limit]
        
        return accounts
    
    def get_hourly_distribution(self) -> Dict[int, int]:
        """시간대별 탐지 분포"""
        all_data = self.get_all_data()
        hourly = defaultdict(int)
        
        # Bonus
        bonus_vis = all_data['bonus'].get('visualization', {})
        if bonus_vis:
            bonus_hourly = bonus_vis.get('time_patterns', {}).get('hourly_distribution', {})
            for hour, count in bonus_hourly.items():
                hourly[int(hour)] += count
        
        # Funding
        funding_vis = all_data['funding'].get('visualization', {})
        if funding_vis:
            funding_hourly = funding_vis.get('hourly_distribution', {})
            for hour, count in funding_hourly.items():
                hourly[int(hour)] += count
        
        # Cooperative - 시간 정보가 있다면 추가
        
        return dict(hourly)
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """시각화 데이터 통합"""
        all_data = self.get_all_data()
        
        return {
            'bonus': all_data['bonus'].get('visualization', {}),
            'funding': all_data['funding'].get('visualization', {}),
            'cooperative': all_data['cooperative'].get('visualization', {}),
        }
    
    def get_trade_pairs(self, model: str) -> List[Dict[str, Any]]:
        """특정 모델의 trade pairs 반환"""
        all_data = self.get_all_data()
        
        if model == 'wash':
            return all_data['bonus'].get('trade_pairs', [])
        elif model == 'cooperative':
            return all_data['cooperative'].get('trade_pairs', [])
        elif model == 'funding':
            return all_data['funding'].get('cases', [])
        
        return []
    
    def get_cooperative_groups(self) -> List[Dict[str, Any]]:
        """Cooperative groups 정보 반환"""
        all_data = self.get_all_data()
        return all_data['cooperative'].get('groups', [])
    
    def get_account_trade_history(self, account_id: str) -> List[Dict[str, Any]]:
        """특정 계정의 거래 이력 반환
        
        Note: 현재는 탐지된 거래만 반환. 
        전체 거래 이력은 별도 데이터베이스 쿼리 필요.
        """
        all_data = self.get_all_data()
        trades = []
        
        # Bonus trade pairs에서 찾기
        bonus_pairs = all_data['bonus'].get('trade_pairs', [])
        if bonus_pairs:
            for pair in bonus_pairs:
                if pair.get('winner_account') == account_id or pair.get('loser_account') == account_id:
                    trades.append({
                        'trade_id': pair.get('pair_id', ''),
                        'account_id': account_id,
                        'timestamp': pair.get('loser_open_ts', ''),
                        'symbol': pair.get('symbol', ''),
                        'side': 'LONG' if pair.get('loser_side') == 'LONG' else 'SHORT',
                        'position_id': '',
                        'leverage': pair.get('leverage', 0),
                        'price': pair.get('loser_open_price', 0),
                        'quantity': pair.get('loser_quantity', 0),
                        'amount': pair.get('laundered_amount', 0),
                        'model': 'wash',
                        'raw': pair
                    })
        
        # Funding cases에서 찾기
        funding_cases = all_data['funding'].get('cases', [])
        if funding_cases:
            for case in funding_cases:
                if case.get('account_id') == account_id:
                    trades.append({
                        'trade_id': case.get('case_id', ''),
                        'account_id': account_id,
                        'timestamp': case.get('open_ts', ''),
                        'symbol': case.get('symbol', ''),
                        'side': case.get('side', ''),
                        'position_id': case.get('position_id', ''),
                        'leverage': case.get('leverage', 0),
                        'price': case.get('open_price', 0),
                        'quantity': case.get('amount', 0),
                        'amount': case.get('total_funding', 0),
                        'model': 'funding',
                        'raw': case
                    })
        
        # Cooperative pairs에서 찾기
        coop_pairs = all_data['cooperative'].get('trade_pairs', [])
        if coop_pairs:
            for pair in coop_pairs:
                if pair.get('account1') == account_id:
                    trades.append({
                        'trade_id': f"{pair.get('pair_id', '')}_1",
                        'account_id': account_id,
                        'timestamp': pair.get('open_ts1', ''),
                        'symbol': pair.get('symbol', ''),
                        'side': pair.get('side1', ''),
                        'position_id': '',
                        'leverage': pair.get('leverage1', 0),
                        'price': pair.get('open_price1', 0),
                        'quantity': pair.get('quantity1', 0),
                        'amount': 0,
                        'model': 'cooperative',
                        'raw': pair
                    })
                if pair.get('account2') == account_id:
                    trades.append({
                        'trade_id': f"{pair.get('pair_id', '')}_2",
                        'account_id': account_id,
                        'timestamp': pair.get('open_ts2', ''),
                        'symbol': pair.get('symbol', ''),
                        'side': pair.get('side2', ''),
                        'position_id': '',
                        'leverage': pair.get('leverage2', 0),
                        'price': pair.get('open_price2', 0),
                        'quantity': pair.get('quantity2', 0),
                        'amount': 0,
                        'model': 'cooperative',
                        'raw': pair
                    })
        
        return trades
    
    def get_case_detail(self, model: str, case_id: str) -> Optional[Dict[str, Any]]:
        """특정 케이스의 상세 정보 반환"""
        all_data = self.get_all_data()
        
        if model == 'wash':
            pairs = all_data['bonus'].get('trade_pairs', [])
            if pairs:
                for pair in pairs:
                    if pair.get('pair_id') == case_id:
                        return pair
        
        elif model == 'funding':
            cases = all_data['funding'].get('cases', [])
            if cases:
                for case in cases:
                    if case.get('case_id') == case_id:
                        return case
        
        elif model == 'cooperative':
            # pair_id로 찾기
            pairs = all_data['cooperative'].get('trade_pairs', [])
            if pairs:
                for pair in pairs:
                    if pair.get('pair_id') == case_id:
                        return pair
            
            # group_id로 찾기
            groups = all_data['cooperative'].get('groups', [])
            if groups:
                for group in groups:
                    if group.get('group_id') == case_id:
                        return group
        
        return None
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """시뮬레이션 현재 상태 조회"""
        from common.data_manager import get_data_manager
        
        try:
            dm = get_data_manager()
            con = dm.get_connection(persistent=True)
            
            # simulaterTime 테이블에서 current_time 조회
            result = con.execute('SELECT current_time FROM "simulaterTime"').fetchone()
            current_time = result[0] if result else None
            
            if current_time:
                return {
                    'current_time': str(current_time),
                    'status': 'running'
                }
            else:
                return {
                    'current_time': None,
                    'status': 'not_initialized'
                }
        except Exception as e:
            return {
                'current_time': None,
                'status': 'error',
                'error': str(e)
            }


# 싱글톤 인스턴스
_aggregator_instance: Optional[DataAggregator] = None


def get_aggregator(output_base_dir: str = "output") -> DataAggregator:
    """DataAggregator 싱글톤 인스턴스 반환"""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = DataAggregator(output_base_dir)
    return _aggregator_instance
