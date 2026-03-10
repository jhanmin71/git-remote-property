import pandas as pd
from pathlib import Path

# 데이터 생성
data = {
    '물건유형': ['주택', '주택', '상업용', '상업용', '주택', '주택'],
    '경매사건번호': ['2024-12345', '2024-12346', '2024-12347', '2024-12348', '2024-12349', '2024-12350'],
    '주소1': ['서울시 강남구', '서울시 강남구', '서울시 강남구', '서울시 마포구', '서울시 마포구', '서울시 송파구'],
    '주소2': ['테헤란로 123', '강남대로 456', '논현로 789', '월드컵로 111', '윤봉길로 222', '올림픽로 333'],
    '평수': [33.0, 33.0, 20.0, 25.0, 42.0, 42.0],
    '예상낙찰가': [450000000, 480000000, 350000000, 280000000, 520000000, 550000000]
}

df = pd.DataFrame(data)

# 경로 생성
data_dir = Path('data/samples')
data_dir.mkdir(parents=True, exist_ok=True)

# 파일 저장
output_path = data_dir / 'test_auction_data.xlsx'
df.to_excel(output_path, index=False, sheet_name='부동산물건')

print('✅ 테스트 파일 생성 완료')
print(f'📁 저장 경로: {output_path.absolute()}')
print(f'📊 데이터 행 수: {len(df)}')
print('\n컬럼:')
for col in df.columns:
    print(f'  - {col}')
print('\n샘플 데이터:')
print(df.to_string())
