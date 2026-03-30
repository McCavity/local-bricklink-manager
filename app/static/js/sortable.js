/**
 * Client-side table sorting.
 * Add class "sortable" to any <table> to enable.
 * Add data-sort-value="..." to <td> cells to override sort value.
 * Add class "col-no-sort" to <th> to disable sorting on that column.
 * Default sort: descending on first click, ascending on second.
 * For the "col-number" class, parses as number.
 */
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("table.sortable").forEach(initSortable);
});

function initSortable(table) {
    var headers = table.querySelectorAll("thead th");
    var tbody = table.querySelector("tbody");
    if (!tbody) return;

    headers.forEach(function (th, colIndex) {
        if (th.classList.contains("col-no-sort")) return;

        // Add sort arrows
        var arrows = document.createElement("span");
        arrows.className = "sort-arrows";
        arrows.innerHTML = ' <span class="sort-arrow sort-arrow-up">\u25B2</span><span class="sort-arrow sort-arrow-down">\u25BC</span>';
        th.appendChild(arrows);

        th.addEventListener("click", function () {
            var currentDir = th.dataset.sortDir;
            // Clear all other headers
            headers.forEach(function (h) {
                h.classList.remove("sort-asc", "sort-desc");
                delete h.dataset.sortDir;
            });

            // Toggle direction
            var newDir;
            if (currentDir === "desc") {
                newDir = "asc";
            } else {
                newDir = "desc";
            }

            th.dataset.sortDir = newDir;
            th.classList.add("sort-" + newDir);

            sortTable(tbody, colIndex, newDir, th.classList.contains("col-number"));
        });
    });
}

function sortTable(tbody, colIndex, direction, isNumeric) {
    var rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort(function (a, b) {
        var aCell = a.children[colIndex];
        var bCell = b.children[colIndex];
        if (!aCell || !bCell) return 0;

        var aVal = aCell.dataset.sortValue || aCell.textContent.trim();
        var bVal = bCell.dataset.sortValue || bCell.textContent.trim();

        if (isNumeric) {
            // Extract first number from the string
            aVal = parseFloat(aVal.replace(/[^0-9.\-]/g, "")) || 0;
            bVal = parseFloat(bVal.replace(/[^0-9.\-]/g, "")) || 0;
        } else {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }

        var cmp;
        if (aVal < bVal) cmp = -1;
        else if (aVal > bVal) cmp = 1;
        else cmp = 0;

        return direction === "desc" ? -cmp : cmp;
    });

    // Re-append rows in sorted order
    rows.forEach(function (row) {
        tbody.appendChild(row);
    });
}
