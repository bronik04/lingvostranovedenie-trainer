import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

const ROOT = new URL('..', import.meta.url);
const HTML = new URL('dist/lingvostranovedenie-trainer.html', ROOT);

function build() {
  execFileSync('python3', ['scripts/build_html.py'], { cwd: ROOT });
  return readFileSync(HTML, 'utf8');
}

test('сборка выпускает один файл без внешних ссылок', () => {
  const html = build();
  assert.ok(statSync(HTML).size > 100_000);
  assert.equal(/<script[^>]+src=/.test(html), false, 'внешний скрипт');
  assert.equal(/<link[^>]+href="https?:/.test(html), false, 'внешний стиль');
  assert.ok(html.includes('const QUESTION_BANK = ['), 'банк не встроен');
  assert.equal(html.includes('/*QUIZ_UI*/'), false, 'обвязка не подставлена');
  assert.equal(html.includes('/*QUIZ_CSS*/'), false, 'стили не подставлены');
});

test('в собранном файле вопросы по-русски, а варианты по-китайски', () => {
  const html = build();
  const bank = JSON.parse(html.match(/const QUESTION_BANK = (\[.*?\]);\n/s)[1]);
  assert.ok(bank.length > 400);
  for (const record of bank) {
    assert.match(record.questionRu, /[А-Яа-яЁё]/, record.id);
    for (const option of record.options) {
      assert.doesNotMatch(option.zh, /[А-Яа-яЁё]/, `${record.id}: ${option.zh}`);
    }
  }
});

test('минификация не ломает синтаксис встроенных скриптов', () => {
  const html = build();
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  assert.equal(scripts.length, 2, 'ожидались два встроенных <script>');
  const dir = mkdtempSync(join(tmpdir(), 'lingvo-syntax-'));
  try {
    scripts.forEach((code, index) => {
      const file = join(dir, `script-${index}.js`);
      writeFileSync(file, code);
      assert.doesNotThrow(() => execFileSync('node', ['--check', file]),
        `скрипт №${index} не проходит проверку синтаксиса`);
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('сборка падает на банке, нарушающем инварианты', () => {
  assert.throws(() => execFileSync('python3', ['-c', `
import json, sys
sys.path.insert(0, 'scripts')
from build_html import validate
broken = json.loads(open('data/bank.json').read())[:1]
broken[0]['questionRu'] = '中国最大的港口城市是哪一个？'
errors = validate(broken)
sys.exit(1 if errors else 0)
`], { cwd: ROOT }));
});
