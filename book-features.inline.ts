type BookChapter = {
  number: number;
  title: string;
  href: string;
  part?: number;
};
type BookPart = { number: number; title: string; first: number; last: number };
type BookLastRead = {
  number: number;
  href: string;
  anchor: string;
  percent: number;
};
type BookReadingState = {
  version: 1;
  completed: number[];
  lastRead: BookLastRead | null;
};
type LibraryBook = {
  id: string;
  title: string;
  root: URL;
  sitePath: string;
  manifest: URL;
  chapterCount: number;
  chapters: Map<number, BookChapter>;
  parts: BookPart[];
  pendingManifest?: Promise<void>;
};

const bookWindow = window as Window & {
  __libraryBookFeaturesInstalled?: boolean;
};

if (!bookWindow.__libraryBookFeaturesInstalled) {
  bookWindow.__libraryBookFeaturesInstalled = true;
  const memory = new Map<string, BookReadingState>();
  const libraries = new Map<string, Promise<LibraryBook[]>>();
  let storageAvailable = true;
  let generation = 0;
  let disposePage: () => void = () => {};
  let refreshPage: () => void = () => {};

  function findSiteRoot(): URL {
    // Quartz emits this script at the site root, including /books/ deployments.
    // A chapter's folder is a book root, so it must never be used as the site root.
    for (const script of document.querySelectorAll<HTMLScriptElement>(
      "script[src]",
    )) {
      const url = new URL(script.src, location.href);
      if (
        url.origin === location.origin &&
        /\/postscript(?:-[\w]+)?\.js$/.test(url.pathname)
      ) {
        return new URL("./", url);
      }
    }
    const home = document.querySelector<HTMLAnchorElement>(".page-title a");
    if (home) {
      const url = new URL(home.href, location.href);
      if (url.origin === location.origin) {
        url.hash = "";
        url.search = "";
        if (/\/index(?:\.html)?$/.test(url.pathname)) return new URL("./", url);
        if (url.pathname.endsWith("/")) return url;
      }
    }
    return new URL("./", location.href);
  }

  function validNumber(book: LibraryBook, value: unknown): number | null {
    const number = Number(value);
    return Number.isInteger(number) &&
      number >= 1 &&
      number <= book.chapterCount
      ? number
      : null;
  }

  function stateKey(book: LibraryBook): string {
    return `ai-generation-library:reading:v1:${book.sitePath}:${book.id}`;
  }

  function emptyState(): BookReadingState {
    return { version: 1, completed: [], lastRead: null };
  }

  function chapterURL(
    book: LibraryBook,
    value: string,
    expected?: number,
  ): URL | null {
    try {
      const url = new URL(value, book.root);
      if (
        url.origin !== book.root.origin ||
        !url.pathname.startsWith(book.root.pathname)
      )
        return null;
      const known =
        expected === undefined ? undefined : book.chapters.get(expected);
      const relative = url.pathname.slice(book.root.pathname.length);
      const match = relative.match(/^(\d+)-[^/]+\/chapter(?:\.html)?\/?$/);
      // Manifest chapters may use descriptive folders; numbered folders also
      // allow the reader controls to work when the manifest fetch is offline.
      if (known) {
        if (
          url.pathname.replace(/\.html\/?$/, "").replace(/\/$/, "") !==
          known.href.replace(/\.html\/?$/, "").replace(/\/$/, "")
        )
          return null;
      } else if (
        !match ||
        validNumber(book, match[1]) === null ||
        (expected !== undefined && Number(match[1]) !== expected)
      ) {
        return null;
      }
      url.search = "";
      return url;
    } catch {
      return null;
    }
  }

  function cleanState(book: LibraryBook, value: unknown): BookReadingState {
    if (typeof value !== "object" || value === null) return emptyState();
    const raw = value as Partial<BookReadingState>;
    const completed = Array.isArray(raw.completed)
      ? [
          ...new Set(
            raw.completed
              .map((value) => validNumber(book, value))
              .filter((n): n is number => n !== null),
          ),
        ]
      : [];
    let lastRead: BookLastRead | null = null;
    if (raw.lastRead && typeof raw.lastRead === "object") {
      const last = raw.lastRead;
      const number = validNumber(book, last.number);
      const url =
        typeof last.href === "string" && number
          ? chapterURL(book, last.href, number)
          : null;
      if (url && number) {
        lastRead = {
          number,
          href: url.pathname,
          anchor:
            typeof last.anchor === "string" ? last.anchor.slice(0, 200) : "",
          percent: Number.isFinite(last.percent)
            ? Math.min(100, Math.max(0, last.percent))
            : 0,
        };
      }
    }
    return { version: 1, completed, lastRead };
  }

  function readState(book: LibraryBook): BookReadingState {
    const key = stateKey(book);
    if (storageAvailable) {
      let raw: string | null = null;
      try {
        raw = window.localStorage.getItem(key);
      } catch {
        // Privacy mode and SecurityError must not break reading.
        storageAvailable = false;
      }
      if (storageAvailable) {
        let state = emptyState();
        try {
          if (raw && raw.length < 20000)
            state = cleanState(book, JSON.parse(raw));
        } catch {
          // A malformed value resets only this book's progress.
        }
        memory.set(key, state);
        return state;
      }
    }
    return memory.get(key) ?? emptyState();
  }

  function saveState(book: LibraryBook, state: BookReadingState): void {
    const key = stateKey(book);
    memory.set(key, state);
    if (storageAvailable) {
      try {
        window.localStorage.setItem(key, JSON.stringify(state));
      } catch {
        storageAvailable = false;
      }
    }
  }

  function loadLibrary(root: URL): Promise<LibraryBook[]> {
    const cached = libraries.get(root.href);
    if (cached) return cached;
    const pending = fetch(new URL("static/library-manifest.json", root), {
      credentials: "same-origin",
    })
      .then(async (response) => {
        if (!response.ok) return [];
        const value: unknown = await response.json();
        if (typeof value !== "object" || value === null) return [];
        const books = (value as { books?: unknown }).books;
        if (!Array.isArray(books)) return [];
        const seen = new Set<string>();
        const result: LibraryBook[] = [];
        for (const item of books) {
          if (typeof item !== "object" || item === null) continue;
          const candidate = item as Record<string, unknown>;
          if (
            typeof candidate.id !== "string" ||
            !/^[a-z0-9][a-z0-9_-]*$/.test(candidate.id) ||
            seen.has(candidate.id)
          )
            continue;
          if (
            typeof candidate.href !== "string" ||
            typeof candidate.manifest !== "string"
          )
            continue;
          const count = Number(candidate.chapterCount);
          if (!Number.isInteger(count) || count < 1 || count > 10000) continue;
          const bookRoot = new URL(candidate.href, root);
          const manifest = new URL(candidate.manifest, root);
          if (
            bookRoot.origin !== root.origin ||
            bookRoot.pathname === root.pathname ||
            !bookRoot.pathname.startsWith(root.pathname)
          )
            continue;
          if (!bookRoot.pathname.endsWith("/")) bookRoot.pathname += "/";
          if (
            manifest.origin !== root.origin ||
            !manifest.pathname.startsWith(bookRoot.pathname)
          )
            continue;
          bookRoot.hash = "";
          bookRoot.search = "";
          seen.add(candidate.id);
          result.push({
            id: candidate.id,
            title:
              typeof candidate.title === "string"
                ? candidate.title
                : candidate.id,
            root: bookRoot,
            sitePath: root.pathname,
            manifest,
            chapterCount: count,
            chapters: new Map(),
            parts: [],
          });
        }
        return result;
      })
      .catch(() => []);
    libraries.set(root.href, pending);
    return pending;
  }

  function collectChapterLinks(book: LibraryBook): void {
    for (const element of document.querySelectorAll<HTMLElement>(
      "[data-book-chapter]",
    )) {
      const number = validNumber(book, element.dataset.bookChapter);
      const link = element.matches("a")
        ? (element as HTMLAnchorElement)
        : element.querySelector<HTMLAnchorElement>("a[href]");
      const url = number && link ? chapterURL(book, link.href, number) : null;
      if (!number || !link || !url) continue;
      const existing = book.chapters.get(number);
      book.chapters.set(number, {
        number,
        title:
          link.querySelector(".chapter-name")?.textContent?.trim() ||
          existing?.title ||
          `${number}장`,
        href: url.pathname,
        part: existing?.part,
      });
    }
  }

  function loadManifest(book: LibraryBook): Promise<void> {
    if (book.pendingManifest) return book.pendingManifest;
    book.pendingManifest = fetch(book.manifest, { credentials: "same-origin" })
      .then(async (response) => {
        if (!response.ok) return;
        const value: unknown = await response.json();
        if (typeof value !== "object" || value === null) return;
        const manifest = value as Record<string, unknown>;
        if (manifest.id !== undefined && manifest.id !== book.id) return;
        if (typeof manifest.title === "string") book.title = manifest.title;
        if (Array.isArray(manifest.chapters)) {
          for (const item of manifest.chapters) {
            if (typeof item !== "object" || item === null) continue;
            const candidate = item as Record<string, unknown>;
            const number = validNumber(book, candidate.number);
            if (!number || typeof candidate.href !== "string") continue;
            const url = new URL(candidate.href, book.root);
            if (
              url.origin !== book.root.origin ||
              !url.pathname.startsWith(book.root.pathname) ||
              !/\/chapter(?:\.html)?\/?$/.test(url.pathname)
            )
              continue;
            const existing = book.chapters.get(number);
            book.chapters.set(number, {
              number,
              href: url.pathname,
              title:
                typeof candidate.title === "string"
                  ? candidate.title
                  : existing?.title || `${number}장`,
              part:
                typeof candidate.part === "number" &&
                Number.isInteger(candidate.part) &&
                candidate.part > 0
                  ? candidate.part
                  : undefined,
            });
          }
        }
        if (Array.isArray(manifest.parts)) {
          book.parts = manifest.parts.flatMap((item) => {
            if (typeof item !== "object" || item === null) return [];
            const part = item as Record<string, unknown>;
            const first = validNumber(book, part.first);
            const last = validNumber(book, part.last);
            if (
              !Number.isInteger(part.number) ||
              Number(part.number) < 1 ||
              !first ||
              !last ||
              first > last
            )
              return [];
            return [
              {
                number: Number(part.number),
                title: typeof part.title === "string" ? part.title : "",
                first,
                last,
              },
            ];
          });
        }
      })
      .catch(() => {
        // An unavailable manifest leaves the normal page and its links usable.
      });
    return book.pendingManifest;
  }

  function updateProgress(
    progress: HTMLElement,
    book: LibraryBook,
    count: number,
  ): void {
    if (progress instanceof HTMLProgressElement) {
      progress.max = book.chapterCount;
      progress.value = count;
    } else {
      progress.setAttribute("role", "progressbar");
      progress.setAttribute("aria-valuemin", "0");
      progress.setAttribute("aria-valuemax", String(book.chapterCount));
      progress.setAttribute("aria-valuenow", String(count));
    }
    progress.setAttribute(
      "aria-label",
      `${book.title} 전체 ${book.chapterCount}장 중 ${count}장 읽기 완료`,
    );
    progress.style.setProperty(
      "--book-progress",
      `${(count / book.chapterCount) * 100}%`,
    );
  }

  function updateLibraryCards(books: LibraryBook[]): void {
    for (const card of document.querySelectorAll<HTMLElement>(
      "[data-library-book]",
    )) {
      const book = books.find((item) => item.id === card.dataset.libraryBook);
      if (!book) continue;
      const count = readState(book).completed.length;
      for (const progress of card.querySelectorAll<HTMLElement>(
        "[data-library-progress]",
      )) {
        updateProgress(progress, book, count);
        if (!(progress instanceof HTMLProgressElement))
          progress.textContent = `${count} / ${book.chapterCount}장 완료`;
      }
      for (const label of card.querySelectorAll(
        "[data-library-progress-count]",
      ))
        label.textContent = `${count} / ${book.chapterCount}장 완료`;
    }
  }

  function updateHomepage(book: LibraryBook): void {
    const state = readState(book);
    const completed = new Set(state.completed);
    for (const progress of document.querySelectorAll<HTMLElement>(
      "[data-book-progress]",
    ))
      updateProgress(progress, book, completed.size);
    for (const count of document.querySelectorAll("[data-book-progress-count]"))
      count.textContent = `${completed.size} / ${book.chapterCount}장 완료`;
    for (const label of document.querySelectorAll<HTMLElement>(
      "[data-book-completed]",
    )) {
      const number = validNumber(book, label.dataset.bookCompleted);
      const done = number !== null && completed.has(number);
      label.textContent = done ? "읽기 완료" : "읽기 전";
      label.classList.toggle("is-complete", done);
      label.dataset.completed = String(done);
      label
        .closest(".chapter-card, .book-chapter-card, [data-book-chapter-card]")
        ?.classList.toggle("is-complete", done);
    }
    const last = state.lastRead;
    const remaining = [...book.chapters.values()]
      .sort((a, b) => a.number - b.number)
      .filter((chapter) => !completed.has(chapter.number));
    const next =
      last && !completed.has(last.number)
        ? (book.chapters.get(last.number) ?? {
            number: last.number,
            title: `${last.number}장`,
            href: last.href,
          })
        : (remaining.find((chapter) => chapter.number > (last?.number ?? 0)) ??
          remaining[0] ??
          book.chapters.get(1));
    if (!next) return;
    const url = chapterURL(book, next.href, next.number);
    if (!url) return;
    if (
      last?.number === next.number &&
      last.anchor &&
      !completed.has(next.number)
    )
      url.hash = last.anchor;
    for (const link of document.querySelectorAll<HTMLAnchorElement>(
      "a[data-book-resume]",
    )) {
      link.href = url.pathname + url.hash;
      link.textContent =
        completed.size === book.chapterCount
          ? `${book.chapterCount}장 완독 · 다시 읽기`
          : `이어서 읽기 · ${String(next.number).padStart(2, "0")}장`;
      link.setAttribute(
        "aria-label",
        `${book.title} ${next.number}장 ${next.title} ${completed.size === book.chapterCount ? "다시 읽기" : "이어서 읽기"}`,
      );
    }
  }

  function partFor(book: LibraryBook, number: number): number | undefined {
    return (
      book.chapters.get(number)?.part ??
      book.parts.find((part) => number >= part.first && number <= part.last)
        ?.number
    );
  }

  function chapterNumber(book: LibraryBook): number | null {
    const path = location.pathname.replace(/\.html\/?$/, "").replace(/\/$/, "");
    for (const chapter of book.chapters.values()) {
      if (chapter.href.replace(/\.html\/?$/, "").replace(/\/$/, "") === path)
        return chapter.number;
    }
    const match = location.pathname
      .slice(book.root.pathname.length)
      .match(/^(\d+)-[^/]+\/chapter(?:\.html)?\/?$/);
    return match ? validNumber(book, match[1]) : null;
  }

  async function initializeBookPage(): Promise<void> {
    disposePage();
    const pageGeneration = ++generation;
    refreshPage = () => {};
    const books = await loadLibrary(findSiteRoot());
    if (generation !== pageGeneration) return;
    updateLibraryCards(books);
    const book = books
      .filter(
        (item) =>
          location.pathname === item.root.pathname.replace(/\/$/, "") ||
          location.pathname.startsWith(item.root.pathname),
      )
      .sort((a, b) => b.root.pathname.length - a.root.pathname.length)[0];
    if (!book) {
      refreshPage = () => updateLibraryCards(books);
      return;
    }
    collectChapterLinks(book);
    await loadManifest(book);
    if (generation !== pageGeneration) return;
    collectChapterLinks(book);
    updateHomepage(book);
    const number = chapterNumber(book);
    const article = document.querySelector<HTMLElement>(
      "article.popover-hint, article, .page-body",
    );
    const abort = new AbortController();
    let observer: ResizeObserver | undefined;
    let frame = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let toolbar: HTMLElement | undefined;
    let readingBar: HTMLElement | undefined;
    let disposed = false;
    let savePosition: () => void = () => {};
    refreshPage = () => {
      updateHomepage(book);
      updateLibraryCards(books);
    };

    if (number && article) {
      const chapterHref = location.pathname;
      toolbar = document.createElement("section");
      toolbar.className = "book-chapter-toolbar";
      toolbar.dataset.bookGenerated = "toolbar";
      toolbar.setAttribute("aria-label", `${book.title} · 장 학습 상태`);
      const position = document.createElement("p");
      position.className = "book-chapter-position";
      const controls = document.createElement("div");
      controls.className = "book-chapter-actions";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "book-completion-toggle";
      const currentProgress = document.createElement("span");
      currentProgress.className = "book-reading-label";
      currentProgress.setAttribute("aria-hidden", "true");
      const note = document.createElement("p");
      note.className = "book-storage-notice";
      const status = document.createElement("span");
      status.className = "book-status";
      status.setAttribute("role", "status");
      status.setAttribute("aria-live", "polite");
      controls.append(button, currentProgress);
      toolbar.append(position, controls, note, status);
      article.before(toolbar);
      readingBar = document.createElement("div");
      readingBar.className = "book-reading-progress";
      readingBar.dataset.bookGenerated = "progress";
      readingBar.setAttribute("role", "progressbar");
      readingBar.setAttribute("aria-label", "이 장 본문 읽기 진도");
      readingBar.setAttribute("aria-valuemin", "0");
      readingBar.setAttribute("aria-valuemax", "100");
      const fill = document.createElement("div");
      fill.className = "book-reading-progress-fill";
      readingBar.append(fill);
      document.body.prepend(readingBar);
      let percent = 0;

      function renderChapter(): void {
        const done = readState(book).completed.includes(number!);
        const part = partFor(book, number!);
        position.textContent = `${part ? `PART ${part} · ` : ""}CHAPTER ${String(number).padStart(2, "0")} / ${book.chapterCount}`;
        button.textContent = done ? "✓ 읽기 완료 · 취소" : "읽기 완료 표시";
        button.setAttribute("aria-pressed", String(done));
        button.classList.toggle("is-complete", done);
        note.textContent = storageAvailable
          ? "학습 기록은 이 브라우저에 저장됩니다."
          : "브라우저 저장을 사용할 수 없어 현재 탭에서만 기록됩니다.";
      }

      savePosition = () => {
        const fresh = readState(book);
        let anchor = "";
        for (const heading of article.querySelectorAll<HTMLElement>(
          "h2[id], h3[id]",
        )) {
          if (heading.getBoundingClientRect().top <= 140) anchor = heading.id;
          else break;
        }
        fresh.lastRead = { number, href: chapterHref, anchor, percent };
        saveState(book, fresh);
      };

      function updateReadingProgress(): void {
        frame = 0;
        const bounds = article!.getBoundingClientRect();
        const top = bounds.top + window.scrollY;
        const travel = bounds.height - window.innerHeight;
        percent =
          travel <= 0
            ? bounds.bottom <= window.innerHeight
              ? 100
              : 0
            : Math.round(
                Math.min(1, Math.max(0, (window.scrollY - top) / travel)) * 100,
              );
        fill.style.width = `${percent}%`;
        readingBar!.setAttribute("aria-valuenow", String(percent));
        currentProgress.textContent = `본문 ${percent}%`;
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
          savePosition();
          renderChapter();
        }, 350);
      }

      function scheduleProgress(): void {
        if (!frame) frame = requestAnimationFrame(updateReadingProgress);
      }

      button.addEventListener(
        "click",
        () => {
          const fresh = readState(book);
          const done = fresh.completed.includes(number);
          fresh.completed = done
            ? fresh.completed.filter((n) => n !== number)
            : [...fresh.completed, number];
          saveState(book, fresh);
          savePosition();
          renderChapter();
          updateHomepage(book);
          updateLibraryCards(books);
          status.textContent = done
            ? `${number}장 완료 표시를 취소했습니다.`
            : `${number}장을 읽기 완료로 표시했습니다.`;
        },
        { signal: abort.signal },
      );
      window.addEventListener("scroll", scheduleProgress, {
        passive: true,
        signal: abort.signal,
      });
      window.addEventListener("resize", scheduleProgress, {
        passive: true,
        signal: abort.signal,
      });
      window.addEventListener("pagehide", savePosition, {
        signal: abort.signal,
      });
      if (typeof ResizeObserver !== "undefined") {
        observer = new ResizeObserver(scheduleProgress);
        observer.observe(article);
      }
      renderChapter();
      updateReadingProgress();
      savePosition();
      refreshPage = () => {
        renderChapter();
        updateHomepage(book);
        updateLibraryCards(books);
      };
    }

    disposePage = () => {
      if (disposed) return;
      disposed = true;
      savePosition();
      abort.abort();
      observer?.disconnect();
      if (frame) cancelAnimationFrame(frame);
      if (timer) clearTimeout(timer);
      toolbar?.remove();
      readingBar?.remove();
      refreshPage = () => {};
    };
    if (typeof window.addCleanup === "function") window.addCleanup(disposePage);
  }

  // One listener set. Each SPA navigation owns its book and cleans up bindings.
  document.addEventListener("nav", () => {
    void initializeBookPage();
  });
  document.addEventListener("render", () => {
    void initializeBookPage();
  });
  window.addEventListener("storage", (event) => {
    if (
      event.key === null ||
      event.key?.startsWith(
        `ai-generation-library:reading:v1:${findSiteRoot().pathname}:`,
      )
    )
      refreshPage();
  });
  void initializeBookPage();
}
