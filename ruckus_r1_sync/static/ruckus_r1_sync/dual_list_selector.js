(function () {
  function bySel(root, sel) { return root.querySelector(sel); }

  // Move only selected options from one select to another.
  // IMPORTANT: When moving into the "selected for sync" list, options must remain selected
  // so the browser submits them in the POST.
  function moveSelected(from, to, selectOnMove) {
    const opts = Array.from(from.options).filter(o => o.selected);
    for (const o of opts) {
      o.selected = !!selectOnMove;
      to.add(o);
    }
  }

  // Move all options from one select to another.
  function moveAll(from, to, selectOnMove) {
    const opts = Array.from(from.options);
    for (const o of opts) {
      o.selected = !!selectOnMove;
      to.add(o);
    }
  }

  function rebuildAvailable(allChoices, selectedEl, availableEl) {
    const selected = new Set(Array.from(selectedEl.options).map(o => o.value));
    availableEl.innerHTML = "";
    for (const pair of allChoices) {
      const val = pair[0];
      const label = pair[1];
      if (!selected.has(val)) {
        const opt = document.createElement("option");
        opt.value = val;
        opt.textContent = label;
        availableEl.add(opt);
      }
    }
  }

  function initOne(root) {
    const allEl = bySel(root, "[data-duallist-all]");
    const availableEl = bySel(root, "[data-duallist-available]");
    const selectedEl = bySel(root, "[data-duallist-selected]");
    const addBtn = bySel(root, "[data-duallist-add]");
    const removeBtn = bySel(root, "[data-duallist-remove]");
    const addAllBtn = bySel(root, "[data-duallist-addall]");
    const removeAllBtn = bySel(root, "[data-duallist-removeall]");

    if (!allEl || !availableEl || !selectedEl) return;

    const allChoices = Array.from(allEl.options).map(o => [o.value, o.textContent]);

    // Initial populate of the left list from ALL choices minus what is already in the right list
    rebuildAvailable(allChoices, selectedEl, availableEl);

    // Buttons
    addBtn && addBtn.addEventListener("click", function () {
      // left -> right (must be selected to be submitted)
      moveSelected(availableEl, selectedEl, true);
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    removeBtn && removeBtn.addEventListener("click", function () {
      // right -> left (does not need to stay selected)
      moveSelected(selectedEl, availableEl, false);
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    addAllBtn && addAllBtn.addEventListener("click", function () {
      // left -> right all (must be selected to be submitted)
      moveAll(availableEl, selectedEl, true);
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    removeAllBtn && removeAllBtn.addEventListener("click", function () {
      // empty right list => sync ALL venues
      selectedEl.innerHTML = "";
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    // Double-click UX
    availableEl.addEventListener("dblclick", function () {
      moveSelected(availableEl, selectedEl, true);
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    selectedEl.addEventListener("dblclick", function () {
      moveSelected(selectedEl, availableEl, false);
      rebuildAvailable(allChoices, selectedEl, availableEl);
    });

    // Safety net: On submit, mark ALL right-side options as selected so the browser submits them.
    const form = selectedEl.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        Array.from(selectedEl.options).forEach(o => { o.selected = true; });
      });
    }
  }

  function initAll() {
    document.querySelectorAll("[data-duallist]").forEach(initOne);
  }

  // Handle both cases:
  // - script loaded before DOM ready -> wait
  // - script loaded after DOM ready -> run now
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
