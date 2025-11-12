"""
Wash Trading Detection API
웹 대시보드를 위한 API 래퍼
"""

from bonus.washTrading import (
    DetectionConfig, DataLoader, LaunderingDetector, 
    LaunderingAnalyzer, ScoreCalculator
)
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import json


class WashTradingAPI:
    """웹 대시보드를 위한 Wash Trading 탐지 API"""
    
    def __init__(self):
        self.config = None
        self.loader = None
        self.detector = None
        self.analyzer = None
        self.results = None
        self.analysis = None
        self.data = None
        
    def set_config(self, config_dict: Dict) -> DetectionConfig:
        """딕셔너리에서 DetectionConfig 생성"""
        self.config = DetectionConfig(**config_dict)
        return self.config
    
    def load_data(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """데이터 로드 및 저장"""
        self.loader = DataLoader(filepath)
        self.data = self.loader.load_excel_data()
        return self.data
    
    def run_detection(self, config: Optional[DetectionConfig] = None) -> Dict:
        """탐지 실행"""
        if config:
            self.config = config
        elif not self.config:
            self.config = DetectionConfig()
        
        if not self.loader:
            raise ValueError("데이터를 먼저 로드해야 합니다. load_data()를 호출하세요.")
        
        # 탐지 실행
        self.detector = LaunderingDetector(self.loader, self.config)
        self.results = self.detector.detect()
        
        # 분석 실행
        self.analyzer = LaunderingAnalyzer(self.config)
        self.analysis = self.analyzer.analyze_results(self.results)
        
        return {
            'results': self.results,
            'analysis': self.analysis,
            'config': self.config.to_dict()
        }
    
    def get_results(self) -> List[Dict]:
        """탐지 결과 반환"""
        return self.results or []
    
    def get_analysis(self) -> Dict:
        """분석 결과 반환"""
        return self.analysis or {}
    
    def get_data_summary(self) -> Dict:
        """데이터 요약 정보 반환"""
        if not self.data:
            return {}
        
        summary = {}
        for sheet_name, df in self.data.items():
            summary[sheet_name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
            }
            
            # 타임스탬프 범위
            if 'ts' in df.columns:
                summary[sheet_name]['time_range'] = {
                    'start': df['ts'].min().isoformat() if pd.notna(df['ts'].min()) else None,
                    'end': df['ts'].max().isoformat() if pd.notna(df['ts'].max()) else None,
                }
        
        return summary
    
    def get_timeline_data(self) -> List[Dict]:
        """타임라인 시각화를 위한 데이터"""
        if not self.results:
            return []
        
        timeline = []
        for r in self.results:
            timeline.append({
                'bonus_ts': r['bonus_ts'],
                'trade_open_ts': r['loser_open_ts'],
                'trade_close_ts': r['loser_close_ts'],
                'loser_account': r['loser_account'],
                'winner_account': r['winner_account'],
                'amount': r['laundered_amount'],
                'score': r['total_score'],
                'symbol': r['symbol'],
            })
        
        return sorted(timeline, key=lambda x: x['bonus_ts'])
    
    def get_network_data(self) -> Dict:
        """네트워크 그래프를 위한 데이터 (노드와 엣지)"""
        if not self.results:
            return {'nodes': [], 'edges': []}
        
        nodes = {}
        edges = []
        
        for r in self.results:
            loser = r['loser_account']
            winner = r['winner_account']
            
            # 노드 추가
            if loser not in nodes:
                nodes[loser] = {
                    'id': loser,
                    'type': 'loser',
                    'total_loss': 0,
                    'trade_count': 0,
                }
            if winner not in nodes:
                nodes[winner] = {
                    'id': winner,
                    'type': 'winner',
                    'total_profit': 0,
                    'trade_count': 0,
                }
            
            # 노드 정보 업데이트
            nodes[loser]['total_loss'] += r['loser_pnl']
            nodes[loser]['trade_count'] += 1
            nodes[winner]['total_profit'] += r['laundered_amount']
            nodes[winner]['trade_count'] += 1
            
            # 엣지 추가
            edges.append({
                'source': loser,
                'target': winner,
                'weight': r['laundered_amount'],
                'score': r['total_score'],
                'symbol': r['symbol'],
                'trade_count': 1,
            })
        
        return {
            'nodes': list(nodes.values()),
            'edges': edges,
        }
    
    def get_time_series_data(self) -> pd.DataFrame:
        """시계열 분석을 위한 데이터"""
        if not self.results:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.results)
        df['loser_open_ts'] = pd.to_datetime(df['loser_open_ts'])
        df = df.sort_values('loser_open_ts')
        
        # 일별 집계
        df['date'] = df['loser_open_ts'].dt.date
        daily = df.groupby('date').agg({
            'laundered_amount': 'sum',
            'loser_pnl': 'sum',
            'total_score': 'mean',
            'loser_account': 'count',
        }).reset_index()
        daily.columns = ['date', 'total_laundered', 'total_loss', 'avg_score', 'trade_count']
        
        return daily
    
    def get_account_profile(self, account_id: str) -> Dict:
        """특정 계정의 상세 프로필"""
        if not self.results:
            return {}
        
        # 계정이 손실 계정인지 수익 계정인지 확인
        loser_trades = [r for r in self.results if r['loser_account'] == account_id]
        winner_trades = [r for r in self.results if r['winner_account'] == account_id]
        
        profile = {
            'account_id': account_id,
            'role': None,
            'total_trades': 0,
            'total_amount': 0,
            'avg_score': 0,
            'partners': [],
            'symbols': set(),
            'trades': [],
        }
        
        if loser_trades:
            profile['role'] = 'loser'
            profile['total_trades'] = len(loser_trades)
            profile['total_amount'] = sum(r['loser_pnl'] for r in loser_trades)
            profile['avg_score'] = sum(r['total_score'] for r in loser_trades) / len(loser_trades)
            profile['partners'] = list(set(r['winner_account'] for r in loser_trades))
            profile['symbols'] = list(set(r['symbol'] for r in loser_trades))
            profile['trades'] = loser_trades
        elif winner_trades:
            profile['role'] = 'winner'
            profile['total_trades'] = len(winner_trades)
            profile['total_amount'] = sum(r['laundered_amount'] for r in winner_trades)
            profile['avg_score'] = sum(r['total_score'] for r in winner_trades) / len(winner_trades)
            profile['partners'] = list(set(r['loser_account'] for r in winner_trades))
            profile['symbols'] = list(set(r['symbol'] for r in winner_trades))
            profile['trades'] = winner_trades
        
        return profile
    
    def filter_results(self, 
                      min_score: Optional[float] = None,
                      max_score: Optional[float] = None,
                      accounts: Optional[List[str]] = None,
                      symbols: Optional[List[str]] = None,
                      min_amount: Optional[float] = None,
                      max_amount: Optional[float] = None) -> List[Dict]:
        """결과 필터링"""
        if not self.results:
            return []
        
        filtered = self.results.copy()
        
        if min_score is not None:
            filtered = [r for r in filtered if r['total_score'] >= min_score]
        
        if max_score is not None:
            filtered = [r for r in filtered if r['total_score'] <= max_score]
        
        if accounts:
            filtered = [r for r in filtered if r['loser_account'] in accounts or r['winner_account'] in accounts]
        
        if symbols:
            filtered = [r for r in filtered if r['symbol'] in symbols]
        
        if min_amount is not None:
            filtered = [r for r in filtered if r['laundered_amount'] >= min_amount]
        
        if max_amount is not None:
            filtered = [r for r in filtered if r['laundered_amount'] <= max_amount]
        
        return filtered
    
    def export_results(self, output_dir: str = "output/bonus"):
        """결과를 파일로 내보내기"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not self.results:
            return None
        
        # JSON
        with open(output_path / 'results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'results': self.results,
                'analysis': self.analysis,
            }, f, indent=2, ensure_ascii=False)
        
        # CSV
        df = pd.DataFrame(self.results)
        df.to_csv(output_path / 'results.csv', index=False)
        
        return str(output_path)
