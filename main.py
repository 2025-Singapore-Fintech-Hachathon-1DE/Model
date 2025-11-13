import pandas as pd

# Excel 파일에서 모든 시트 읽기
excel_path = 'problem_data_final.xlsx'  # 파일명에 맞게 수정
sheets = pd.read_excel(excel_path, sheet_name=None)

for sheet_name, df in sheets.items():
    head_df = df.head(3)
    csv_filename = f"{sheet_name}_head.csv"
    head_df.to_csv(csv_filename, index=False)