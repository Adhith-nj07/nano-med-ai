import hashlib

with open('src/simulation/mechanisms.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'hash(f"{env_state.pH}_{env_state.temperature_c}_{env_state.buffer}")',
    'hashlib.sha256(f"{env_state.pH}_{env_state.temperature_c}_{env_state.buffer}".encode()).hexdigest()'
)

if 'import hashlib' not in code:
    code = 'import hashlib\n' + code

with open('src/simulation/mechanisms.py', 'w', encoding='utf-8') as f:
    f.write(code)
