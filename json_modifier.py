import json
import streamlit as st
import zipfile
import io
import re

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
5. content에 스크린샷(screenshot)이 포함된 경우 "<<screenshot: undefined>>" 항목을 제거한다.
6. 밑줄, 볼드체, 이텔릭체 적용 태그를 제거한다. [ex. <u>, </u>, <em>, </em>, ** ]
7. 문장 맨 끝에 " [숫자]" 또는 " [숫자]." 는 제거한다.
- before: "파이썬 인덱싱은 [1], [2]와 같이 표기한다. [132]"
- after: "파이썬 인덱싱은 [1], [2]와 같이 표기한다."
8. 문장 끝이 " ." 이렇게 띄어쓰기 + 마침표의 경우 "."로 수정한다.
9. 문장 끝이 마침표로 끝나지 않을 경우 마침표를 붙인다.

실행
1. 다운받은 json 파일을 업로드 합니다.
2. 처리가 완료되면 modified_jsons.zip 압축파일로 다운로드 받습니다.
3. 해당 파일의 압축을 열어 수정완료된 json 파일을 확인합니다.
4. 재업로드 시 페이지를 새로고침 한 뒤 진행해 주세요.
"""

st.title("JSON Modifier")

uploaded_files = st.file_uploader("JSON 파일 업로드 (여러 개 가능)", type="json", accept_multiple_files=True)

if uploaded_files:
    processed_files = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        data = json.load(uploaded_file)

        # level 1, 2 존재여부 체크
        has_level_1 = False
        has_level_2 = False

        for section in data:
            level = section.get("level")
            if level == 1:
                has_level_1 = True
            elif level == 2:
                has_level_2 = True

        curr_start_time = 0
        new_data = []

        for section in data:
            # 빈 content 필터링
            if section.get("content") == [""]:
                continue

            level = section.get("level")

            if (has_level_1 and not has_level_2) or level == 2:
                start_time = section.get("startTime")
                if start_time == -1:
                    section["startTime"] = 0
                curr_start_time = section["startTime"]

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

            elif (has_level_1 and has_level_2) and level == 1:
                start_time = section.get("startTime")
                if start_time == -1:
                    section["startTime"] = curr_start_time
                content = section.get("content")
                new_content = []
                for string in content:
                    if string == "":  # 빈 문자열 pass
                        continue

                    string = re.sub(r"</?(u|em)>", "", string)  # Remove <u>, </u>, <em>, </em>
                    string = string.replace("**", "")  # Remove **
                    # 문장 끝의 " [숫자]" 또는 " [숫자]." 패턴만 제거
                    idx = string.rfind(" [")
                    if idx != -1:
                        end_bracket = string.find("]", idx)
                        if end_bracket != -1 and (
                            end_bracket == len(string) - 1 or (end_bracket == len(string) - 2 and string[end_bracket + 1] == ".")
                        ):
                            string = string[:idx].rstrip(". ") + "."

                    string = string.strip()
                    if string[-2:] == " .":  # 문장 끝이 " ."로 끝날 경우
                        string = string[:-2] + "."
                    if string[-1] != ".":  # 마침표가 없을 경우
                        string = string + "."
                    new_content.append(string)

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
