document.addEventListener("DOMContentLoaded", function () {

    function updateEntry(orderId, entryId, receivedQty, notes) {
        return fetch("/checklist/" + orderId + "/item/" + entryId, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                received_qty: receivedQty,
                notes: notes || "",
            }),
        })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            // Update the status badge
            var badge = document.getElementById("status-" + entryId);
            if (badge) {
                badge.textContent = data.status;
                badge.className = "badge badge-check-" + data.status;
            }
            // Update row color
            var row = document.getElementById("row-" + entryId);
            if (row) {
                row.className = "checklist-row checklist-" + data.status;
            }
            return data;
        });
    }

    // OK buttons - set received = expected
    document.querySelectorAll(".btn-ok").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var entryId = btn.dataset.entryId;
            var orderId = btn.dataset.orderId;
            var expected = parseInt(btn.dataset.expected);
            var notesInput = document.getElementById("notes-" + entryId);
            var qtyInput = document.getElementById("qty-" + entryId);

            if (qtyInput) qtyInput.value = expected;

            updateEntry(orderId, entryId, expected, notesInput ? notesInput.value : "");
        });
    });

    // Save buttons - save current qty and notes
    document.querySelectorAll(".btn-save").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var entryId = btn.dataset.entryId;
            var orderId = btn.dataset.orderId;
            var qtyInput = document.getElementById("qty-" + entryId);
            var notesInput = document.getElementById("notes-" + entryId);

            var qty = qtyInput ? parseInt(qtyInput.value) : 0;
            var notes = notesInput ? notesInput.value : "";

            updateEntry(orderId, entryId, qty, notes);
        });
    });

    // Enter key on qty input triggers save
    document.querySelectorAll(".qty-input").forEach(function (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                var entryId = input.dataset.entryId;
                var saveBtn = document.querySelector('.btn-save[data-entry-id="' + entryId + '"]');
                if (saveBtn) saveBtn.click();
            }
        });
    });
});
