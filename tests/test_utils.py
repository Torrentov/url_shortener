from app.utils import generate_short_code


def test_generate_short_code_length():
    code = generate_short_code(length=6)
    assert len(code) == 6
    assert code.isalnum()

def test_generate_short_code_uniqueness():
    codes = {generate_short_code() for _ in range(1000)}
    assert len(codes) == 1000
