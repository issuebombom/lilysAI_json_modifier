import json
import streamlit as st
import zipfile
import io
import re

st.title("JSON Modifier")
st.markdown("#### 릴리즈 AI를 통해 확보한 json의 버그를 수정합니다.")

uploaded_files = st.file_uploader("JSON 파일 업로드 (여러 개 가능)", type="json", accept_multiple_files=True)

if uploaded_files:
    processed_files = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        data = json.load(uploaded_file)

        new_data = []

        for section in data:
            level = section.get("level")
            title = section.get("title")
            # 빈 content 필터링
            if section.get("content") == [""]:
                continue

            start_time = section.get("startTime")
            if start_time == -1:
                section["startTime"] = 0

            if (start_time == None) and (level == 1):
                section["startTime"] = 0

            if (start_time == None) and (level != 1):
                input_key = f"{file_name}_{data.index(section)}_startTime"
                existing_value = st.session_state.get(input_key)

                if existing_value is None:
                    st.warning(f"⚠️ startTime이 null인 항목이 있습니다. 값을 입력해주세요.")
                    section["startTime"] = st.number_input(f"변경 위치: {file_name} | '{title}' 의 startTime", min_value=0, key=input_key)
                    st.stop()
                else:
                    section["startTime"] = existing_value

            # content 개행 분할 및 첫 항목의 "- " 제거
            content = section.get("content")
            if isinstance(content, list) and content:
                new_content = []
                for string in content:
                    if ("screenshot" in string) or string == "":  # 스크린샷 or 빈 문자열 pass
                        continue

                    split_content = string.split("\n- ")
                    cleaned = []
                    for s in split_content:
                        s = s.lstrip("- ").strip()
                        s = re.sub(r"</?(u|em)>", "", s)  # Remove <u>, </u>, <em>, </em>
                        s = s.replace("**", "")  # Remove **
                        # 문장 끝의 " [숫자]" 또는 " [숫자]." 패턴만 제거
                        idx = s.rfind(" [")
                        if idx != -1:
                            end_bracket = s.find("]", idx)
                            if end_bracket != -1 and (
                                end_bracket == len(s) - 1 or (end_bracket == len(s) - 2 and s[end_bracket + 1] == ".")
                            ):
                                s = s[:idx].rstrip(". ") + "."

                        s = s.strip()
                        if s[-2:] == " .":  # 문장 끝이 " ."로 끝날 경우
                            s = s[:-2] + "."
                        if s[-1] != ".":  # 마침표가 없을 경우
                            s = s + "."

                        cleaned.append(s)
                    new_content.extend(cleaned)

                section["content"] = new_content

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


st.markdown("")  # 공란

"""
> 실행
1. 릴리즈 AI에서 다운받은 json 파일을 업로드 합니다.
2. 처리가 완료되면 modified_jsons.zip 압축파일로 다운로드 받습니다.
3. 해당 파일의 압축을 열어 수정완료된 json 파일을 확인합니다.
4. 재업로드 시 페이지를 새로고침 한 뒤 진행해 주세요.

---
"""
st.markdown("")  # 공란
"""

> `new` 수정 적용 사항  

(2025. 07. 25)
- 최상단에 위치한 **전체 요약** 영역의 startTime 값을 null에서 0으로 수정 적용함
    - 요약내용의 최상단에 위치한 **전체 요약** 영역(이 강의는...으로 시작하는 영역)의 startTime이 null값으로 설정되도록 릴리즈 AI 측에서 업데이트 됨 
    - startTime의 null값은 백오피스 상에 업로드 에러를 발생시킴
- 그 외 내용에서 startTime이 간혹 null값일 경우 이를 직접 수정하는 로직 추가
"""
st.markdown("")  # 공란
"""
> History
1. 첫 제목의 startTime이 -1로 찍히는 것을 0으로 변경한다.
2. 대제목의 내용(content)를 아래와 같이 수정한다.
- before: ["- 파이썬에 대해서 설명한다. \\n- 파이썬의 장점을 얘기한다. \\n- ..."]
- after: ["파이썬에 대해서 설명한다.", "파이썬의 장점을 얘기한다."]
3. 내용이 없는 경우는 삭제한다. (content: [""])
4. content에 스크린샷(screenshot)이 포함된 경우 "<<screenshot: undefined>>" 항목을 제거한다.
5. 밑줄, 볼드체, 이텔릭체 적용 태그를 제거한다. [ex. <u>, </u>, <em>, </em>, ** ]
6. 문장 맨 끝에 " [숫자]" 또는 " [숫자]." 는 제거한다.
- before: "파이썬 인덱싱은 [1], [2]와 같이 표기한다. [132]"
- after: "파이썬 인덱싱은 [1], [2]와 같이 표기한다."
7. 문장 끝이 " ." 이렇게 띄어쓰기 + 마침표의 경우 "."로 수정한다.
8. 문장 끝이 마침표로 끝나지 않을 경우 마침표를 붙인다.

> 삭제된 기능  

`[removed]` 대제목의 하위 항목인 소제목의 startTime이 대제목의 startTime을 따르도록 수정한다.
"""
