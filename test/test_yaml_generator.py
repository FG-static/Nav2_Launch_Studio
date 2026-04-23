"""YAML 生成器测试。"""


def test_generator_import():
    """测试 YamlGenerator 可正常导入。"""
    from nav2_launch_studio.core.yaml_generator import YamlGenerator
    gen = YamlGenerator()
    assert gen is not None


def test_generator_produces_string():
    """测试 generate() 返回字符串。"""
    from nav2_launch_studio.core.yaml_generator import YamlGenerator
    gen = YamlGenerator()
    result = gen.generate(None)
    assert isinstance(result, str)
