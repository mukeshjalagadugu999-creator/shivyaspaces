// Apply theme immediately before page renders — prevents flash
(function () {
  var saved = localStorage.getItem("siteTheme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute("data-theme") || "light";
  var next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("siteTheme", next);
  updateToggleLabels();
}

function updateToggleLabels() {
  var theme = document.documentElement.getAttribute("data-theme");
  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
  });
}

document.addEventListener("DOMContentLoaded", function () {
  updateToggleLabels();
});

// KEY FIX: pageshow fires when page is restored from browser cache (back button)
// This re-applies the correct saved theme even on cached pages
window.addEventListener("pageshow", function () {
  var saved = localStorage.getItem("siteTheme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  updateToggleLabels();
});

// Sync across tabs — if you change theme in one tab, all others update too
window.addEventListener("storage", function (e) {
  if (e.key === "siteTheme") {
    var newTheme = e.newValue || "light";
    document.documentElement.setAttribute("data-theme", newTheme);
    updateToggleLabels();
  }
});