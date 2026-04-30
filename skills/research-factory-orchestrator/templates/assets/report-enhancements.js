
(function () {
  const filter = document.querySelector("[data-source-filter]");
  if (!filter) return;
  filter.addEventListener("input", function () {
    const q = filter.value.toLowerCase();
    document.querySelectorAll("[data-source-row]").forEach(function (row) {
      row.hidden = q && !row.textContent.toLowerCase().includes(q);
    });
  });
})();
