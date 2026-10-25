
import requests


BASE_URL = "http://127.0.0.1:8001"

STATUS_URL = BASE_URL + "/dynamic/status"

TOOL_URL = (
    BASE_URL
    + "/dynamic/research-agent/pdf-tool"
)

EXECUTE_URL = BASE_URL + "/dynamic/execute-pdf"

RDF_URL = (
    BASE_URL
    + "/dynamic/ontology/tool-bindings"
)


def request(method, url):
    """向 FastAPI 发送 HTTP 请求"""

    response = requests.request(
        method,
        url,
        timeout=30
    )

    return response


def status():
    response = request("GET", STATUS_URL)
    response.raise_for_status()
    return response.json()


def assert_http(response, expected):
    assert response.status_code == expected, (
        f"预期 HTTP {expected}，"
        f"实际 {response.status_code}: "
        f"{response.text}"
    )


def check_state(has_pdf, team_size):
    """验证 Agent 能力和推荐结果"""

    data = status()

    research = data["agents"]["ResearchAgent"]

    capabilities = research["capabilities"]
    tools = research["registered_tools"]

    team = data["recommendations"]["ResearchTask"]

    assert ("read_pdf" in capabilities) == has_pdf

    assert (
        "PDFReaderTool" in tools
    ) == has_pdf

    assert len(team) == team_size

    assert data["consistency"] is True

    print("Agent 能力: PASS")
    print("推荐团队:", team)
    print("推荐一致性: PASS")

    return data


def check_rdf(expected_tool):
    """直接检查 RDF 工具来源"""

    response = request("GET", RDF_URL)

    assert_http(response, 200)

    data = response.json()

    bindings = data["bindings"]

    research_bindings = [
        item
        for item in bindings
        if item["agent"] == "ResearchAgent"
        and item["tool"] == "PDFReaderTool"
        and item["capability"] == "read_pdf"
    ]

    if expected_tool:
        assert len(research_bindings) == 1
    else:
        assert len(research_bindings) == 0

    assert data["provenance_consistency"] is True
    assert data["recommendation_consistency"] is True

    print("RDF 来源一致性: PASS")


def main():

    print("\n===== OntoAgent-Evolve E2E =====")

    # Test 0: 将测试环境恢复为未注册状态
    print("\nTest 0：准备初始状态")

    initial = status()

    tools = initial[
        "agents"
    ]["ResearchAgent"]["registered_tools"]

    if "PDFReaderTool" in tools:
        response = request("DELETE", TOOL_URL)
        assert_http(response, 200)

    check_state(False, 3)
    check_rdf(False)

    try:
        # Test 1: 新增 PDF 工具
        print("\nTest 1：注册工具")

        response = request("POST", TOOL_URL)
        assert_http(response, 200)

        check_state(True, 2)
        check_rdf(True)

        # Test 2: 重复注册
        print("\nTest 2：重复注册")

        response = request("POST", TOOL_URL)
        assert_http(response, 409)

        check_state(True, 2)
        print("重复注册保护: PASS")

        # Test 3: 执行真实 PDF
        print("\nTest 3：执行 PDF")

        response = request("POST", EXECUTE_URL)
        assert_http(response, 200)

        print("真实 PDF 执行: PASS")

        # Test 4: 移除工具
        print("\nTest 4：移除工具")

        response = request("DELETE", TOOL_URL)
        assert_http(response, 200)

        check_state(False, 3)
        check_rdf(False)

        # Test 5: 重复删除
        print("\nTest 5：重复删除")

        response = request("DELETE", TOOL_URL)
        assert_http(response, 404)

        check_state(False, 3)

        print("重复删除保护: PASS")

        # Test 6: 再次注册
        print("\nTest 6：重新注册")

        response = request("POST", TOOL_URL)
        assert_http(response, 200)

        check_state(True, 2)
        check_rdf(True)

        print("\n==========================")
        print("全部 E2E 测试: PASS")
        print("==========================")

    finally:
        # 无论测试是否成功，尽量恢复初始状态
        print("\n清理测试状态...")

        try:
            current = status()
            tools = current["agents"][
                "ResearchAgent"
            ]["registered_tools"]

            if "PDFReaderTool" in tools:
                response = request(
                    "DELETE", TOOL_URL
                )

                if response.status_code != 200:
                    print(
                        "清理失败:",
                        response.status_code,
                        response.text
                    )
                else:
                    print("测试状态已恢复")
            else:
                print("无需清理")

        except requests.RequestException as error:
            print("无法清理:", error)


if __name__ == "__main__":
    main()
