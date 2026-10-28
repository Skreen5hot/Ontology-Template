/* SPDX-License-Identifier: MIT
 *
 * The term explorer.
 *
 * Carried through the Business Capability Ontology from BFO-Aligned
 * ValueNet, where it was written and reviewed in
 * four browser engines. Changed here: it lists upstream terms beside
 * authored ones, so every record says which it is, and the mapping section
 * is gone because nothing in this repository asserts mappings.
 *
 * Reads the generated index and searches it in the browser. No framework,
 * no third-party runtime: the site must render with no external request,
 * and the checker refuses any reference to another origin.
 *
 * THREE RULES THIS FILE IS BUILT AROUND
 *
 * Ontology text is never markup. Every value from the index reaches the
 * page through textContent or a created node -- never innerHTML, not even
 * for a value that "obviously" cannot contain a tag. A definition is
 * authored text in a file anyone can edit, and the day one contains
 * "<img onerror=...>" is not the day to discover the difference.
 *
 * Ranking is deterministic. Two classes matching equally well must come
 * back in the same order every time, so every comparison ends in a tie
 * break on normalised label and then IRI. Sorting by score alone leaves
 * the rest to whatever order the array happened to be in.
 *
 * IRIs are not links. They identify entities and do not resolve; an
 * anchor would send a reader to a 404 and imply the ontology is broken.
 * They are selectable text with a copy button, and if the clipboard
 * refuses -- it does, without a user gesture or a secure context -- the
 * refusal is visible rather than a button that silently does nothing.
 *
 * Nothing is chosen for the reader. A term whose label or definition
 * differs between modules is shown with every variant and the modules
 * each comes from, under the findings the build noted; and each finding
 * the register accepts about the term is shown with its reason. The
 * index carries all of it (`variants`, `notes`, `accepted`), and the
 * status page lists the same notes, so none is only here.
 */

