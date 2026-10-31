/* Личные замечания к вопросам. Запускается после quiz.ui.js и chengyu.ui.js;
 * читает их состояние, но не меняет ни раунд, ни учебный прогресс. */
(() => {
  const KEY = 'lingvo-trainer:review:v1';
  const MODE_KEY = 'lingvo-trainer:review-mode:v1';
  const dialog = $('reviewDialog');
  const formats = { choice: 'Выбор ответа', recall: 'Вспомни сам', truefalse: 'Верно или нет', chengyu: 'Чэнъюй' };
  let entries = [];
  let enabled = false;
  let storageBlocked = false;
  let warning = '';
  let editing = null;
  const keyOf = (entry) => `${entry.section}:${entry.questionId}`;
  const titleOf = (entry) => entry.snapshot.questionRu
    || [entry.snapshot.prompt, entry.snapshot.chengyu].filter(Boolean).join(' — ') || entry.questionId;

  function storageProblem(corrupt = false) {
    storageBlocked = true;
    warning = corrupt
      ? 'Сохранённый список не удалось прочитать. Он не перезаписан. Новые замечания временные — выгрузите их до закрытия страницы.'
      : 'Браузер не сохраняет замечания. Они доступны только до закрытия страницы — выгрузите их сейчас.';
  }

  function readEntries() {
    let raw;
    try { raw = localStorage.getItem(KEY); } catch { storageProblem(); return null; }
    if (raw === null) return [];
    try {
      const saved = JSON.parse(raw);
      if (saved.version !== 1 || !Array.isArray(saved.entries)
          || !saved.entries.every((entry) => entry && ['quiz', 'chengyu'].includes(entry.section)
            && typeof entry.questionId === 'string' && typeof entry.comment === 'string'
            && typeof entry.createdAt === 'string' && typeof entry.updatedAt === 'string'
            && entry.snapshot && typeof entry.snapshot === 'object'
            && entry.context && Array.isArray(entry.context.shownOptions)
            && entry.context.shownOptions.every((option) => option && typeof option.text === 'string'))
          || new Set(saved.entries.map(keyOf)).size !== saved.entries.length) throw new Error('format');
      return saved.entries;
    } catch { storageProblem(true); return null; }
  }

// Перед изменением читаем свежий список: открытая рядом вкладка могла добавить отметку.
  function updateEntries(change) {
    if (!storageBlocked) entries = readEntries() ?? entries;
    change();
    if (!storageBlocked) {
      try { localStorage.setItem(KEY, JSON.stringify({ version: 1, entries })); }
      catch { storageProblem(); }
    }
    renderControls();
  }

  function current(section) {
    return section === 'chengyu' ? cy.round[cy.position] : state.round[state.position];
  }

  function renderControls() {
    document.documentElement.dataset.review = enabled ? 'on' : 'off';
    $('reviewBar').hidden = !enabled;
    $('reviewToggle').textContent = enabled ? 'Отладка: вкл' : 'Отладка: выкл';
    $('reviewState').textContent = enabled ? 'вкл' : 'выкл';
    for (const id of ['reviewToggle', 'reviewMenu']) $(id).setAttribute('aria-pressed', String(enabled));
    $('reviewCount').textContent = entries.length;
    for (const [section, id] of [['quiz', 'reviewFlag'], ['chengyu', 'cyReviewFlag']]) {
      const marked = entries.some((entry) => entry.section === section && entry.questionId === current(section)?.id);
      $(id).textContent = marked ? '✓ Отмечен' : 'Отметить вопрос';
      $(id).dataset.marked = String(marked);
    }
    for (const id of ['reviewStorageWarning', 'reviewDialogWarning']) {
      $(id).textContent = warning;
      $(id).hidden = !warning;
    }
    $('reviewSaveState').textContent = storageBlocked
      ? 'Комментарий временный — выгрузите замечания до закрытия страницы.'
      : 'Отметка и комментарий сохраняются автоматически.';
    for (const id of ['reviewExport', 'reviewCopy', 'reviewShare']) $(id).disabled = !entries.length;
  }

  function toggleMode() {
    enabled = !enabled;
    try { localStorage.setItem(MODE_KEY, enabled ? 'on' : 'off'); } catch { /* отметки проверяются отдельно */ }
    setViewMenu(false);
    renderControls();
  }

  function capture(section, record) {
    const isCy = section === 'chengyu';
    const options = $(isCy ? 'cyOptions' : 'options');
// Берём id и порядок из кнопок, текст — из записи: пиньинь/подписи/✓ в DOM не варианты.
    const shownOptions = [...options.querySelectorAll('button')].map((button) => {
      const option = record.options.find((item) => item.id === button.dataset.optionId);
      return { optionId: option.id, text: option.zh ?? option.text };
    });
    const context = {
      format: isCy ? 'chengyu' : state.roundFormat,
      stage: isCy ? 'choice' : state.stage,
      answered: isCy ? cy.answered : state.answered,
      shownOptions,
    };
    if (!isCy && state.roundFormat === 'truefalse') context.statement = { ...state.statement };
    const now = new Date().toISOString();
    return {
      section, questionId: record.id, createdAt: now, updatedAt: now, comment: '',
      snapshot: JSON.parse(JSON.stringify(record)), context,
    };
  }

  function mark(section, comment = false) {
    const record = current(section);
    if (!record || !enabled) return;
    const key = `${section}:${record.id}`;
    let existed;
    updateEntries(() => {
      existed = entries.some((entry) => keyOf(entry) === key);
      if (!existed) entries.push(capture(section, record));
    });
    if (comment || existed) openEditor(key);
  }

  function renderList() {
    $('reviewEmpty').hidden = entries.length > 0;
    $('reviewList').replaceChildren(...[...entries].reverse().map((entry) => {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      const heading = document.createElement('strong');
      heading.textContent = titleOf(entry);
      const note = document.createElement('small');
      note.textContent = entry.comment || 'Без комментария';
      button.append(heading, note);
      button.addEventListener('click', () => openEditor(keyOf(entry)));
      item.append(button);
      return item;
    }));
  }

  function openDialog() {
    $('reviewStatus').textContent = '';
    $('reviewCopyText').hidden = true;
    if (!dialog.open) dialog.showModal();
    try { $('reviewShare').hidden = !navigator.canShare?.({ files: [reportFile()] }); }
    catch { $('reviewShare').hidden = true; }
  }

  function openList() {
    editing = null;
    $('reviewEditor').hidden = true;
    $('reviewListPanel').hidden = false;
    renderList();
    openDialog();
    $('reviewClose').focus();
  }

  function openEditor(key) {
    const entry = entries.find((item) => keyOf(item) === key);
    if (!entry) return openList();
    editing = key;
    $('reviewListPanel').hidden = true;
    $('reviewEditor').hidden = false;
    $('reviewQuestion').textContent = titleOf(entry);
    $('reviewMeta').textContent = `${formats[entry.context.format] || entry.section} · ${entry.questionId}`;
    const shown = entry.context.statement
      ? [{ text: `Предложенный ответ: ${entry.context.statement.zh}` }] : entry.context.shownOptions;
    $('reviewShownOptions').replaceChildren(...shown.map((option) => {
      const item = document.createElement('li');
      item.textContent = option.text;
      return item;
    }));
    $('reviewComment').value = entry.comment;
    openDialog();
    $('reviewComment').focus();
  }

  function report() {
    return { type: 'lingvo-question-review', version: 1, exportedAt: new Date().toISOString(), entries };
  }

  function reportFile() {
    return new File([JSON.stringify(report(), null, 2)],
      `lingvo-question-review-${new Date().toISOString().slice(0, 10)}.json`, { type: 'application/json' });
  }

  function reportText() {
    return ['Замечания к вопросам тренажёра',
      'Проверь замечания по источникам и исправь вопросы по правилам проекта, сохраняя их id.',
      ...entries.map((entry, index) => {
        const context = entry.context;
        const lines = [`${index + 1}. ${titleOf(entry)}`, `Раздел: ${entry.section}; id: ${entry.questionId}`,
          `Формат: ${formats[context.format] || context.format}`, `Комментарий: ${entry.comment || '(без комментария)'}`];
        if (context.statement) lines.push(`Предложенный ответ: ${context.statement.zh} (${context.statement.optionId})`);
        if (context.shownOptions.length) lines.push('Показанные варианты:', ...context.shownOptions.map(
          (option) => `- ${option.optionId}: ${option.text}`));
        lines.push('Снимок вопроса:', JSON.stringify(entry.snapshot, null, 2));
        return lines.join('\n');
      })].join('\n\n');
  }

  function removedElsewhere() {
    openList();
    $('reviewStatus').textContent = 'Отметка снята в другой вкладке. Чтобы добавить новый комментарий, отметьте вопрос снова.';
  }

  $('reviewComment').addEventListener('input', () => {
    updateEntries(() => {
      const entry = entries.find((item) => keyOf(item) === editing);
      if (!entry) return removedElsewhere();
      entry.comment = $('reviewComment').value;
      entry.updatedAt = new Date().toISOString();
    });
  });
  $('reviewRemove').addEventListener('click', () => {
    updateEntries(() => { entries = entries.filter((entry) => keyOf(entry) !== editing); });
    openList();
  });
  $('reviewExport').addEventListener('click', () => {
    const file = reportFile();
    const url = URL.createObjectURL(file);
    const link = document.createElement('a');
    link.href = url;
    link.download = file.name;
    document.body.append(link);
    link.click();
    link.remove();
// Даём мобильному браузеру забрать Blob до освобождения адреса.
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
    $('reviewStatus').textContent = 'Файл подготовлен. Прикрепите его к сообщению Codex. Отметки сохранены в списке.';
  });
  $('reviewCopy').addEventListener('click', async () => {
    const text = reportText();
    try {
      await navigator.clipboard.writeText(text);
      $('reviewStatus').textContent = 'Отчёт скопирован. Вставьте его в сообщение Codex.';
    } catch {
      $('reviewCopyText').value = text;
      $('reviewCopyText').hidden = false;
      $('reviewCopyText').focus();
      $('reviewCopyText').select();
      $('reviewStatus').textContent = 'Браузер не разрешил копирование. Скопируйте выделенный текст ниже.';
    }
  });
  $('reviewShare').addEventListener('click', async () => {
    try { await navigator.share({ files: [reportFile()], title: 'Замечания к вопросам' }); }
    catch (error) {
      if (error.name !== 'AbortError') $('reviewStatus').textContent = 'Не удалось поделиться. Используйте выгрузку файла или копирование отчёта.';
    }
  });
  for (const id of ['reviewToggle', 'reviewMenu', 'reviewDisable']) $(id).addEventListener('click', toggleMode);
  for (const [section, prefix] of [['quiz', 'review'], ['chengyu', 'cyReview']]) {
    $(`${prefix}Flag`).addEventListener('click', () => mark(section));
    $(`${prefix}CommentOpen`).addEventListener('click', () => mark(section, true));
  }
  $('reviewOpenList').addEventListener('click', openList);
  $('reviewBack').addEventListener('click', openList);
  $('reviewClose').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { editing = null; });
  document.addEventListener('reviewchange', renderControls);
  document.addEventListener('keydown', (event) => {
    if (dialog.open || event.isComposing || event.repeat || event.altKey
        || event.target.closest?.('input, textarea, select, [contenteditable]')) return;
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.code === 'KeyE') {
      event.preventDefault();
      toggleMode();
    }
  });
  window.addEventListener('storage', (event) => {
    if ((event.key !== KEY && event.key !== null) || storageBlocked) return;
    entries = readEntries() ?? entries;
    renderControls();
    if (dialog.open) {
      if (editing && !entries.some((entry) => keyOf(entry) === editing)) removedElsewhere();
      else if (!editing) renderList();
    }
  });
  entries = readEntries() ?? [];
  try { enabled = localStorage.getItem(MODE_KEY) === 'on'; } catch {}
  renderControls();
})();
