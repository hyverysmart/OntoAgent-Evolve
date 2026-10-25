
from services.writer_client import generate_report

# 一段我们自己编写的测试文本
text = """
Title: Test Research Paper

Abstract:
This paper investigates how dynamic ontologies
improve multi-agent recommendation systems.

We propose an incremental recommendation algorithm
that updates affected tasks when an agent gains
or loses a capability.

Experiments show that incremental updates reduce
recomputation time compared with full recomputation.

A limitation is that the experiments only use
small simulated datasets.
"""

print("开始测试 WriterAgent...")

report = generate_report(
    paper_title="Test Research Paper",
    paper_text=text
)

print("\n=== Dify 生成的报告 ===")
print(report)

if "提供的文本中未说明" in report:
    print("\n提示：请检查报告是否遗漏了测试文本中明确给出的信息。")
