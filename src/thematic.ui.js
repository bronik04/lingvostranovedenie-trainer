/* Тематические блоки живут в собственной очереди и хранилище. */
(() => {
  const prefix = 'lingvo-trainer:thematic:v1:';
  const questions = new Map([...QUESTION_BANK, ...LESSON_QUESTIONS].map((record) => [record.id, record]));
  const fallback = new Map();
  let current = null;

  const href = (block) => `#topics/${block.id}`;

  function readProgress(block) {
    try {
      const progress = fallback.has(block.id)
        ? fallback.get(block.id)
        : JSON.parse(localStorage.getItem(prefix + block.id));
      if (!progress) return null;
      const { optionIds, selected, completed } = progress;
      if (!Array.isArray(optionIds) || optionIds.length !== LABELS.length
          || new Set(optionIds).size !== LABELS.length) return null;
      if (selected !== null && !optionIds.includes(selected)) return null;
      if (completed === true && selected !== null) return { completed: true };
      const step = block.steps.find(({ questionId }) => questionId === progress.questionId);
      if (!step) return null;
      const record = questions.get(step.questionId);
      if (!optionIds.every((id) => record.options.some((option) => option.id === id))
          || !optionIds.includes(record.answer.optionId)) return null;
      return { questionId: step.questionId, optionIds, selected, completed: false };
    } catch {
      return null;
    }
  }

  function saveProgress(block, progress) {
    try {
      localStorage.setItem(prefix + block.id, JSON.stringify(progress));
      fallback.delete(block.id);
    } catch {
      fallback.set(block.id, progress);
    }
  }

  function openQuestion(block, index) {
    const { questionId } = block.steps[index];
    const optionIds = labelledOptions(questions.get(questionId)).map((option) => option.optionId);
    const progress = { questionId, optionIds, selected: null, completed: false };
    saveProgress(block, progress);
    return progress;
  }

  function openCatalog() {
    current = null;
    $('lessonBlocks').replaceChildren(...LESSON_BLOCKS.map((block) => {
      const progress = readProgress(block);
      const card = document.createElement('article');
      card.className = 'lesson-block';
      const title = document.createElement('h2');
      title.className = 'ink-title-2';
      title.textContent = block.title;
      const detail = document.createElement('p');
      detail.className = 'ink-caption';
      const count = block.steps.length;
      const size = `${count} ${pluralRu(count, ['вопрос', 'вопроса', 'вопросов'])}`;
      if (progress?.completed) {
        detail.textContent = `${size} · блок пройден`;
      } else if (progress) {
        const index = block.steps.findIndex(({ questionId }) => questionId === progress.questionId);
        detail.textContent = `Вопрос ${index + 1} из ${count}`;
      } else {
        detail.textContent = size;
      }
      const link = document.createElement('a');
      link.className = 'ink-btn ink-btn--primary';
      link.href = href(block);
      link.textContent = progress?.completed ? 'Открыть конспект' : progress ? 'Продолжить' : 'Начать блок';
      link.addEventListener('click', (event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        setAddress(link.hash, true, 'fromLessons');
        openBlock(block);
      });
      card.append(title, detail, link);
      return card;
    }));
    show('lesson-catalog');
    $('lessonCatalogTitle').focus({ preventScroll: true });
  }

  function openBlock(block, progress = readProgress(block) ?? openQuestion(block, 0)) {
    if (progress.completed) {
      current = { block };
      $('lessonSummaryTitle').textContent = block.title;
      $('lessonRecap').replaceChildren(...block.summary.map((item) => {
        const li = document.createElement('li');
        li.append(...questionNodes(item));
        return li;
      }));
      show('lesson-summary', href(block));
      $('lessonSummaryTitle').focus({ preventScroll: true });
      return;
    }

    const index = block.steps.findIndex(({ questionId }) => questionId === progress.questionId);
    const step = block.steps[index];
    const record = questions.get(step.questionId);
    current = { block, progress, index, step, record };
    $('lessonTitle').textContent = block.title;
    $('lessonStep').textContent = `Вопрос ${index + 1} из ${block.steps.length}`;
    $('lessonQuestion').replaceChildren(...questionNodes(record.questionRu));
    $('lessonQuestionZh').hidden = !record.questionZh;
    $('lessonQuestionZh').replaceChildren(...[record.questionZh, pinyinLine(record.questionZh)].filter(Boolean));
    $('lessonOptions').replaceChildren(...progress.optionIds.map((optionId, position) => {
      const { zh, pinyin } = record.options.find((option) => option.id === optionId);
      const button = choiceButton({ optionId, zh, pinyin, label: LABELS[position] });
      button.addEventListener('click', () => answer(optionId));
      return button;
    }));
    renderFeedback();
    show('lesson-quiz', href(block));
    $('lessonQuestion').focus({ preventScroll: true });
  }

  function renderFeedback() {
    const { block, progress, record, step, index } = current;
    const answered = progress.selected !== null;
    $('lessonFeedback').hidden = !answered;
    $('lessonNext').hidden = !answered;
    const done = index + Number(answered);
    $('lessonMeter').setAttribute('aria-valuenow', done);
    $('lessonMeter').setAttribute('aria-valuemax', block.steps.length);
    $('lessonMeterFill').style.width = `${done / block.steps.length * 100}%`;
    if (!answered) return;

    const { correct, answerOptionId } = grade(record, progress.selected);
    const right = record.options.find((option) => option.id === answerOptionId);
    for (const button of $('lessonOptions').children) {
      const { optionId } = button.dataset;
      button.disabled = true;
      button.classList.toggle('correct', optionId === answerOptionId);
      button.classList.toggle('wrong', !correct && optionId === progress.selected);
    }
    $('lessonFeedback').className = `feedback ${correct ? 'good' : 'bad'}`;
    const han = document.createElement('span');
    han.lang = 'zh-Hans';
    han.textContent = right.zh;
    const verdict = document.createElement('strong');
    verdict.append(correct ? 'Верно. ' : 'Правильный ответ — ', han, ` · ${step.answerLabel}`);
    $('lessonVerdict').replaceChildren(verdict);
    $('lessonExplanation').replaceChildren(...questionNodes(step.explanation));
    $('lessonNext').textContent = index === block.steps.length - 1 ? 'К конспекту' : 'Следующий вопрос';
  }

  function answer(optionId) {
    const { block, progress } = current;
    if (progress.selected !== null || !progress.optionIds.includes(optionId)) return;
    progress.selected = optionId;
    saveProgress(block, progress);
    renderFeedback();
    $('lessonFeedback').focus();
  }

  function advance() {
    const { block, progress, index } = current;
    if (progress.selected === null) return;
    if (index === block.steps.length - 1) {
      progress.completed = true;
      saveProgress(block, progress);
      openBlock(block, progress);
    } else {
      openBlock(block, openQuestion(block, index + 1));
    }
  }

  function routeLesson() {
    if (!/^#topics(?:\/|$)/.test(location.hash)) return;
    const block = LESSON_BLOCKS.find((item) => href(item) === location.hash);
    if (block) openBlock(block);
    else openCatalog();
  }

  $('navLessons').addEventListener('click', (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    openCatalog();
  });
  $('lessonLeave').addEventListener('click', openCatalog);
  $('lessonSummaryBack').addEventListener('click', openCatalog);
  $('lessonNext').addEventListener('click', advance);
  $('lessonRestart').addEventListener('click', () => openBlock(current.block, openQuestion(current.block, 0)));
  document.addEventListener('keydown', (event) => {
    if (!['lesson-quiz', 'lesson-summary'].includes(state.view) || event.defaultPrevented
        || event.metaKey || event.ctrlKey || event.altKey || document.querySelector('dialog[open]')) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      openCatalog();
      return;
    }
    if (state.view !== 'lesson-quiz') return;
    const control = document.activeElement?.closest('a, button, summary, input, textarea, select');
    const { progress } = current;
    const index = ANSWER_KEYS[event.code];
    if (index !== undefined && progress.selected === null) {
      event.preventDefault();
      answer(progress.optionIds[index]);
    } else if ((event.key === 'Enter' || event.key === ' ') && progress.selected !== null && !control) {
      event.preventDefault();
      advance();
    }
  });
  window.addEventListener('popstate', routeLesson);
  window.addEventListener('storage', (event) => {
    if (event.key?.startsWith(prefix)) routeLesson();
  });
  routeLesson();
})();
