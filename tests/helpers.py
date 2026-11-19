TEMPLATE = """id: {tid}
title_ja: サンプル{suffix}
title_en: Sample {suffix}
portal:
  name_ja: x
  url: https://example.go.jp/
  operator: x
category: lookup
difficulty: easy
instructions_ja: 検索する
instructions_en: Search.
inputs: {{}}
success:
  type: field_match
  fields: [name]
safety:
  stop_before_submit: false
gold_source: example
"""


def valid_task_yaml(tid, title_suffix=None, extra=""):
    suffix = title_suffix or tid
    return TEMPLATE.format(tid=tid, suffix=suffix) + extra