(function () {
  "use strict";

  var INDEX_URL = "../data/terms.json";
  var state = { index: null, module: "", category: "", q: "", selected: "" };

  function $(id) { return document.getElementById(id); }

  /* Text only. The single place ontology-derived strings become DOM. */
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null) { node.textContent = String(text); }
    return node;
  }

  function setStatus(message) { $("status").textContent = message; }

  /* ---------------------------------------------------------------- URL */

  function readParams() {
    var p = new URLSearchParams(window.location.search);
    return {
      q: p.get("q") || "",
      module: p.get("module") || "",
      category: p.get("category") || "",
      selected: p.get("class") || ""
    };
  }

  function paramsFor(next) {
    var p = new URLSearchParams();
    if (next.q) { p.set("q", next.q); }
    if (next.module) { p.set("module", next.module); }
    if (next.category) { p.set("category", next.category); }
    if (next.selected) { p.set("class", next.selected); }
    var query = p.toString();
    return query ? "?" + query : window.location.pathname;
  }

  function pushState(next, replace) {
    var url = paramsFor(next);
    if (replace) { window.history.replaceState(null, "", url); }
    else { window.history.pushState(null, "", url); }
  }

  /* ------------------------------------------------------------ ranking */

  /* Ranking lives in ranking.js so it can be exercised directly rather
   * than through a browser. This file holds the DOM; that one holds the
   * order, and the tests run the same code the site does. */
  var ranking = window.SiteRanking;

  function search() {
    return ranking.search(state.index.classes, state.q,
                          { module: state.module,
                            category: state.category },
                          state.index.modules);
  }

  /* ------------------------------------------------------------ render */

  function excerpt(text, limit) {
    if (text.length <= limit) { return text; }
    return text.slice(0, limit).replace(/\s+\S*$/, "") + "…";
  }

  function resultItem(record) {
    var item = document.createElement("li");
    var link = document.createElement("a");
    /* A real anchor: copyable, openable in a new tab, and in history. */
    link.href = paramsFor({
      q: state.q, module: state.module, category: state.category,
      selected: record.id
    });
    link.className = "result";
    link.appendChild(el("span", "result-label", record.label));
    link.appendChild(el("span", "result-id", record.id));
    link.appendChild(el("span", "result-meta",
                        record.category + " · " + record.module
                        + (record.origin === "upstream" ? " · upstream" : "")
                        + (record.notes.length
                           ? " · " + record.notes.length + " finding(s)"
                           : "")));
    if (record.definition) {
      link.appendChild(el("p", "result-definition",
                          excerpt(record.definition, 160)));
    }
    item.appendChild(link);
    return item;
  }

  function renderResults(matches) {
    var list = $("results");
    list.textContent = "";
    if (!matches.length) {
      list.appendChild(el("li", "empty",
        state.q
          ? "No term matches that search with the current filters."
          : "No term matches the current filters."));
      setStatus("0 terms");
      return;
    }
    for (var i = 0; i < matches.length; i += 1) {
      list.appendChild(resultItem(matches[i].record));
    }
    setStatus(matches.length === 1 ? "1 term" : matches.length + " terms");
  }

  function iriRow(label, value) {
    var wrap = el("div", "iri-row");
    wrap.appendChild(el("span", "iri-label", label));
    var text = el("code", "iri-value", value);
    /* Selectable text, never an anchor: these do not resolve.
     *
     * No tabindex. It was focusable, which put a stop in the tab order at
     * something that does nothing when focused -- focus does not select
     * the text, so it bought a keyboard user an extra Tab per IRI and no
     * capability. Selection is `user-select: all` plus the copy button
     * beside it, which is a real control and is in the tab order. */
    wrap.appendChild(text);

    var button = el("button", "copy", "Copy");
    button.type = "button";
    button.setAttribute("aria-label", "Copy " + label);
    var said = el("span", "copy-result");
    said.setAttribute("role", "status");
    said.setAttribute("aria-live", "polite");
    button.addEventListener("click", function () {
      /* The clipboard refuses without a secure context or a gesture it
       * recognises. A button that silently does nothing is worse than one
       * that says it could not. */
      if (!navigator.clipboard || !navigator.clipboard.writeText) {
        said.textContent = "Clipboard unavailable — select the text to copy.";
        return;
      }
      navigator.clipboard.writeText(value).then(function () {
        said.textContent = "Copied.";
      }, function () {
        said.textContent = "Copy refused by the browser — select the text.";
      });
    });
    wrap.appendChild(button);
    wrap.appendChild(said);
    return wrap;
  }

  function renderDetail(record) {
    var pane = $("detail"), body = $("detail-body");
    body.textContent = "";
    if (!record) {
      pane.hidden = true;
      return;
    }
    body.appendChild(el("h3", "detail-label", record.label));
    body.appendChild(el("p", "detail-id", record.id));
    if (record.notes.length) {
      var box = el("section", "notice-block");
      box.setAttribute("aria-label", "Findings on this term");
      box.appendChild(el("h2", null, "Findings on this term"));
      var noted = document.createElement("ul");
      record.notes.forEach(function (note) {
        noted.appendChild(el("li", null, note.text));
      });
      box.appendChild(noted);
      box.appendChild(el("p", "muted",
        "Shown as the ontology states it. The validator reports the same; "
        + "the status page lists every term like this."));
      body.appendChild(box);
    }
    var conflicting = { label: false, definition: false };
    record.notes.forEach(function (note) {
      if (note.kind === "conflict" || note.kind === "not-literal") {
        conflicting[note.about === "rdfs:label" ? "label" : "definition"]
          = true;
      }
    });
    ["label", "definition"].forEach(function (field) {
      if (!conflicting[field]) { return; }
      body.appendChild(el("h4", null, field === "label"
        ? "Every label, by module" : "Every definition, by module"));
      var list = document.createElement("ul");
      record.variants[field].forEach(function (variant) {
        var li = el("li", null, variant.value);
        li.appendChild(el("span", "muted",
          " — " + (variant.lang ? variant.lang + ", " : "")
          + (variant.literal ? "" : "not a literal, ")
          + "in " + variant.modules.join(", ")));
        list.appendChild(li);
      });
      body.appendChild(list);
    });
    if (conflicting.definition) {
      /* Listed above, each with its module; no one of them is the
       * definition. */
    } else if (record.definition) {
      body.appendChild(el("p", "detail-definition", record.definition));
    } else if (record.origin === "authored") {
      body.appendChild(el("p", "muted",
        "No definition is asserted. That is a finding, listed above."));
    } else {
      /* Upstream stubs are declared and labelled, nothing more. Saying so
       * is better than an empty paragraph that reads as a rendering bug. */
      body.appendChild(el("p", "muted",
        "No definition: this term is declared in the vendored extract "
        + "only so that a reference to it resolves."));
    }

    body.appendChild(iriRow("IRI", record.iri));

    var meta = el("dl", "detail-meta");
    meta.appendChild(el("dt", null, "Origin"));
    meta.appendChild(el("dd", null, record.origin === "upstream"
      ? "Upstream, vendored -- not authored by this project"
      : "Authored in this repository"));
    meta.appendChild(el("dt", null, "Category"));
    meta.appendChild(el("dd", null, record.category));
    meta.appendChild(el("dt", null, record.declared_in.length > 1
      ? "Declared in" : "Module"));
    meta.appendChild(el("dd", null, record.declared_in.join(", ")));
    meta.appendChild(el("dt", null, "Source"));
    meta.appendChild(el("dd", null, record.source));
    body.appendChild(meta);

    if (record.accepted.length) {
      body.appendChild(el("h4", null, "Findings accepted in the register"));
      var accepted = document.createElement("ul");
      record.accepted.forEach(function (entry) {
        var li = el("li", null, entry.severity + ", " + entry.check + ": "
                    + (entry.text || entry.rule));
        li.appendChild(el("p", "muted",
          "Accepted because: " + entry.reason + " Owner: " + entry.owner
          + ". Review by " + entry.review + "."
          + (entry.upstream ? " The defect is upstream: " + entry.upstream
             + "." : "")));
        accepted.appendChild(li);
      });
      body.appendChild(accepted);
    }

    if (record.synonyms.length) {
      body.appendChild(el("h4", null, "Also known as"));
      var syn = document.createElement("ul");
      record.synonyms.forEach(function (value) {
        syn.appendChild(el("li", null, value));
      });
      body.appendChild(syn);
    }

    body.appendChild(el("h4", null, "Named parents"));
    if (!record.parents.length) {
      body.appendChild(el("p", "muted", "None asserted."));
    } else {
      var parents = document.createElement("ul");
      record.parents.forEach(function (parent) {
        /* A parent in the index is a link into it; one outside the index
         * (an upstream term nothing here names) is its IRI as text. */
        var li = document.createElement("li");
        var known = byIri(parent);
        if (known) {
          var a = el("a", null, known.label + " (" + known.id + ")");
          a.href = paramsFor({ q: "", module: "", category: "",
                               selected: known.id });
          li.appendChild(a);
        } else {
          li.appendChild(el("span", "iri-inline", parent));
        }
        parents.appendChild(li);
      });
      body.appendChild(parents);
    }
    pane.hidden = false;
  }

  function byIri(iri) {
    for (var i = 0; i < state.index.classes.length; i += 1) {
      if (state.index.classes[i].iri === iri) { return state.index.classes[i]; }
    }
    return null;
  }

  function byId(id) {
    for (var i = 0; i < state.index.classes.length; i += 1) {
      if (state.index.classes[i].id === id) { return state.index.classes[i]; }
    }
    return null;
  }

  /* ------------------------------------------------------------ wiring */

  function fillSelect(select, values, allLabel) {
    select.textContent = "";
    var any = document.createElement("option");
    any.value = "";
    any.textContent = allLabel;
    select.appendChild(any);
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function apply(options) {
    var matches = search();
    renderResults(matches);

    if (!state.selected) {
      $("jump-wrap").hidden = true;
      renderDetail(null);
      return;
    }
    /* From here the detail pane has content, and it sits after every
     * result in DOM order. Following a result link moves focus there, but
     * arriving on a shared ?class= URL does not -- moving focus on load
     * would wrench it from someone who came to read the page. So the
     * bypass is offered instead of taken: a link ahead of the list, which
     * is what stops a deep link costing 187 tabs. */
    $("jump-wrap").hidden = false;
    var record = byId(state.selected);
    if (!record) {
      var pane = $("detail"), body = $("detail-body");
      body.textContent = "";
      body.appendChild(el("p", "error",
        "No term has the identifier “" + state.selected + "”. It "
        + "may have been renamed, or the link may be from an older build."));
      pane.hidden = false;
      setStatus("Unknown class identifier");
      return;
    }
    renderDetail(record);
    if (options && options.focusDetail) {
      /* Deliberate: following a result link moves focus to what it
       * opened, so a keyboard or screen-reader user is not left at the
       * top of a list that changed underneath them. */
      $("detail").focus();
    }
  }

  function syncControls() {
    $("q").value = state.q;
    $("module").value = state.module;
    $("category").value = state.category;
  }

  function adoptParams(params, options) {
    state.q = params.q;
    state.module = params.module;
    state.category = params.category;
    state.selected = params.selected;
    syncControls();
    apply(options);
  }

  function start(index) {
    state.index = index;
    $("explorer-controls").hidden = false;
    /* Bound here rather than as an onsubmit attribute: the attribute was
     * the only inline script on the site, and a form whose controls all
     * act on input has nothing to submit. */
    $("explorer-controls").addEventListener("submit", function (event) {
      event.preventDefault();
    });

    var modules = index.modules.map(function (m) { return m.key; }).sort();
    var categories = [];
    index.classes.forEach(function (r) {
      if (categories.indexOf(r.category) === -1) {
        categories.push(r.category);
      }
    });
    categories.sort();
    fillSelect($("module"), modules, "All modules");
    fillSelect($("category"), categories, "All categories");

    var params = readParams();
    /* A filter value naming something that does not exist is dropped
     * rather than silently returning nothing: an empty result set would
     * look like a corpus with no such classes. */
    if (params.module && modules.indexOf(params.module) === -1) {
      params.module = "";
    }
    if (params.category && categories.indexOf(params.category) === -1) {
      params.category = "";
    }
    adoptParams(params);
    pushState(state, true);

    $("q").addEventListener("input", function () {
      state.q = $("q").value;
      state.selected = "";
      apply();
      pushState(state, true);
    });
    ["module", "category"].forEach(function (name) {
      $(name).addEventListener("change", function () {
        state[name] = $(name).value;
        apply();
        pushState(state);
      });
    });
    $("clear").addEventListener("click", function () {
      state.q = ""; state.module = ""; state.category = ""; state.selected = "";
      syncControls();
      apply();
      pushState(state);
      $("q").focus();
    });

    $("jump").addEventListener("click", function () {
      /* A button, not a link. It moves focus within the page rather than
       * navigating, which is what a button is for -- and it has to be a
       * button to work: WebKit's default keyboard model puts no anchor in
       * the tab order at all, so as a link this control was unreachable
       * by Tab in that engine while working in the other three. Measured,
       * not assumed: 36 anchors in Chromium, Chrome and Firefox, zero in
       * WebKit. */
      $("detail").focus();
    });

    $("results").addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest("a.result") : null;
      if (!link || event.metaKey || event.ctrlKey || event.shiftKey
          || event.button !== 0) {
        return;   /* let the browser open it in a tab or window */
      }
      event.preventDefault();
      var params = new URLSearchParams(link.search);
      state.selected = params.get("class") || "";
      apply({ focusDetail: true });
      pushState(state);
    });

    window.addEventListener("popstate", function () {
      adoptParams(readParams());
    });
  }

  function fail(message) {
    setStatus(message);
    var list = $("results");
    list.textContent = "";
    var item = el("li", "error", message);
    list.appendChild(item);
  }

  document.addEventListener("DOMContentLoaded", function () {
    setStatus("Loading the term index…");
    fetch(INDEX_URL, { cache: "no-cache" }).then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    }).then(function (index) {
      if (!index || !Array.isArray(index.classes) || !index.classes.length) {
        throw new Error("the index is empty");
      }
      start(index);
    }).catch(function (error) {
      fail("The term index could not be loaded (" + error.message
           + "). The module pages and downloads do not depend on it.");
    });
  });
}());
