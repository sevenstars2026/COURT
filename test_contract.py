"""
测试契约验证系统
"""
from pathlib import Path
from courtroom.contract import (
    ContractAuditor, Contract, ContractType,
    generate_contracts_from_verdict
)


def test_contract_system():
    """测试契约验证系统"""
    print("🧪 测试契约验证系统\n")

    project_root = Path("/home/sevenstars/CLionProjects/Oasis")
    auditor = ContractAuditor(project_root)

    # 测试 1: 函数存在性检查
    print("1️⃣ 测试函数存在性检查")
    contract1 = Contract(
        type=ContractType.FUNCTION_EXISTS,
        description="必须存在 get_player_state 函数",
        target="backend/services/map_service.py:get_player_state",
        params={"file": "backend/services/map_service.py"}
    )

    passed, violations = auditor.audit([contract1], ["backend/services/map_service.py"])
    if passed:
        print("   ✅ 通过：函数存在\n")
    else:
        print(f"   ❌ 失败：{violations[0].details}\n")

    # 测试 2: 代码模式检查
    print("2️⃣ 测试代码模式检查")
    contract2 = Contract(
        type=ContractType.CODE_PATTERN,
        description="必须包含错误处理",
        target=r"(try|except|raise)",
        params={"file": "backend/services/map_service.py"}
    )

    passed, violations = auditor.audit([contract2], ["backend/services/map_service.py"])
    if passed:
        print("   ✅ 通过：包含错误处理\n")
    else:
        print(f"   ❌ 失败：{violations[0].details}\n")

    # 测试 3: 禁止模式检查
    print("3️⃣ 测试禁止模式检查")
    contract3 = Contract(
        type=ContractType.NO_PATTERN,
        description="禁止使用 eval",
        target=r"\beval\s*\(",
        params={"file": "backend/services/map_service.py"}
    )

    passed, violations = auditor.audit([contract3], ["backend/services/map_service.py"])
    if passed:
        print("   ✅ 通过：未使用 eval\n")
    else:
        print(f"   ❌ 失败：{violations[0].details}\n")

    # 测试 4: 文件存在性检查
    print("4️⃣ 测试文件存在性检查")
    contract4 = Contract(
        type=ContractType.FILE_EXISTS,
        description="必须存在配置文件",
        target="backend/config.py"
    )

    passed, violations = auditor.audit([contract4], [])
    if passed:
        print("   ✅ 通过：文件存在\n")
    else:
        print(f"   ❌ 失败：{violations[0].details}\n")

    # 测试 5: 从判决生成契约
    print("5️⃣ 测试从判决生成契约")
    execution_plan = [
        "添加超时处理到网络请求",
        "编写单元测试",
        "添加错误处理",
        "确保代码安全，禁止使用 eval"
    ]

    contracts = generate_contracts_from_verdict("批准该动议", execution_plan)
    print(f"   生成了 {len(contracts)} 个契约：")
    for c in contracts:
        print(f"   - {c.description}")
    print()

    # 测试 6: 综合审计
    print("6️⃣ 测试综合审计")
    all_contracts = [contract1, contract2, contract3, contract4]
    passed, violations = auditor.audit(all_contracts, ["backend/services/map_service.py"])

    print(f"   审计结果: {'✅ 通过' if passed else '❌ 失败'}")
    print(f"   检查了 {len(all_contracts)} 个契约")
    print(f"   发现 {len(violations)} 个违反")

    if violations:
        print("\n   违反详情:")
        for v in violations:
            print(f"   - [{v.severity}] {v.description}")
            print(f"     {v.details}")

    print("\n✅ 契约系统测试完成！")


if __name__ == "__main__":
    test_contract_system()
