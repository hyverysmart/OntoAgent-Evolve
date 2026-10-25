
import requests

BASE_URL = "http://127.0.0.1:8001"

STATUS = BASE_URL + "/dynamic/status"
PDF_TOOL = BASE_URL + "/dynamic/research-agent/pdf-tool"
EXECUTE = BASE_URL + "/dynamic/execute-pdf"


def get_status():
    response = requests.get(STATUS, timeout=15)
    response.raise_for_status()
    return response.json()


def check_state(expected_count, has_pdf):
    data = get_status()

    research = data["agents"]["ResearchAgent"]
    capabilities = research["capabilities"]
    tools = research["registered_tools"]

    team = data["recommendations"]["ResearchTask"]

    assert len(team) == expected_count
    assert ("read_pdf" in capabilities) == has_pdf
    assert ("PDFReaderTool" in tools) == has_pdf
    assert data["consistency"] is True

    print("RDF、工具与推荐缓存一致: PASS")


def main():
    print("=== 动态 Agent 可靠性测试 ===")

    # 先恢复初始状态，允许重复运行测试
    initial = get_status()

    if "PDFReaderTool" in initial[
        "agents"]["ResearchAgent"]["registered_tools"]:

        response = requests.delete(
            PDF_TOOL, timeout=15
        )
        assert response.status_code == 200

    check_state(3, False)

    # Test 1：正常注册
    print("\nTest 1：正常注册工具")

    response = requests.post(PDF_TOOL, timeout=30)
    assert response.status_code == 200, response.text

    check_state(2, True)

    # Test 2：重复注册
    print("\nTest 2：重复注册")

    response = requests.post(PDF_TOOL, timeout=30)

    assert response.status_code == 409
    check_state(2, True)

    print("重复注册保护: PASS")

    # Test 3：真实执行 PDF
    print("\nTest 3：执行 PDF")

    response = requests.post(EXECUTE, timeout=30)
    assert response.status_code == 200, response.text

    print("PDF 工具执行: PASS")

    # Test 4：正常移除
    print("\nTest 4：移除工具")

    response = requests.delete(PDF_TOOL, timeout=15)
    assert response.status_code == 200, response.text

    check_state(3, False)

    # Test 5：重复移除
    print("\nTest 5：重复移除")

    response = requests.delete(PDF_TOOL, timeout=15)

    assert response.status_code == 404
    check_state(3, False)

    print("重复移除保护: PASS")

    print("\n=== API 测试全部通过 ===")


if __name__ == "__main__":
    main()
