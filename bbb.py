import streamlit as st
import pandas as pd
from io import BytesIO
import csv

st.set_page_config(page_title="Multi-Column Extractor", layout="centered")
st.title("📄 Extract Multiple Columns from Excel or CSV Files")

st.write("""
Upload multiple Excel or CSV files.  
From each file, select **one or more columns**, and extract all their data.  
All selected columns will be combined side by side into a single Excel sheet.
""")

uploaded_files = st.file_uploader(
    "📁 Upload Excel or CSV files",
    type=["xlsx", "csv"],
    accept_multiple_files=True
)

column_mapping = {}

def detect_csv_info(file):
    """Detect encoding and delimiter of a CSV file"""
    content = file.read()
    for encoding in ['utf-8', 'latin-1']:
        try:
            decoded = content.decode(encoding)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(decoded.splitlines()[0])
            file.seek(0)
            return encoding, dialect.delimiter
        except Exception:
            continue
    file.seek(0)
    return None, None

if uploaded_files:
    st.write("## 🔧 Select Columns from Each File")

    for file in uploaded_files:
        filename = file.name
        file_type = filename.split('.')[-1].lower()

        try:
            if file_type == "xlsx":
                with pd.ExcelFile(file) as xls:
                    sheet_names = xls.sheet_names

                selected_sheet = st.selectbox(
                    f"🗂 Sheet for `{filename}`",
                    sheet_names,
                    key=f"{filename}_sheet"
                )

                df_header = pd.read_excel(file, sheet_name=selected_sheet, nrows=0)

            elif file_type == "csv":
                selected_sheet = None
                encoding, delimiter = detect_csv_info(file)

                if encoding is None or delimiter is None:
                    st.error(f"❗ Could not read header from `{filename}`.")
                    continue

                df_header = pd.read_csv(file, encoding=encoding, sep=delimiter, nrows=0)

            # Clean column names
            cleaned_columns = df_header.columns.str.strip().str.replace('\u200b', '', regex=True).str.replace('\xa0', ' ', regex=True)

            selected_columns = st.multiselect(
                f"📌 Columns to extract from `{filename}`",
                cleaned_columns,
                key=f"{filename}_cols"
            )

            # Save metadata
            file.seek(0)
            column_mapping[filename] = {
                "file": file,
                "sheet": selected_sheet,
                "columns": selected_columns,
                "file_type": file_type,
                "encoding": encoding if file_type == "csv" else None,
                "delimiter": delimiter if file_type == "csv" else None
            }

        except Exception as e:
            st.error(f"⚠️ Error reading `{filename}`: {e}")

# Extract and combine
if st.button("📤 Create Combined Excel"):
    extracted_columns = []

    for filename, info in column_mapping.items():
        try:
            file = info["file"]
            file.seek(0)
            cols = info["columns"]

            if not cols:
                continue  # Skip if no columns selected

            if info["file_type"] == "xlsx":
                df = pd.read_excel(file, sheet_name=info["sheet"])
            elif info["file_type"] == "csv":
                df = pd.read_csv(file, encoding=info["encoding"], sep=info["delimiter"])

            df.columns = df.columns.str.strip().str.replace('\u200b', '', regex=True).str.replace('\xa0', ' ', regex=True)

            # Extract and clean selected columns
            for col in cols:
                if col in df.columns:
                    series = df[col].dropna().reset_index(drop=True)
                    series.name = col
                    extracted_columns.append(series)
                else:
                    st.warning(f"⚠️ Column `{col}` not found in `{filename}`")

        except Exception as e:
            st.error(f"❗ Error processing `{filename}`: {e}")

    if extracted_columns:
        combined_df = pd.concat(extracted_columns, axis=1)
        output = BytesIO()
        combined_df.to_excel(output, index=False)
        output.seek(0)

        st.success("✅ Combined Excel file is ready!")
        st.download_button(
            label="📥 Download Combined Excel",
            data=output,
            file_name="combined_columns.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ No columns selected or no data to export.")
