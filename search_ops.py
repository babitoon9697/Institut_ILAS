import json

with open(r'C:\Users\INSTITUT ILAS\.gemini\antigravity\brain\1d599951-6aee-436a-8103-40348bcad81f\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index', 0)
        if 400 <= idx <= 420:
            tool_calls = obj.get('tool_calls')
            content = obj.get('content')
            typ = obj.get('type')
            print(f"Step {idx} ({typ}):")
            if tool_calls:
                print("  Tool:", tool_calls[0]['name'])
                print("  Args:", str(tool_calls[0].get('args'))[:300].encode('ascii', 'replace').decode('ascii'))
            if content:
                print("  Cont:", str(content)[:300].encode('ascii', 'replace').decode('ascii'))
