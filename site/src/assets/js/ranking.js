/* SPDX-License-Identifier: MIT
 *
 * Search ranking for the class explorer.
 *
 * Separated from the DOM code so it can be exercised directly rather than
 * through a browser. A ranking tested by re-implementing it in the test
 * proves the re-implementation works; this is the code the site runs.
 *
 * The order is the plan's: exact label, identifier or IRI, label prefix,
 * label token, synonym, then a substring of the definition, the IRI, or
 * the module -- by key or by title.
 *
 * A full IRI is an exact identifier, not a substring of one. Someone
 * pasting an IRI from a Turtle file has typed the most specific thing
 * they could, and ranking that below a label prefix put the class they
 * named underneath classes they did not.
 *
 * Module titles are passed in rather than copied onto every record. The
 * index holds 187 classes and 5 modules; stamping the title into each
 * record would repeat five strings 187 times and create a second place
 * for the title to be wrong.
 *
 * Every comparison ends in a tie break on normalised label and then IRI.
 * Sorting by score alone leaves equal matches in whatever order the array
 * happened to hold, which differs between builds and between browsers,
 * and makes "the first result" a thing nobody can predict or test. Six
 * labels in this corpus are shared between modules, so the tie break is
 * load-bearing rather than theoretical.
 */

(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module && module.exports) {
    module.exports = factory();
  } else {
    root.SiteRanking = factory();
  }
}(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var EXACT = 0, PREFIX = 1, TOKEN = 2, SYNONYM = 3, SUBSTRING = 4, NONE = 9;

  /* key -> lowercased human-readable title, built once per search. */
  function moduleTitles(modules) {
    var map = {};
    if (!modules) { return map; }
    for (var i = 0; i < modules.length; i += 1) {
      var entry = modules[i];
      if (entry && entry.key && entry.title) {
        map[entry.key] = String(entry.title).toLowerCase();
      }
    }
    return map;
  }

  function rank(record, needle, titles) {
    if (!needle) { return NONE; }
    var label = String(record.label).toLowerCase();
    var id = String(record.id).toLowerCase();
    var iri = String(record.iri).toLowerCase();
    if (label === needle || id === needle || iri === needle) { return EXACT; }
    if (label.indexOf(needle) === 0 || id.indexOf(needle) === 0) {
      return PREFIX;
    }
    var tokens = label.split(/\s+/);
    for (var i = 0; i < tokens.length; i += 1) {
      if (tokens[i] === needle || tokens[i].indexOf(needle) === 0) {
        return TOKEN;
      }
    }
    var synonyms = record.synonyms || [];
    for (var s = 0; s < synonyms.length; s += 1) {
      if (String(synonyms[s]).toLowerCase().indexOf(needle) !== -1) {
        return SYNONYM;
      }
    }
    var title = (titles && titles[record.module]) || "";
    if (String(record.definition).toLowerCase().indexOf(needle) !== -1
        || iri.indexOf(needle) !== -1
        || String(record.module).toLowerCase().indexOf(needle) !== -1
        || (title && title.indexOf(needle) !== -1)) {
      return SUBSTRING;
    }
    return NONE;
  }

  function compare(a, b) {
    if (a.score !== b.score) { return a.score - b.score; }
    var la = String(a.record.label).toLowerCase();
    var lb = String(b.record.label).toLowerCase();
    if (la !== lb) { return la < lb ? -1 : 1; }
    if (a.record.iri !== b.record.iri) {
      return a.record.iri < b.record.iri ? -1 : 1;
    }
    return 0;
  }

  /* Filters then ranks. An empty query keeps everything at SUBSTRING so
   * the filtered set is browsable without typing.
   *
   * `modules` is the index's module list. Omitting it costs only the
   * title field: everything else still ranks. */
  function search(records, query, filters, modules) {
    var needle = String(query || "").trim().toLowerCase();
    var wantModule = (filters && filters.module) || "";
    var wantCategory = (filters && filters.category) || "";
    var titles = moduleTitles(modules);
    var out = [];
    for (var i = 0; i < records.length; i += 1) {
      var record = records[i];
      if (wantModule && record.module !== wantModule) { continue; }
      if (wantCategory && record.category !== wantCategory) { continue; }
      var score = needle ? rank(record, needle, titles) : SUBSTRING;
      if (score === NONE) { continue; }
      out.push({ record: record, score: score });
    }
    out.sort(compare);
    return out;
  }

  return {
    EXACT: EXACT, PREFIX: PREFIX, TOKEN: TOKEN,
    SYNONYM: SYNONYM, SUBSTRING: SUBSTRING, NONE: NONE,
    moduleTitles: moduleTitles, rank: rank, compare: compare, search: search
  };
}));
