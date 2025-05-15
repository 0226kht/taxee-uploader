
import streamlit as st
import pandas as pd
import io
import re
import openpyxl

st.set_page_config(page_title="Taxee 리포트 업로드", layout="centered")
st.title("📤 세무자료 업로드 & 자동 리포트")

# 1. 고객명, 기준월 입력
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("고객명")
    with col2:
        month = st.text_input("자료 기준월 (예: 2025-04)")

    submit = st.form_submit_button("입력 완료")

# 2. 기준월 형식 검증 (yyyy-mm)
month_valid = False
if month:
    if re.match(r"^\d{4}-(0[1-9]|1[0-2])$", month):
        month_valid = True
    else:
        st.error("❌ 자료 기준월은 yyyy-mm 형식으로 입력해 주세요. 예: 2025-04")

# 3. 입력 완료 후 업로드 활성화
if submit and name and month_valid:
    st.success("✅ 입력 완료! 아래에서 엑셀 파일을 업로드해 주세요.")
    uploaded = st.file_uploader("엑셀 파일 업로드", type=["xls", "xlsx"])

    if uploaded:
        try:
            # 0행 + 1행을 병합헤더로 처리
            df_raw = pd.read_excel(uploaded, header=None)
            merged_header = []
            for i in range(len(df_raw.columns)):
                top = str(df_raw.iloc[0, i]).strip() if pd.notna(df_raw.iloc[0, i]) else ""
                bottom = str(df_raw.iloc[1, i]).strip() if pd.notna(df_raw.iloc[1, i]) else ""
                merged_header.append(bottom if bottom else top)
            df = df_raw.iloc[2:].copy()
            df.columns = merged_header

            # 마지막 합계 행 제외
            df = df.iloc[:-1]

            # 학자금수당까지만 추출
            if "학자금수당" in df.columns:
                last_col = df.columns.get_loc("학자금수당") + 1
                df = df.iloc[:, :last_col]

            # 엑셀로 출력
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="정리본")
                sheet = writer.sheets["정리본"]
                for col in sheet.columns:
                    max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                    sheet.column_dimensions[col[0].column_letter].width = max_len + 3
            output.seek(0)

            st.dataframe(df)

            st.download_button(
                label="📥 정리된 리포트 다운로드",
                data=output,
                file_name=f"{name}_{month}_정리본.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"⚠️ 처리 중 오류 발생: {e}")
else:
    st.info("고객명과 기준월을 먼저 정확히 입력해 주세요.")
