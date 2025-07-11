import json
import os
import streamlit as st
import zipfile
import io

"""
구현 기능 요약
- 릴리즈 AI를 통해 확보한 json의 버그를 수정합니다.

수정 적용 사항
1. 첫 제목의 startTime이 -1로 찍히는 것을 0으로 변경한다.
2. 대제목의 내용(content)를 아래와 같이 수정한다.
- before: ["- 파이썬에 대해서 설명한다. \\n- 파이썬의 장점을 얘기한다. \\n- ..."]
- after: ["파이썬에 대해서 설명한다.", "파이썬의 장점을 얘기한다."]
3. 대제목의 하위 항목인 소제목의 startTime이 대제목의 startTime을 따르도록 수정한다.
4. 내용이 없는 경우는 삭제한다. (content: [""])

실행
1. 다운받은 json 파일을 업로드 합니다.
2. 처리가 완료되면 modified_jsons.zip 압축파일로 다운로드 받습니다.
3. 해당 파일의 압축을 열어 수정완료된 json 파일을 확인합니다.
"""

st.title("JSON Modifier")

uploaded_files = st.file_uploader("JSON 파일 업로드 (여러 개 가능)", type="json", accept_multiple_files=True)

if uploaded_files:
    processed_files = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        data = json.load(uploaded_file)

        curr_start_time = 0
        new_data = []

        for section in data:
            # 빈 content 필터링
            if section.get("content") == [""]:
                continue

            level = section.get("level")

            if level == 2:
                start_time = section.get("startTime")
                if start_time == -1:
                    section["startTime"] = 0
                curr_start_time = section["startTime"]

                # content 개행 분할 및 첫 항목의 "- " 제거
                content = section.get("content")
                if isinstance(content, list) and isinstance(content[0], str):
                    split_content = content[0].split("\n- ")
                    split_content = [s.lstrip("- ").strip() for s in split_content]
                    section["content"] = split_content

            elif level == 1:
                section["startTime"] = curr_start_time

            new_data.append(section)

        # 메모리 버퍼에 저장
        json_buffer = io.StringIO()
        json.dump(new_data, json_buffer, ensure_ascii=False, indent=2)
        json_bytes = json_buffer.getvalue().encode("utf-8")

        processed_files.append((file_name, json_bytes))

    # ZIP 파일 생성
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for name, content in processed_files:
            zip_file.writestr(name, content)

    zip_buffer.seek(0)
    st.download_button(label="📦 수정된 JSON 압축 파일 다운로드", data=zip_buffer, file_name="modified_jsons.zip", mime="application/zip")
