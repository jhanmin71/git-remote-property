import aiohttp
import pandas as pd
from typing import Optional, Dict, List
import asyncio
from datetime import datetime


class AuctionFinder:
    """경매사건번호로 경매현황을 조회하는 모듈"""
    
    # 대법원 경매정보 시스템 API
    BASE_URL = "https://www.court.go.kr/ecms/ecmsView"
    
    @staticmethod
    def validate_auction_number(number: str) -> bool:
        """경매사건번호 형식 검증 (예: 2024-12345)"""
        if not isinstance(number, str):
            return False
        parts = number.split('-')
        return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()
    
    @staticmethod
    async def search_auction(auction_number: str) -> Optional[Dict]:
        """
        경매사건번호로 경매현황 조회
        
        Args:
            auction_number: 경매사건번호 (예: 2024-12345)
            
        Returns:
            경매 정보 딕셔너리 또는 None
        """
        if not AuctionFinder.validate_auction_number(auction_number):
            return None
        
        try:
            # 실제 대법원 API 호출 (공개 정보 활용)
            # 현재는 구조를 위해 기본 정보를 반환하도록 설정
            return {
                "경매사건번호": auction_number,
                "상태": "조회 불가",
                "조회일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "비고": "대법원 API 연동 필요"
            }
        except Exception as e:
            print(f"경매 조회 실패: {auction_number}, 오류: {str(e)}")
            return None
    
    @staticmethod
    async def search_auctions_batch(auction_numbers: List[str]) -> pd.DataFrame:
        """
        여러 경매사건번호 일괄 조회
        
        Args:
            auction_numbers: 경매사건번호 리스트
            
        Returns:
            경매 정보 DataFrame
        """
        results = []
        
        # 동시성 문제 방지: 한 번에 최대 10개씩 처리
        chunk_size = 10
        for i in range(0, len(auction_numbers), chunk_size):
            chunk = auction_numbers[i:i+chunk_size]
            tasks = [AuctionFinder.search_auction(num) for num in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend([r for r in chunk_results if r is not None])
        
        return pd.DataFrame(results) if results else pd.DataFrame()


async def get_auction_info(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    DataFrame에서 경매사건번호 컬럼을 찾아 경매현황 조회
    
    Args:
        df: 업로드된 데이터 DataFrame
        
    Returns:
        경매 정보 DataFrame 또는 None
    """
    # 경매사건번호 컬럼 찾기
    auction_columns = [col for col in df.columns if '경매' in col or '사건' in col]
    
    if not auction_columns:
        return None
    
    auction_col = auction_columns[0]
    auction_numbers = df[auction_col].astype(str).unique().tolist()
    
    # 유효한 사건번호만 필터링
    valid_numbers = [num for num in auction_numbers if AuctionFinder.validate_auction_number(num)]
    
    if not valid_numbers:
        return None
    
    # 경매 정보 조회
    auction_df = await AuctionFinder.search_auctions_batch(valid_numbers)
    
    return auction_df if not auction_df.empty else None
