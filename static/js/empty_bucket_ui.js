function recalcTotal() {
    const total = document.querySelectorAll('.allocation-move-amount-input');
    let sum = 0;

    total.forEach(function (input) {
        if (input.disabled) return; // skip unchecked rows
        const value = parseFloat(input.value);
        if (!isNaN(value)) sum += value;
    });

    const totalEl = document.getElementById('allocation-total');
    if (totalEl) totalEl.textContent = '$' + sum.toFixed(2);

    const balance = parseFloat(totalEl.dataset.bucketBalance);
    if (!isNaN(balance)) {
        const over = sum > balance;
        totalEl.classList.toggle('text-error', over);
        totalEl.classList.toggle('text-success', sum == balance);
    }
}

document.addEventListener('change', function(event) {
    const checkbox = event.target.closest('.allocation-checkbox');

    if (!checkbox) return;

    const row = checkbox.closest('tr');
    if (!row) return;

    const amountInput = row.querySelector('.allocation-move-amount-input');
    if (!amountInput) return;

    amountInput.disabled = !checkbox.checked;

    if (checkbox.checked) {
        amountInput.focus();
        amountInput.select();
    }

    recalcTotal();
});

document.addEventListener('input', function (event) {
    if (!event.target.classList.contains('allocation-move-amount-input')) return;
    recalcTotal();
});

document.addEventListener('DOMContentLoaded', recalcTotal);
