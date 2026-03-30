document.addEventListener("DOMContentLoaded", function () {
    const selectAll = document.getElementById("select-all");
    const checkboxes = document.querySelectorAll('input[name="order_ids"]');
    const countSpan = document.getElementById("selected-count");
    const selectAllBtn = document.getElementById("select-all-btn");

    function updateCount() {
        const checked = document.querySelectorAll('input[name="order_ids"]:checked').length;
        if (countSpan) {
            countSpan.textContent = checked > 0 ? checked + " selected" : "";
        }
    }

    if (selectAll) {
        selectAll.addEventListener("change", function () {
            checkboxes.forEach(function (cb) {
                cb.checked = selectAll.checked;
            });
            updateCount();
        });
    }

    if (selectAllBtn) {
        selectAllBtn.addEventListener("click", function () {
            const allChecked = Array.from(checkboxes).every(function (cb) { return cb.checked; });
            checkboxes.forEach(function (cb) {
                cb.checked = !allChecked;
            });
            if (selectAll) selectAll.checked = !allChecked;
            updateCount();
        });
    }

    checkboxes.forEach(function (cb) {
        cb.addEventListener("change", updateCount);
    });
});
