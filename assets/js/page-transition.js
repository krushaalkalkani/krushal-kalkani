// Smooth page transitions for the static multi-page site.
// On load the content fades/slides in (handled in CSS via .content-column).
// Here we fade the current page OUT before following an internal link, so
// navigating (e.g. clicking "Read") no longer shows a harsh flash.
(function () {
  "use strict";

  var root = document.documentElement;
  var reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // How long the leave animation runs — keep in sync with the CSS
  // `.is-leaving .content-column` transition (240ms) plus a small buffer.
  var LEAVE_MS = 260;

  // Returns true if this click should trigger an animated same-tab navigation.
  function isInternalNavigation(link, event) {
    if (
      event.defaultPrevented ||
      event.button !== 0 || // not a left-click
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return false;
    }
    if (
      !link ||
      link.target === "_blank" ||
      link.hasAttribute("download") ||
      link.getAttribute("rel") === "external"
    ) {
      return false;
    }

    var href = link.getAttribute("href");
    if (!href || href.charAt(0) === "#") {
      return false; // same-page anchor — no navigation
    }

    var url;
    try {
      url = new URL(link.href, window.location.href);
    } catch (e) {
      return false;
    }

    // Different origin → let the browser handle it normally.
    if (url.origin !== window.location.origin) {
      return false;
    }
    // Same page, just a hash change → don't fade out.
    if (
      url.pathname === window.location.pathname &&
      url.search === window.location.search &&
      url.hash
    ) {
      return false;
    }
    return true;
  }

  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a[href]");
    if (!link || !isInternalNavigation(link, event)) {
      return;
    }

    if (reduceMotion) {
      return; // honor reduced-motion: instant navigation
    }

    event.preventDefault();
    var destination = link.href;
    root.classList.add("is-leaving");

    window.setTimeout(function () {
      window.location.href = destination;
    }, LEAVE_MS);
  });

  // Coming back via the back/forward cache restores the old DOM with
  // .is-leaving still set — clear it so the page is visible again.
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      root.classList.remove("is-leaving");
    }
  });
})();
