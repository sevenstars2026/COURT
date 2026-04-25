"""
契约验证系统 - 确保判决执行符合承诺
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
import ast
import re
import subprocess
from pydantic import BaseModel, Field


class ContractType(str, Enum):
    """契约类型"""
    FUNCTION_EXISTS = "function_exists"          # 函数必须存在
    CLASS_EXISTS = "class_exists"                # 类必须存在
    IMPORT_EXISTS = "import_exists"              # 导入必须存在
    CODE_PATTERN = "code_pattern"                # 代码必须包含特定模式
    NO_PATTERN = "no_pattern"                    # 代码不能包含特定模式
    TEST_EXISTS = "test_exists"                  # 测试必须存在
    TEST_PASSES = "test_passes"                  # 测试必须通过
    FILE_EXISTS = "file_exists"                  # 文件必须存在
    CUSTOM_RULE = "custom_rule"                  # 自定义 Python 断言
    AST_CHECK = "ast_check"                      # AST 结构检查


class Contract(BaseModel):
    """契约条款"""
    contract_id: str = Field(default_factory=lambda: f"contract_{id(object())}")
    type: ContractType
    description: str
    target: str  # 目标文件/函数/类/模式
    params: Dict[str, Any] = Field(default_factory=dict)
    required: bool = True  # 是否必须满足
    severity: str = "error"  # error, warning


class ContractViolation(BaseModel):
    """契约违反记录"""
    contract_id: str
    description: str
    severity: str
    details: str


class ContractAuditor:
    """契约审计器 - 验证代码变更是否满足判决契约"""

    def __init__(self, project_root: Path):
        """
        初始化审计器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root

    def audit(self, contracts: List[Contract], changed_files: List[str]) -> tuple[bool, List[ContractViolation]]:
        """
        审计契约

        Args:
            contracts: 契约列表
            changed_files: 变更的文件列表

        Returns:
            (是否通过, 违反列表)
        """
        violations = []

        for contract in contracts:
            violation = self._check_contract(contract, changed_files)
            if violation:
                violations.append(violation)

        # 只有 error 级别的违反才算失败
        has_errors = any(v.severity == "error" for v in violations)
        return not has_errors, violations

    def _check_contract(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """
        检查单个契约

        Args:
            contract: 契约
            changed_files: 变更的文件列表

        Returns:
            违反记录，如果通过则返回 None
        """
        try:
            if contract.type == ContractType.FUNCTION_EXISTS:
                return self._check_function_exists(contract, changed_files)
            elif contract.type == ContractType.CLASS_EXISTS:
                return self._check_class_exists(contract, changed_files)
            elif contract.type == ContractType.IMPORT_EXISTS:
                return self._check_import_exists(contract, changed_files)
            elif contract.type == ContractType.CODE_PATTERN:
                return self._check_code_pattern(contract, changed_files)
            elif contract.type == ContractType.NO_PATTERN:
                return self._check_no_pattern(contract, changed_files)
            elif contract.type == ContractType.TEST_EXISTS:
                return self._check_test_exists(contract)
            elif contract.type == ContractType.TEST_PASSES:
                return self._check_test_passes(contract)
            elif contract.type == ContractType.FILE_EXISTS:
                return self._check_file_exists(contract)
            elif contract.type == ContractType.CUSTOM_RULE:
                return self._check_custom_rule(contract, changed_files)
            elif contract.type == ContractType.AST_CHECK:
                return self._check_ast(contract, changed_files)
            else:
                return ContractViolation(
                    contract_id=contract.contract_id,
                    description=f"未知的契约类型: {contract.type}",
                    severity="error",
                    details=""
                )
        except Exception as e:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=f"契约检查失败: {contract.description}",
                severity="error",
                details=str(e)
            )

    def _check_function_exists(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查函数是否存在"""
        target_file = contract.params.get("file", contract.target.split(":")[0] if ":" in contract.target else None)
        function_name = contract.target.split(":")[-1] if ":" in contract.target else contract.target

        if not target_file:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details="未指定目标文件"
            )

        file_path = self.project_root / target_file
        if not file_path.exists():
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"文件不存在: {target_file}"
            )

        # 解析 AST 查找函数
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                return ContractViolation(
                    contract_id=contract.contract_id,
                    description=contract.description,
                    severity=contract.severity,
                    details=f"语法错误: {e}"
                )

        # 查找函数定义
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # 检查参数（如果指定）
                if "params" in contract.params:
                    expected_params = contract.params["params"]
                    actual_params = [arg.arg for arg in node.args.args]
                    if expected_params != actual_params:
                        return ContractViolation(
                            contract_id=contract.contract_id,
                            description=contract.description,
                            severity=contract.severity,
                            details=f"参数不匹配: 期望 {expected_params}, 实际 {actual_params}"
                        )
                return None  # 找到了

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"函数 {function_name} 不存在于 {target_file}"
        )

    def _check_class_exists(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查类是否存在"""
        target_file = contract.params.get("file", contract.target.split(":")[0] if ":" in contract.target else None)
        class_name = contract.target.split(":")[-1] if ":" in contract.target else contract.target

        if not target_file:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details="未指定目标文件"
            )

        file_path = self.project_root / target_file
        if not file_path.exists():
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"文件不存在: {target_file}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                return ContractViolation(
                    contract_id=contract.contract_id,
                    description=contract.description,
                    severity=contract.severity,
                    details=f"语法错误: {e}"
                )

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return None

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"类 {class_name} 不存在于 {target_file}"
        )

    def _check_import_exists(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查导入是否存在"""
        target_file = contract.params.get("file")
        import_name = contract.target

        if not target_file:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details="未指定目标文件"
            )

        file_path = self.project_root / target_file
        if not file_path.exists():
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"文件不存在: {target_file}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 简单的正则匹配
        patterns = [
            rf"^import\s+{re.escape(import_name)}",
            rf"^from\s+\S+\s+import\s+.*{re.escape(import_name)}"
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                return None

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"导入 {import_name} 不存在于 {target_file}"
        )

    def _check_code_pattern(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查代码是否包含特定模式"""
        target_file = contract.params.get("file")
        pattern = contract.target

        if not target_file:
            # 检查所有变更的文件
            files_to_check = changed_files
        else:
            files_to_check = [target_file]

        for file in files_to_check:
            file_path = self.project_root / file
            if not file_path.exists():
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                return None  # 找到了

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"代码模式 '{pattern}' 未找到"
        )

    def _check_no_pattern(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查代码不包含特定模式（反向检查）"""
        target_file = contract.params.get("file")
        pattern = contract.target

        if not target_file:
            files_to_check = changed_files
        else:
            files_to_check = [target_file]

        violations = []
        for file in files_to_check:
            file_path = self.project_root / file
            if not file_path.exists():
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                violations.append(file)

        if violations:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"禁止的代码模式 '{pattern}' 出现在: {', '.join(violations)}"
            )

        return None

    def _check_test_exists(self, contract: Contract) -> Optional[ContractViolation]:
        """检查测试是否存在"""
        test_name = contract.target
        test_file = contract.params.get("file", f"tests/test_{test_name}.py")

        test_path = self.project_root / test_file
        if not test_path.exists():
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"测试文件不存在: {test_file}"
            )

        # 检查测试函数是否存在
        with open(test_path, "r", encoding="utf-8") as f:
            content = f.read()

        if f"def test_{test_name}" in content or f"def {test_name}" in content:
            return None

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"测试函数 test_{test_name} 不存在于 {test_file}"
        )

    def _check_test_passes(self, contract: Contract) -> Optional[ContractViolation]:
        """检查测试是否通过"""
        test_target = contract.target

        try:
            result = subprocess.run(
                f"pytest {test_target} -v",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_root
            )

            if result.returncode == 0:
                return None

            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"测试失败:\n{result.stdout}\n{result.stderr}"
            )
        except subprocess.TimeoutExpired:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details="测试超时"
            )
        except Exception as e:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"测试执行失败: {e}"
            )

    def _check_file_exists(self, contract: Contract) -> Optional[ContractViolation]:
        """检查文件是否存在"""
        file_path = self.project_root / contract.target

        if file_path.exists():
            return None

        return ContractViolation(
            contract_id=contract.contract_id,
            description=contract.description,
            severity=contract.severity,
            details=f"文件不存在: {contract.target}"
        )

    def _check_custom_rule(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """执行自定义 Python 规则"""
        rule_code = contract.target
        context = {
            "changed_files": changed_files,
            "project_root": self.project_root,
            **contract.params
        }

        try:
            # 安全执行自定义代码
            exec(rule_code, {"__builtins__": {}}, context)
            return None
        except AssertionError as e:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"自定义规则失败: {e}"
            )
        except Exception as e:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"自定义规则执行错误: {e}"
            )

    def _check_ast(self, contract: Contract, changed_files: List[str]) -> Optional[ContractViolation]:
        """检查 AST 结构"""
        target_file = contract.params.get("file")
        check_type = contract.params.get("check_type")

        if not target_file:
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details="未指定目标文件"
            )

        file_path = self.project_root / target_file
        if not file_path.exists():
            return ContractViolation(
                contract_id=contract.contract_id,
                description=contract.description,
                severity=contract.severity,
                details=f"文件不存在: {target_file}"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError as e:
                return ContractViolation(
                    contract_id=contract.contract_id,
                    description=contract.description,
                    severity=contract.severity,
                    details=f"语法错误: {e}"
                )

        # 根据 check_type 执行不同的 AST 检查
        if check_type == "no_eval":
            # 禁止使用 eval
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
                    return ContractViolation(
                        contract_id=contract.contract_id,
                        description=contract.description,
                        severity=contract.severity,
                        details="代码中使用了 eval()"
                    )

        elif check_type == "has_docstring":
            # 检查是否有文档字符串
            if not ast.get_docstring(tree):
                return ContractViolation(
                    contract_id=contract.contract_id,
                    description=contract.description,
                    severity=contract.severity,
                    details="缺少模块文档字符串"
                )

        return None


def generate_contracts_from_verdict(verdict_reasoning: str, execution_plan: List[str]) -> List[Contract]:
    """
    从判决理由和执行计划中生成契约

    Args:
        verdict_reasoning: 判决理由
        execution_plan: 执行计划

    Returns:
        契约列表
    """
    contracts = []

    # 解析执行计划，提取契约
    for plan_item in execution_plan:
        plan_lower = plan_item.lower()

        # 添加测试
        if "测试" in plan_lower or "test" in plan_lower:
            contracts.append(Contract(
                type=ContractType.TEST_EXISTS,
                description="必须添加测试",
                target="new_feature",
                severity="error"
            ))

        # 添加超时处理
        if "超时" in plan_lower or "timeout" in plan_lower:
            contracts.append(Contract(
                type=ContractType.CODE_PATTERN,
                description="必须包含超时处理",
                target=r"timeout\s*[=:]",
                severity="error"
            ))

        # 添加错误处理
        if "错误处理" in plan_lower or "exception" in plan_lower:
            contracts.append(Contract(
                type=ContractType.CODE_PATTERN,
                description="必须包含异常处理",
                target=r"(try|except|raise)",
                severity="error"
            ))

        # 禁止使用危险函数
        if "安全" in plan_lower or "security" in plan_lower:
            contracts.append(Contract(
                type=ContractType.NO_PATTERN,
                description="禁止使用 eval",
                target=r"\beval\s*\(",
                severity="error"
            ))

    return contracts
