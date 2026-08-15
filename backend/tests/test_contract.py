"""契约漂移检测：把手工维护的 contracts/openapi.yaml 与 FastAPI 运行时
生成的 openapi.json 对齐，防止前后端分头开发时契约悄悄断裂。

对比内容：
1. (method, path) 集合双向相等 —— 后端增删接口、契约漏登记都会被抓住；
2. 每个接口的参数集合（name, in）一致，header 名大小写不敏感；
3. 请求体与 200 响应的 schema 形状一致：required 集合相等、属性名
   生成侧 ⊆ 契约侧（契约可以预先声明可选字段）、逐字段类型/枚举一致；
4. 生成侧声明的响应状态码必须是契约的子集（契约额外声明的 4xx/429
   属于客户端可见的错误码，允许后端 openapi.json 不重复声明）。
"""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts" / "openapi.yaml"

META_PATHS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
# FastAPI 对带 body 的接口自动声明 422，契约无需重复登记
IMPLICIT_CODES = {"422"}


def load_contract() -> dict:
    with CONTRACT_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def generated_spec() -> dict:
    # 不进入 lifespan：纯契约校验不需要创建本地数据库
    response = TestClient(create_app()).get("/openapi.json")
    assert response.status_code == 200, response.text
    return response.json()


def operations(spec: dict) -> dict[tuple[str, str], dict]:
    found: dict[tuple[str, str], dict] = {}
    for path, item in spec.get("paths", {}).items():
        if path in META_PATHS:
            continue
        for method, operation in item.items():
            if method in HTTP_METHODS:
                found[(method, path)] = operation
    return found


def resolve(spec: dict, node, seen: frozenset[str] | None = None):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if ref and len(node) == 1:
            if seen is None:
                seen = frozenset()
            if ref in seen:
                return node
            parts = ref.lstrip("#/").split("/")
            target = spec
            for part in parts:
                target = target[part]
            return resolve(spec, target, seen | {ref})
        return {key: resolve(spec, value, seen) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve(spec, value, seen) for value in node]
    return node


def unwrap(schema: dict) -> dict:
    """把 anyOf/oneOf 中「单一真实类型 + null」的可空字段还原为真实类型。

    契约是手工编写的、不标注 nullable；Pydantic 可选字段生成的 schema
    是 anyOf[T, null]。比较时忽略这层包装，避免每个可选字段都报类型漂移。
    """
    for key in ("anyOf", "oneOf"):
        members = schema.get(key)
        if isinstance(members, list):
            non_null = [
                member
                for member in members
                if not (isinstance(member, dict) and member.get("type") == "null")
            ]
            if len(non_null) == 1:
                return unwrap(non_null[0])
    return schema


def parameter_keys(spec: dict, operation: dict) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for param in operation.get("parameters", []):
        resolved = resolve(spec, param)
        name = str(resolved.get("name", ""))
        location = str(resolved.get("in", ""))
        if location == "header":
            name = name.lower()
        keys.add((location, name))
    return keys


def body_schema(spec: dict, operation: dict) -> dict | None:
    body = operation.get("requestBody")
    if not body:
        return None
    media = body.get("content", {}).get("application/json", {})
    schema = media.get("schema")
    if schema is None:
        return None
    return resolve(spec, schema)


def response_schema(spec: dict, operation: dict, code: str) -> dict | None:
    response = operation.get("responses", {}).get(code, {})
    media = response.get("content", {}).get("application/json", {})
    schema = media.get("schema")
    if schema is None:
        return None
    return resolve(spec, schema)


def type_name(schema: dict) -> str:
    if schema.get("type") == "array":
        return f"array[{type_name(schema.get('items') or {})}]"
    return str(schema.get("type") or "object")


def compare_schema(
    contract_schema: dict,
    generated_schema: dict,
    path: str,
    errors: list[str],
) -> None:
    contract_schema = unwrap(contract_schema)
    generated_schema = unwrap(generated_schema)
    contract_type = type_name(contract_schema)
    generated_type = type_name(generated_schema)
    if contract_type != generated_type:
        errors.append(f"{path}: 类型不一致 契约={contract_type} 实现={generated_type}")
        return
    if contract_type == "object" or generated_type == "object":
        contract_props = set((contract_schema.get("properties") or {}).keys())
        generated_props = set((generated_schema.get("properties") or {}).keys())
        extra = sorted(generated_props - contract_props)
        if extra:
            errors.append(f"{path}: 实现多出契约未声明的字段 {extra}")
        contract_required = sorted(contract_schema.get("required") or [])
        generated_required = sorted(generated_schema.get("required") or [])
        if contract_required != generated_required:
            errors.append(
                f"{path}: required 不一致 "
                f"契约={contract_required} 实现={generated_required}"
            )
        for key in sorted(generated_props & contract_props):
            compare_schema(
                contract_schema["properties"][key],
                generated_schema["properties"][key],
                f"{path}.{key}",
                errors,
            )
        return
    contract_enum = contract_schema.get("enum")
    generated_enum = generated_schema.get("enum")
    if contract_enum is not None and generated_enum is not None:
        if set(contract_enum) != set(generated_enum):
            errors.append(
                f"{path}: 枚举不一致 契约={sorted(contract_enum)} "
                f"实现={sorted(generated_enum)}"
            )


def test_contract_matches_generated_spec() -> None:
    contract = load_contract()
    generated = generated_spec()

    contract_ops = operations(contract)
    generated_ops = operations(generated)

    errors: list[str] = []

    only_contract = sorted(contract_ops.keys() - generated_ops.keys())
    only_generated = sorted(generated_ops.keys() - contract_ops.keys())
    if only_contract:
        errors.append(f"契约声明但后端缺失的接口 {only_contract}")
    if only_generated:
        errors.append(f"后端存在但契约未登记的接口 {only_generated}")

    for key in sorted(contract_ops.keys() & generated_ops.keys()):
        method, path = key
        label = f"{method.upper()} {path}"
        contract_op = contract_ops[key]
        generated_op = generated_ops[key]

        contract_params = parameter_keys(contract, contract_op)
        generated_params = parameter_keys(generated, generated_op)
        if contract_params != generated_params:
            errors.append(
                f"{label}: 参数不一致 契约={sorted(contract_params)} "
                f"实现={sorted(generated_params)}"
            )

        contract_body = body_schema(contract, contract_op)
        generated_body = body_schema(generated, generated_op)
        if (contract_body is None) != (generated_body is None):
            errors.append(f"{label}: 请求体存在性不一致")
        elif contract_body is not None and generated_body is not None:
            compare_schema(contract_body, generated_body, f"{label} 请求体", errors)

        generated_codes = set(generated_op.get("responses", {}).keys())
        undeclared = sorted(generated_codes - IMPLICIT_CODES - set(contract_op.get("responses", {}).keys()))
        if undeclared:
            errors.append(f"{label}: 实现声明了契约没有的响应码 {undeclared}")

        for code in sorted(generated_codes & set(contract_op.get("responses", {}).keys())):
            contract_resp = response_schema(contract, contract_op, code)
            generated_resp = response_schema(generated, generated_op, code)
            if (contract_resp is None) != (generated_resp is None):
                errors.append(f"{label} {code}: 响应体存在性不一致")
            elif contract_resp is not None and generated_resp is not None:
                compare_schema(contract_resp, generated_resp, f"{label} {code}", errors)

    assert not errors, (
        f"契约与实现漂移 {len(errors)} 处。"
        f"修改后端接口时同步更新 contracts/openapi.yaml：\n- "
        + "\n- ".join(errors)
    )
